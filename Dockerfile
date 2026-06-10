FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.lock .
RUN pip install --no-cache-dir --prefix=/install -r requirements.lock

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY bot/ ./bot/
COPY api/ ./api/
COPY knowledge_base/ ./knowledge_base/
CMD ["python", "-m", "bot.main"]
