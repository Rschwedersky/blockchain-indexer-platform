import json
import logging
import asyncio
import time
import aiohttp
import redis.asyncio as redis
from typing import Optional, List
import os

logger = logging.getLogger(__name__)


class ABIManager:
    # Camada 4: ABIs de Padrão para Eventos de Transferência
    ERC20_TRANSFER_EVENT = {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }

    ERC721_TRANSFER_EVENT = {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": True, "name": "tokenId", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }

    TRANSFER_TOPIC0 = (
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    )

    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True
        )
        self.etherscan_key = os.getenv("ETHERSCAN_API_KEY")
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(3)  # Limite para Etherscan Free
        self.last_request_time = 0
        # Endpoint V2 Unificado
        self.base_url = "https://api.etherscan.io/v2/api"

    async def initialize(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )

    async def get_abi(
        self, contract_address: str, chain_id: int = 1, topics: List = None
    ) -> Optional[List]:
        addr = contract_address.lower()
        cache_key = f"abi:{chain_id}:{addr}"

        # --- CAMADA 1: Cache de Performance (Redis) ---
        cached = await self.redis.get(cache_key)
        if cached:
            if cached == "NOT_FOUND":
                return self._apply_heuristics(topics)
            return json.loads(cached)

        # --- CAMADA 2: Etherscan V2 (Fonte Oficial) ---
        abi = await self._fetch_etherscan_abi(addr, chain_id)
        if abi:
            await self._save_to_cache(cache_key, abi)
            return abi

        # --- CAMADA 3: OpenChain (Assinaturas da Comunidade) ---
        abi = await self._fetch_from_openchain(addr)
        if abi:
            await self._save_to_cache(cache_key, abi)
            return abi

        # --- CAMADA 4: Heurística (Padrões ERC) ---
        heuristic_abi = self._apply_heuristics(topics)
        if heuristic_abi:
            return heuristic_abi

        # --- FALHA TOTAL: Registrar para Treinamento de IA ---
        await self.redis.setex(cache_key, 3600, "NOT_FOUND")
        await self._log_for_ai_training(addr, chain_id)
        return None

    # --- NOVA FUNÇÃO PARA O AI-COLLECTOR ---
    async def get_source_code(self, address: str, chain_id: int = 1) -> Optional[str]:
        """Busca o código fonte Solidity usando Etherscan V2"""
        if not self.etherscan_key:
            return None

        async with self.semaphore:
            params = {
                "chainid": chain_id,
                "module": "contract",
                "action": "getsourcecode",
                "address": address.lower(),
                "apikey": self.etherscan_key,
            }
            try:
                async with self.session.get(self.base_url, params=params) as resp:
                    data = await resp.json()
                    if data.get("status") == "1" and data.get("result"):
                        result = data["result"][0]
                        source = result.get("SourceCode")
                        return source if source and len(source) > 10 else None
            except Exception as e:
                logger.error(f"Erro ao buscar source V2 para {address}: {e}")
        return None

    def _apply_heuristics(self, topics: List) -> Optional[List]:
        if not topics or topics[0] != self.TRANSFER_TOPIC0:
            return None
        if len(topics) == 4:
            return [self.ERC721_TRANSFER_EVENT]
        return [self.ERC20_TRANSFER_EVENT]

    async def _fetch_etherscan_abi(self, address: str, chain_id: int) -> Optional[List]:
        if not self.etherscan_key:
            return None

        async with self.semaphore:
            now = time.time()
            wait = (1.0 / 3.0) - (now - self.last_request_time)
            if wait > 0:
                await asyncio.sleep(wait)

            # URL AJUSTADA PARA V2
            url = f"{self.base_url}?chainid={chain_id}&module=contract&action=getabi&address={address}&apikey={self.etherscan_key}"

            try:
                self.last_request_time = time.time()
                async with self.session.get(url) as resp:
                    data = await resp.json()
                    if data.get("status") == "1":
                        return json.loads(data["result"])
                    logger.debug(
                        f"Etherscan V2 Info [{address[:10]}]: {data.get('result')}"
                    )
            except Exception as e:
                logger.error(f"Erro na conexão Etherscan V2: {e}")
        return None

    async def _fetch_from_openchain(self, address: str) -> Optional[List]:
        url = f"https://api.openchain.xyz/signature-database/v1/lookup?addresses={address}&filter=true"
        try:
            async with self.session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = data.get("result", {}).get(address, {})
                    partial_abi = []
                    for item_type, items in [
                        ("function", result.get("functions", {})),
                        ("event", result.get("events", {})),
                    ]:
                        for selector, sigs in items.items():
                            if sigs:
                                name = sigs[0]["name"].split("(")[0]
                                partial_abi.append(
                                    {"type": item_type, "name": name, "inputs": []}
                                )
                    return partial_abi if partial_abi else None
        except Exception:
            pass
        return None

    async def _log_for_ai_training(self, address: str, chain_id: int):
        await self.redis.sadd(
            "ai:training:unidentified_contracts", f"{chain_id}:{address}"
        )
        logger.warning(f"Contrato {address} movido para backlog de treinamento de IA.")

    async def _save_to_cache(self, key: str, abi: List):
        await self.redis.setex(key, 60 * 60 * 24 * 7, json.dumps(abi))

    async def close(self):
        if self.session:
            await self.session.close()
        await self.redis.close()
