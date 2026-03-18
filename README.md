Serviço,Entrada,Saída,Papel Principal
Ingestor,Blockchain RPC,raw-logs (Kafka),Captura bruta.
EventNormalizer,raw-logs,normalized-events,Limpeza de tipos e tipos JSON.
Decoder,normalized-events,token-transfers,Tradução via ABI/Heurística.
AI-Collector,Redis Backlog,.sol e .bin (Disco),Mineração de exemplos reais.
DataNormalizer,.sol / .bin,dataset.jsonl,Preparação para Treinamento IA.
