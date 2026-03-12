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


def get_total_supply(client, token_address):
    contract = client.w3.eth.contract(
        address=Web3.to_checksum_address(token_address), abi=ERC20_ABI
    )

    return contract.functions.totalSupply().call()
