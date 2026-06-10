FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.lock .
RUN pip install --no-cache-dir --prefix=/install -r requirements.lock

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    curl -o /usr/local/share/ca-certificates/russian_ca.crt \
    https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /install /usr/local
COPY bot/ ./bot/
COPY api/ ./api/
COPY knowledge_base/ ./knowledge_base/
CMD ["python", "-m", "bot.main"]
