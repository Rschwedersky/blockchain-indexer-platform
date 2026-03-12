ERC20_TRANSFER_TOPIC = "0xddf252ad"


def get_transfer_logs(client, from_block, to_block):
    logs = client.get_logs(from_block, to_block, topics=[ERC20_TRANSFER_TOPIC])

    return logs
