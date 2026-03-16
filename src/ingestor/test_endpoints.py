from ingestor.ethereum_client import EthereumClient
import os
from dotenv import load_dotenv

load_dotenv()

RPC = os.getenv("ETHEREUM_RPC")

client = EthereumClient(RPC)


def run_tests():
    print("\n--- BLOCK ---")
    latest = client.get_latest_block_number()
    print("Latest block:", latest)

    block = client.get_block(latest)
    print("Block timestamp:", block["timestamp"])
    print("Transactions:", len(block["transactions"]))

    print("\n--- TRANSACTION ---")
    tx = block["transactions"][0]

    print("TX hash:", tx["hash"].hex())
    print("From:", tx["from"])
    print("To:", tx["to"])

    receipt = client.get_transaction_receipt(tx["hash"])
    print("Status:", receipt["status"])
    print("Gas used:", receipt["gasUsed"])

    print("\n--- ACCOUNT ---")
    balance = client.get_balance(tx["from"])
    print("Balance:", balance)

    print("\n--- NETWORK ---")
    gas = client.get_gas_price()
    print("Gas price:", gas)

    print("\n--- LOGS ---")
    logs = client.get_logs(latest, latest)
    print("Logs count:", len(logs))

    print("\n--- BLOCK FIELDS ---")
    print(block.keys())

    print("\n--- TX FIELDS ---")
    print(tx.keys())

    print("\n--- RECEIPT FIELDS ---")
    print(receipt.keys())

    for log in logs[:3]:
        print(log)


if __name__ == "__main__":
    run_tests()
