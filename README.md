# Blockchain Indexer Platform

Sistema distribuído e escalável para indexação, normalização e decodificação de eventos de blockchain.
Focado em rastreamento de movimentos de tokens (ERC-20 / ERC-721) com arquitetura moderna e pipeline em tempo real.

## Badges

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka-Apache-brightgreen?style=flat-square&logo=apachekafka&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/github/license/Rschwedersky/blockchain-indexer-platform?style=flat-square)

## Sobre o Projeto

Este é um indexador de blockchain completo e modular que:

- Coleta blocos e logs em tempo real da Ethereum (ou outras EVM-compatíveis)
- Produz eventos crus no Kafka
- Normaliza e enriquece logs
- Decodifica eventos padrão (Transfer ERC-20/ERC-721) + ABIs dinâmicos via cascata
- Prepara dados para análise no PostgreSQL

## Arquitetura Atual
Ethereum RPC → Ingestor → raw-logs (Kafka) → Normalizer → normalized-events (Kafka)
→ Decoder + ABIManager (Redis cache) → token-transfers-enriched (Kafka) → Sink → PostgreSQL


## Status dos Serviços

| Serviço      | Responsabilidade                              | Status     |
|--------------|-----------------------------------------------|------------|
| ingestor     | Coleta blocos/logs em tempo real              | Funcional  |
| decoder      | Decodificação + cascata de ABIs               | Funcional  |
| redis        | Cache de ABIs                                 | Integrado  |
| kafka        | Fila de eventos (KRaft mode)                  | Funcional  |
| postgres     | Armazenamento persistente                     | Pronto     |
| normalizer   | Normalização de logs                          | Em progresso |
| sink         | Inserção no PostgreSQL                        | Pendente   |

## Instalação Rápida

1. Clone o repositório

   ```bash
   git clone https://github.com/Rschwedersky/blockchain-indexer-platform.git
   cd blockchain-indexer-platform

2. Crie o arquivo .env na raizenv
    ETHEREUM_RPC=https://mainnet.infura.io/v3/SUA_CHAVE_INFURA
    ETHERSCAN_API_KEY=SUA_CHAVE_ETHERSCAN

3. Suba os serviços base
    docker compose up -d kafka redis postgres

4. Inicie os serviços ativos
    docker compose up -d --build ingestor
    docker compose up -d --build decoder

## Monitoramento

- Ver status dos containers
    docker compose ps

- Ver logs do decoder
    docker compose logs -f decoder

- Consumir mensagens decodadas
    docker exec -it kafka kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic token-transfers-enriched --from-beginning --max-messages 5

## Roadmap

Normalizer completo
Sink funcional (PostgreSQL)
Suporte a 4byte.directory no ABIManager
Django API + autenticação
Sistema de pagamentos (Stripe / PagSeguro)
Suporte multi-chain
Dashboard básico

## Licença
MIT License
Feito por Rodrigo Schwedersky • Santa Catarina, Brasil • 2026
