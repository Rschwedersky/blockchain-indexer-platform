import os
from dotenv import load_dotenv

from .ethereum_client import EthereumClient
from .block_listener import BlockListener
from .logs_listener import LogsListener
from .event_builder import EventBuilder


def get_field(obj, key):
    if isinstance(obj, dict):
        return obj[key]
    return getattr(obj, key)


def run():
    load_dotenv()

    rpc_url = os.getenv("ETHEREUM_RPC")

    client = EthereumClient(rpc_url)

    block_listener = BlockListener(client)
    logs_listener = LogsListener(client)

    builder = EventBuilder()

    for block in block_listener.listen():
        block_event = builder.build_block_event(block)
        print(block_event)

        for tx in block.transactions[:5]:
            tx_event = builder.build_transaction_event(tx, block["number"])
            print(tx_event)

        logs = logs_listener.get_block_logs(block["number"])
        print(f"logs found: {len(logs)}")


if __name__ == "__main__":
    run()
