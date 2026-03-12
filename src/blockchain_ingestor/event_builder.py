class EventBuilder:
    def build_block_event(self, block):
        return {
            "type": "block",
            "block_number": block["number"],
            "timestamp": block["timestamp"],
            "tx_count": len(block["transactions"]),
        }

    def build_transaction_event(self, block_number, tx):
        return {
            "type": "transaction",
            "block_number": block_number,
            "tx_hash": tx["hash"].hex() if hasattr(tx["hash"], "hex") else tx["hash"],
            "from": tx.get("from"),
            "to": tx.get("to"),
            "value": tx.get("value"),
            "gas": tx.get("gas"),
        }

    def build_events_from_block(self, block):
        events = []
        # block event
        events.append(self.build_block_event(block))
        # transaction events
        for tx in block["transactions"]:
            events.append(self.build_transaction_event(block["number"], tx))

        return events

    def build_log_event(self, block_number, log):
        return {
            "type": "log",
            "block_number": block_number,
            "address": log["address"],
            "topics": log["topics"],
            "data": log["data"],
            "tx_hash": log["transactionHash"].hex(),
        }
