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

for message in consumer:
    raw_log = message.value

    # Normalize / clean / enrich
    normalized = NormalizedLog(
        chain_id=raw_log.get("chain_id", 1),
        block_number=raw_log["block_number"],
        block_timestamp=raw_log.get("block_timestamp", 0),
        transaction_hash=raw_log["transactionHash"],
        log_index=raw_log["logIndex"],
        address=raw_log["address"].lower(),
        topics=[t if isinstance(t, str) else f"0x{t.hex()}" for t in raw_log["topics"]],
        data=(
            raw_log["data"]
            if isinstance(raw_log["data"], str)
            else f"0x{raw_log['data'].hex()}"
        ),
        removed=raw_log.get("removed", False),
    ).model_dump()

    producer.send("normalized-events", normalized)
    print(
        f"Normalized & sent: {normalized['transaction_hash'][:10]}... log {normalized['log_index']}"
    )
