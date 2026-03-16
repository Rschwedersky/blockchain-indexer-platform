import os
import json
from dotenv import load_dotenv
from kafka import KafkaConsumer
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

load_dotenv()

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
POSTGRES_URL = (
    "postgresql://indexer_user:secure_password@postgres:5432/blockchain_indexer"
)

engine = create_engine(POSTGRES_URL)

consumer = KafkaConsumer(
    "token-transfers",
    bootstrap_servers=KAFKA_BOOTSTRAP,
    auto_offset_reset="earliest",
    group_id="sink-group",
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
)

with engine.connect() as conn:
    for msg in consumer:
        transfer = msg.value

        try:
            conn.execute(
                text(
                    """
                INSERT INTO token_transfers (
                    chain_id, block_number, block_timestamp, transaction_hash, log_index,
                    token_address, from_address, to_address, value, token_id, token_type, event_name
                ) VALUES (
                    :chain_id, :block_number, :block_timestamp, :transaction_hash, :log_index,
                    :token_address, :from_address, :to_address, :value, :token_id, :token_type, :event_name
                )
                ON CONFLICT (transaction_hash, log_index) DO NOTHING
            """
                ),
                {
                    "chain_id": transfer.get("chain_id", 1),
                    "block_number": transfer["block_number"],
                    "block_timestamp": transfer.get("block_timestamp"),
                    "transaction_hash": transfer["transaction_hash"],
                    "log_index": transfer["log_index"],
                    "token_address": transfer["token_address"],
                    "from_address": transfer["from_address"],
                    "to_address": transfer["to_address"],
                    "value": transfer.get("value"),
                    "token_id": transfer.get("token_id"),
                    "token_type": transfer["token_type"],
                    "event_name": transfer.get("event_name"),
                },
            )
            conn.commit()
            print(
                f"Inserted transfer: {transfer['transaction_hash'][:10]}... {transfer['token_type']}"
            )
        except IntegrityError:
            conn.rollback()  # duplicate, skip
        except Exception as e:
            print(f"DB error: {e}")
            conn.rollback()
