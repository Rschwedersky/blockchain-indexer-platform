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

## Fluxo Completo do Pipeline (Ingestão → Decodificação → Armazenamento)

| Etapa | Serviço/Componente          | Responsabilidade                                                                 | Entrada                          | Saída / Próximo Tópico           | Usa LLM? | Status Atual |
|-------|-----------------------------|----------------------------------------------------------------------------------|----------------------------------|----------------------------------|----------|--------------|
| 1     | Ingestor                    | Conecta ao RPC Ethereum, escuta blocos novos, coleta logs crus                  | Ethereum RPC (Infura/Alchemy)    | Kafka: `raw-logs`                | Não      | ✅ Funcional  |
| 2     | Kafka (raw-logs)            | Fila de eventos crus (logs sem decodificação)                                   | Ingestor                         | Normalizer / Decoder             | Não      | ✅ KRaft      |
| 3     | Normalizer                  | Padroniza campos (chain_id, timestamp, endereço lower, topics como strings)     | Kafka: `raw-logs`                | Kafka: `normalized-events`       | Não      | Em progresso |
| 4     | Decoder                     | Recebe logs normalizados e inicia cascata de ABI                                | Kafka: `normalized-events`       | Kafka: `token-transfers-enriched` | Não (ainda) | ✅ Funcional  |
| 5     | ABIManager (cascata nível 1)| Primeiro nível: verifica cache no Redis                                         | Endereço do contrato             | ABI do cache ou próximo nível    | Não      | ✅ Integrado  |
| 6     | ABIManager (nível 2)        | Segundo nível: consulta Etherscan API (contratos verificados)                   | Endereço + Etherscan API Key     | ABI completo ou próximo nível    | Não      | ✅ Funcional  |
| 7     | ABIManager (nível 3)        | Terceiro nível: consulta 4byte.directory (só seletores/event signatures)        | Endereço                         | ABI parcial (eventos conhecidos) | Não      | Pendente     |
| 8     | ABIManager (nível 4 – LLM)  | Último recurso: usa LLM para tentar inferir ABI a partir do bytecode            | Bytecode do contrato (via RPC)   | ABI estimado ou "não decodificável" | **Sim**  | Pendente     |
| 9     | Decoder (fallback)          | Se nenhum ABI foi encontrado, aplica fallback hardcoded para Transfer ERC20/721 | Log cru                          | Evento Transfer básico           | Não      | ✅ Funcional  |
| 10    | Kafka (enriched)            | Fila de eventos já decodados/enriquecidos                                      | Decoder                          | Sink                             | Não      | ✅           |
| 11    | Sink                        | Consome eventos enriquecidos e insere no PostgreSQL (bulk insert)               | Kafka: `token-transfers-enriched`| PostgreSQL (tabelas)             | Não      | Pendente     |
| 12    | PostgreSQL                  | Armazena dados persistentes para consultas analíticas e API                     | Sink                             | API / Dashboard / Analytics      | Não      | ✅ Pronto    |

**Onde o LLM entra?**
Somente no **nível 4 da cascata** (ABIManager) — quando todos os níveis anteriores falharam (sem cache, sem verificação no Etherscan, sem assinatura no 4byte).
Nesse ponto o LLM recebe o bytecode do contrato e tenta inferir funções/eventos (via prompt estruturado: "Extraia ABI do bytecode em formato JSON").

Exemplo de prompt futuro para o LLM:

## Instalação Rápida

1. Clone o repositório

   ```bash
   git clone https://github.com/Rschwedersky/blockchain-indexer-platform.git
   cd blockchain-indexer-platform

2. Crie o arquivo .env na raiz .env
    ```bash
    ETHEREUM_RPC=https://mainnet.infura.io/v3/SUA_CHAVE_INFURA
    ETHERSCAN_API_KEY=SUA_CHAVE_ETHERSCAN

3. Suba os serviços base
    ```bash
    docker compose up -d kafka redis postgres

4. Inicie os serviços ativos
    ```bash
    docker compose up -d --build ingestor
    docker compose up -d --build decoder

## Monitoramento

- Ver status dos containers
    ```bash
    docker compose ps

- Ver logs do decoder
    ```bash
    docker compose logs -f decoder

- Consumir mensagens decodadas
    ```bash
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
