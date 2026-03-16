src/ingestor

ethereum_client.py
      ↓
block_listener.py
      ↓
event_builder.py
      ↓
main.py


Blockchain RPCs
     ↓
[Ingestor] (seu repo atual) → produz raw logs/events
     ↓ (Kafka topic: raw-logs)
[EventNormalizer] (microservice 1)
     ↓ (Kafka topic: normalized-events)
[Kafka/Redis Producer] (já integrado no normalizer ou separado)
     ↓
[Token Transfer Decoder] (microservice 2) → decodifica ERC20/ERC721
     ↓ (Kafka topic: token-transfers + enriched-events)
[Sink] → Postgres/Clickhouse + analytics (Dune-style queries)
