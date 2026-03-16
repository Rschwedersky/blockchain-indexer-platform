from web3 import Web3


class EthereumClient:
    def __init__(self, rpc_url: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

    # -------- BLOCKS --------

    def get_latest_block_number(self):
        return self.w3.eth.block_number

    def get_block(self, block_number: int):
        return self.w3.eth.get_block(block_number, full_transactions=True)

    # -------- TRANSACTIONS --------

    def get_transaction(self, tx_hash):
        return self.w3.eth.get_transaction(tx_hash)

    def get_transaction_receipt(self, tx_hash):
        return self.w3.eth.get_transaction_receipt(tx_hash)

    # -------- ACCOUNT --------

    def get_balance(self, address):
        return self.w3.eth.get_balance(address)

    # -------- NETWORK --------

    def get_gas_price(self):
        return self.w3.eth.gas_price

    def get_fee_history(self, block_count=10):
        latest = self.w3.eth.block_number
        return self.w3.eth.fee_history(block_count, latest, [10, 50, 90])

    # -------- LOGS --------

    def get_logs(self, from_block, to_block, topics=None):
        return self.w3.eth.get_logs(
            {"fromBlock": from_block, "toBlock": to_block, "topics": topics}
        )
