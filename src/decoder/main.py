import json
import asyncio
import os
import logging
import redis.asyncio as redis
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from web3 import Web3
from eth_utils import event_abi_to_log_topic
from web3._utils.events import get_event_data
from src.shared.abimanager import ABIManager

# Configurações
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
INPUT_TOPIC = "normalized-events"
OUTPUT_TOPIC = "token-transfers-enriched"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("decoder")
w3 = Web3()

# HASH PADRÃO ERC20 Transfer(address,address,uint256)
ERC20_TRANSFER_TOPIC = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)


def normalize_hex(val):
    """Garante que strings hexadecimais comecem com 0x e sejam lowercase"""
    if not val:
        return "0x"
    s = str(val).lower()
    return s if s.startswith("0x") else "0x" + s


async def decode_log(log: dict, abimanager: ABIManager, r_client):
    contract = normalize_hex(log.get("address", ""))
    # Normaliza todos os tópicos para evitar erro de comparação sem '0x'
    topics = [normalize_hex(t) for t in log.get("topics", [])]
    data = normalize_hex(log.get("data", "0x"))
    chain_id = log.get("chain_id", 1)

    if not topics:
        return {**log, "decoded_success": False}

    topic0 = topics[0]

    # --- CAMADA 1, 2, 3: BUSCA ABI OFICIAL ---
    abi = await abimanager.get_abi(contract, topics=topics)

    if abi:
        try:
            event_abi = None
            for item in abi:
                if item.get("type") == "event":
                    try:
                        if normalize_hex(event_abi_to_log_topic(item).hex()) == topic0:
                            event_abi = item
                            break
                    except (ValueError, TypeError, AttributeError):
                        continue

            if event_abi:
                mock_log = {
                    "address": contract,
                    "topics": topics,
                    "data": data,
                    "blockNumber": log.get("blockNumber", 0),
                    "transactionHash": log.get("transactionHash", "0x"),
                    "logIndex": log.get("logIndex", 0),
                    "transactionIndex": log.get("transactionIndex", 0),
                }
                decoded = get_event_data(w3.codec, event_abi, mock_log)
                return {
                    **log,
                    "event_name": event_abi["name"],
                    "decoded_params": dict(decoded.args),
                    "decoded_success": True,
                }
        except Exception as e:
            logger.debug(f"Falha na decodificação técnica com ABI: {e}")

    # --- CAMADA 4: HEURÍSTICA (DECIFRAGEM "CEGA") ---
    # Se chegamos aqui, a ABI falhou. Vamos tentar decodificar o básico (Transfer)
    if topic0 == ERC20_TRANSFER_TOPIC and len(topics) >= 3:
        try:
            # Extrai endereços dos tópicos indexados
            from_addr = "0x" + topics[1][-40:]
            to_addr = "0x" + topics[2][-40:]
            # Valor está no data
            value = int(data, 16) if data != "0x" else 0

            return {
                **log,
                "event_name": "Transfer (Heuristic)",
                "decoded_params": {"from": from_addr, "to": to_addr, "value": value},
                "decoded_success": True,
            }
        except (ValueError, TypeError, AttributeError):
            pass

    # --- FALHA TOTAL: MANDAR PARA O REDIS (AI-COLLECTOR) ---
    await r_client.sadd("ai:training:unidentified_contracts", f"{chain_id}:{contract}")
    logger.warning(f"⚠️ Contrato {contract[:12]}... movido para backlog de IA.")

    return {**log, "decoded_success": False, "event_name": "Unknown"}


async def main():
    manager = ABIManager()
    await manager.initialize()

    # Cliente Redis para o Backlog de IA
    r_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

    consumer = AIOKafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id="decoder-group-v1",
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    )
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
    )

    await consumer.start()
    await producer.start()

    logger.info("📡 Decoder iniciado e ouvindo Kafka...")

    try:
        async for msg in consumer:
            enriched = await decode_log(msg.value, manager, r_client)
            await producer.send_and_wait(OUTPUT_TOPIC, enriched)

            if enriched["decoded_success"]:
                # Se for heurística, usamos um log diferente
                status = (
                    "✨ [HEURÍSTICA]"
                    if "Heuristic" in enriched["event_name"]
                    else "✔ [ABI]"
                )
                logger.info(
                    f"{status} {enriched['event_name']} em {enriched['address'][:10]}"
                )
    finally:
        await consumer.stop()
        await producer.stop()
        await manager.close()
        await r_client.close()


if __name__ == "__main__":
    asyncio.run(main())
