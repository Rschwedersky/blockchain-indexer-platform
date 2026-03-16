import os
import json
from dotenv import load_dotenv
from kafka import KafkaProducer
from kafka.errors import KafkaError
from hexbytes import HexBytes  # You might need to install this if not present

from .ethereum_client import EthereumClient
from .block_listener import BlockListener
from .logs_listener import LogsListener
from .event_builder import EventBuilder


# 1. ADD THIS HELPER TO HANDLE WEB3 TYPES
def handle_hex_bytes(obj):
    if isinstance(obj, HexBytes):
        return obj.hex()
    if isinstance(obj, bytes):
        return obj.hex()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def run():
    load_dotenv()

    rpc_url = os.getenv("ETHEREUM_RPC")
    kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    # 2. UPDATE THE SERIALIZER
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap,
        value_serializer=lambda v: json.dumps(v, default=handle_hex_bytes).encode(
            "utf-8"
        ),
        retries=5,
        acks=1,
    )

    client = EthereumClient(rpc_url)
    block_listener = BlockListener(client)
    logs_listener = LogsListener(client)
    builder = EventBuilder()

    print("🚀 Ingestor started. Waiting for blocks...")

    for block in block_listener.listen():
        block_event = builder.build_block_event(block)
        print(f"📦 Processing Block: {block_event}")

        # Optional: send block/tx events to other topics if needed
        # ...

        logs = logs_listener.get_block_logs(block["number"])
        print(f"🔍 Logs found: {len(logs)}")

        # 3. PERFORMANCE: Send logs into the background buffer
        for log in logs:
            log_with_context = {
                **log,
                "chain_id": 1,
                "block_number": block["number"],
                "block_timestamp": block.get("timestamp", 0),
            }

            try:
                # Async send (very fast)
                producer.send("raw-logs", value=log_with_context)
            except KafkaError as e:
                print(f"❌ Kafka send error: {e}")

        # 4. PERFORMANCE: Flush ONCE per block, not once per log
        producer.flush(timeout=10)
        print(f"✅ Block {block['number']} synced to Kafka.")

    producer.close()


if __name__ == "__main__":
    run()
