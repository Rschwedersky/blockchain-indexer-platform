from collections import deque
import json
import os
from dotenv import load_dotenv
from kafka import KafkaConsumer, KafkaProducer
from pydantic import BaseModel

load_dotenv()


class NormalizedLog(BaseModel):
    chain_id: int
    block_number: int
    block_timestamp: int = 0
    transaction_hash: str
    log_index: int
    address: str  # contract address
    topics: list[str]
    data: str  # hex
    removed: bool = False


KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

consumer = KafkaConsumer(
    "raw-logs",
    bootstrap_servers=KAFKA_BOOTSTRAP,
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="normalizer-group",
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)
processed_cache = deque(maxlen=5000)
for message in consumer:
    try:
        raw_log = message.value

        # Garante que campos críticos existam antes de validar
        if "transactionHash" not in raw_log or "address" not in raw_log:
            continue
        # Cria uma chave única para o log
        log_id = f"{raw_log['transactionHash']}_{raw_log['logIndex']}"

        if log_id in processed_cache:
            continue  # Pula se já processamos este log recentemente

        # Normalização usando o seu modelo Pydantic
        log_data = NormalizedLog(
            chain_id=raw_log.get("chain_id", 1),
            block_number=raw_log.get("block_number", 0),
            block_timestamp=raw_log.get("block_timestamp", 0),
            transaction_hash=raw_log["transactionHash"],
            log_index=raw_log["logIndex"],
            address=raw_log["address"].lower(),
            # A sua lógica de conversão de Hex para String está perfeita aqui:
            topics=[
                t if isinstance(t, str) else f"0x{t.hex()}"
                for t in raw_log.get("topics", [])
            ],
            data=(
                raw_log["data"]
                if isinstance(raw_log["data"], str)
                else f"0x{raw_log['data'].hex()}"
            ),
            removed=raw_log.get("removed", False),
        ).model_dump()

        # Envia para o tópico que o DECODER vai ler
        producer.send("normalized-events", log_data)

    except Exception as e:
        print(f"❌ Erro ao normalizar log: {e}")
