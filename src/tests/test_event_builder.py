from blockchain_ingestor.event_builder import EventBuilder


def test_build_transaction_event():
    builder = EventBuilder()

    tx = {
        "hash": "0x123",
        "from": "0xabc",
        "to": "0xdef",
        "value": 100,
        "gas": 21000,
    }

    event = builder.build_transaction_event(1, tx)

    assert event["tx_hash"] == "0x123"
    assert event["block_number"] == 1
