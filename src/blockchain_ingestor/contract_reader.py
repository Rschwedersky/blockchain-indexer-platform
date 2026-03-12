from web3 import Web3

ERC20_ABI = [
    {
        "name": "totalSupply",
        "outputs": [{"type": "uint256"}],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    }
]


class ContractReader:
    def __init__(self, client):
        self.client = client

    def get_total_supply(self, token_address):
        contract = self.client.w3.eth.contract(
            address=Web3.to_checksum_address(token_address), abi=ERC20_ABI
        )

        return contract.functions.totalSupply().call()
