ERC20_TRANSFER_TOPIC = "0xddf252ad"


class LogsListener:
    def __init__(self, client):
        self.client = client

    def get_block_logs(self, block_number):
        logs = self.client.get_logs(block_number, block_number)

        return logs
