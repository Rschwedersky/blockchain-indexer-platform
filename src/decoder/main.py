# ... imports ...
from web3 import Web3
from web3.exceptions import ABIEventNotFound
import os
import json
from kafka import KafkaConsumer, KafkaProducer
from dotenv import load_dotenv

load_dotenv()

w3 = Web3()  # for decoding only

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

ERC20_ABI = [...]  # paste the ERC20_TRANSFER_ABI dict from earlier
ERC721_ABI = [...]  # paste ERC721_TRANSFER_ABI

consumer = KafkaConsumer(
    "normalized-events",
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    auto_offset_reset="earliest",
    group_id="decoder-group",
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
)

producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

for msg in consumer:
    event = msg.value

    if not event.get("topics") or event["topics"][0] != TRANSFER_TOPIC:
        continue

    try:
        decoded = w3.eth.abi.decode_log(ERC20_ABI, event["data"], event["topics"])
        token_type = "ERC20"
        value = str(decoded["value"])
        token_id = None
    except ABIEventNotFound:
        if len(event["topics"]) == 4:
            decoded = w3.eth.abi.decode_log(ERC721_ABI, event["data"], event["topics"])
            token_type = "ERC721"
            value = None
            token_id = str(decoded["tokenId"])
        else:
            continue

    enriched = {
        **event,
        "event_name": "Transfer",
        "token_type": token_type,
        "from_address": decoded["from"].lower(),
        "to_address": decoded["to"].lower(),
        "value": value,
        "token_id": token_id,
        "token_address": event["address"].lower(),
    }

    producer.send("token-transfers", enriched)
    print(f"Decoded {token_type} Transfer in {enriched['transaction_hash'][:10]}...")
