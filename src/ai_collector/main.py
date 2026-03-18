import asyncio
import os
import logging
import redis.asyncio as redis
from web3 import Web3
from src.shared.abimanager import ABIManager

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai-collector")

# 1. CONFIGURAÇÕES (Variáveis de Ambiente)
RPC_URL = os.getenv("ETHEREUM_RPC")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
DATA_DIR = "data/training_set"

# 2. BANCO DE DADOS DE ASSINATURAS (Para Labeling Automático)
SIGNATURES_DB = {
    "a9059cbb": "ERC20_Transfer",
    "23b872dd": "ERC20_TransferFrom",
    "095ea7b3": "ERC20_Approve",
    "70a08231": "ERC20_BalanceOf",
    "ba138e67": "MEV_Flashloan_Call",
    "f04f275a": "MEV_Execute",
    "18cbafe5": "DEX_Swap_V2",
    "38ed1739": "DEX_Swap_Fee_Support",
    "4a25d94a": "DEX_Swap_V3",
    "f305d719": "DEX_Add_Liquidity",
    "ac9650d8": "Multicall",
    "5ae1801c": "Conduit_Execute",
}

# Inicializa Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))


def get_labels(bytecode: str) -> list:
    """Analisa o bytecode bruto em busca de padrões de funções conhecidas."""
    found = []
    clean_bytecode = bytecode.lower()
    if clean_bytecode.startswith("0x"):
        clean_bytecode = clean_bytecode[2:]

    for sig, name in SIGNATURES_DB.items():
        if sig in clean_bytecode:
            found.append(name)

    return found if found else ["UNKNOWN_LOGIC"]


async def collect_data():
    # Inicializa conexão com Redis e ABIManager
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    abi_manager = ABIManager()
    await abi_manager.initialize()

    # Garante que a pasta de dados existe
    os.makedirs(DATA_DIR, exist_ok=True)

    if not RPC_URL:
        logger.error("❌ Variável ETHEREUM_RPC não encontrada no .env!")
        return

    logger.info("🚀 AI-Collector iniciado. Capturando Bytecodes e Fontes...")

    while True:
        # Pega um contrato da fila de unidentified (backlog do decoder)
        contract_data = await r.spop("ai:training:unidentified_contracts")

        if not contract_data:
            await asyncio.sleep(10)
            continue

        try:
            chain_id, address = contract_data.split(":")
            address_checksum = w3.to_checksum_address(address)

            # 1. BUSCA O BYTECODE (Obrigatório)
            bytecode = w3.eth.get_code(address_checksum).hex()

            if bytecode == "0x" or not bytecode:
                continue

            # 2. TENTA BUSCAR O CÓDIGO FONTE (Se disponível no Etherscan/Sourcify)
            # Nota: O ABIManager deve ter o método get_source_code implementado
            source_code = None
            try:
                # Tentamos pegar o código fonte oficial
                source_code = await abi_manager.get_source_code(address)
            except Exception as e:
                logger.debug(f"Fonte não disponível para {address}: {e}")

            # 3. LABELING
            labels = get_labels(bytecode)
            label_string = ",".join(labels)

            # 4. SALVAMENTO DOS ARQUIVOS
            base_path = f"{DATA_DIR}/{chain_id}_{address}"

            # Salva o binário com metadados
            with open(f"{base_path}.bin", "w") as f:
                f.write(f"ADDRESS:{address}\n")
                f.write(f"LABELS:{label_string}\n")
                f.write(f"SOURCE_AVAILABLE:{'YES' if source_code else 'NO'}\n")
                f.write(f"BYTECODE:{bytecode}\n")

            # Se houver fonte, salva em arquivo separado .sol
            if source_code:
                with open(f"{base_path}.sol", "w", encoding="utf-8") as f:
                    f.write(source_code)
                logger.info(f"✅ CAPTURA COMPLETA (Bin+Sol): {address[:10]}")
            else:
                logger.info(
                    f"✅ CAPTURA BINÁRIA: {address[:10]}... | Labels: [{label_string}]"
                )

        except Exception as e:
            await r.sadd("ai:training:unidentified_contracts", contract_data)
            logger.error(f"❌ Erro ao processar {contract_data}: {e}")
            await asyncio.sleep(5)

    await abi_manager.close()


if __name__ == "__main__":
    try:
        asyncio.run(collect_data())
    except KeyboardInterrupt:
        logger.info("Encerrando AI-Collector...")
