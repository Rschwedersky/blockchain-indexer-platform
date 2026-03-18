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



🚀 Fluxo da sua Infraestrutura
1. EventNormalizer (O "Limpador")O raw-logs do Ethereum é "sujo" (contém HexBytes, estruturas complexas do Web3.py e metadados redundantes). O papel deste microserviço é:JSON Puro: Converter tudo para tipos primitivos (strings hex, ints).Deduplicação: Garantir que, se o Ingestor enviar o mesmo log duas vezes (devido a um retry de rede), o Normalizer ignore a duplicata.Topic Output: normalized-events.

2. Token Transfer Decoder (O "Cérebro")Este é o serviço mais crítico. Ele não deve apenas decodificar, mas também classificar.Lógica de Tópicos: Ele olha para o topic[0].Se 0xddf25... e
3 tópicos $\rightarrow$ ERC20 Transfer.Se 0xddf25... e 4 tópicos $\rightarrow$ ERC721 (NFT) Transfer.ABI Mapping: Ele mantém um cache de ABIs padrões (ERC20, ERC721, ERC1155).Output: token-transfers (tabela limpa de quem mandou o quê) e enriched-events (o log original + campos humanos como value_decimal).

3. Sink (O "Destino")Postgres: Ótimo para queries relacionais (ex: "Qual o saldo do endereço X?").Clickhouse: Essencial se você quiser fazer "Dune-style queries" em bilhões de linhas com performance de milissegundos.
