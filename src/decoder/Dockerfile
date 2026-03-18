# syntax=docker/dockerfile:1   # optional but good

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Copy root-level dependency files (adjust path to go up)
COPY ../../pyproject.toml ../../uv.lock* ./

# Install locked deps without project code
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Runtime stage
FROM python:3.12-slim-bookworm

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy the ingestor code (this folder)
COPY . .

# For monorepo: set PYTHONPATH if needed to find shared code
ENV PYTHONPATH="/app:${PYTHONPATH}"

CMD python -m src.decoder.main
