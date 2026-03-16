import os
from ingestor.ethereum_client import EthereumClient


def test_connection():
    rpc = os.getenv("ETHEREUM_RPC")

    client = EthereumClient(rpc)

    block = client.get_latest_block_number()

    assert block > 0


def test_get_block():
    rpc = os.getenv("ETHEREUM_RPC")
    client = EthereumClient(rpc)

    latest = client.get_latest_block_number()

    block = client.get_block(latest)

    assert block["number"] == latest
    assert "transactions" in block


def test_transaction_receipt():
    rpc = os.getenv("ETHEREUM_RPC")
    client = EthereumClient(rpc)

    latest = client.get_latest_block_number()
    block = client.get_block(latest)

    tx = block["transactions"][0]

    receipt = client.get_transaction_receipt(tx["hash"])

    assert receipt is not None
    assert "status" in receipt
