import time


class BlockListener:
    def __init__(self, client, poll_interval=2):
        self.client = client
        self.poll_interval = poll_interval
        self.last_block = None

    def get_latest_block_number(self):
        return self.client.get_latest_block_number()

    def fetch_block(self):
        block_number = self.get_latest_block_number()
        block = self.client.get_block(block_number)

        print(f"Block number: {block['number']}")
        print(f"Transactions: {len(block['transactions'])}")

        return block

    def listen_blocks(self):
        if self.last_block is None:
            self.last_block = self.get_latest_block_number()

        while True:
            current_block = self.get_latest_block_number()

            if current_block > self.last_block:
                for block_number in range(self.last_block + 1, current_block + 1):
                    block = self.client.get_block(block_number)

                    yield block

                self.last_block = current_block

            time.sleep(self.poll_interval)
