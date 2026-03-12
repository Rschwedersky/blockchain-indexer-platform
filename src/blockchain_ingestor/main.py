import os
from dotenv import load_dotenv

from .ethereum_client import EthereumClient
from .block_listener import BlockListener
from .event_builder import EventBuilder


def run():
    load_dotenv()

    rpc = os.getenv("ETHEREUM_RPC")

    client = EthereumClient(rpc)
    listener = BlockListener(client)
    builder = EventBuilder()

    block = listener.fetch_block()

    events = builder.build_events_from_block(block)

    for event in events[:5]:
        print(event)


if __name__ == "__main__":
    run()
