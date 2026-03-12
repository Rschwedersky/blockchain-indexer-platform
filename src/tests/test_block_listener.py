from blockchain_ingestor.block_listener import BlockListener
from blockchain_ingestor.ethereum_client import EthereumClient
import os


def test_fetch_block():
    rpc = os.getenv("ETHEREUM_RPC")
    client = EthereumClient(rpc)

    listener = BlockListener(client)

    block = listener.fetch_block()

    assert block is not None
    assert "transactions" in block
