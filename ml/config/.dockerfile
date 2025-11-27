FROM python:3.12-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

EXPOSE 5003 5004 5005 8001

# ===== embedding_model =====
FROM base AS embedding_model-builder
RUN apt-get update && apt-get install -y \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*
COPY config/requirements/embedding_model.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r embedding_model.txt

FROM base AS embedding_model
COPY --from=embedding_model-builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=embedding_model-builder /usr/local/bin/ /usr/local/bin/
COPY embedding_model/embedding_model.py embedding_model/config.py embedding_model/__init__.py /app/
CMD ["uvicorn", "embedding_model:app", "--host", "0.0.0.0", "--port", "5003"]

# ===== llm =====
FROM base AS llm-builder
RUN apt-get update && apt-get install -y \
    gcc g++ cmake make git pkg-config \
    && rm -rf /var/lib/apt/lists/*
COPY config/requirements/llm.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r llm.txt

FROM base AS llm
RUN apt-get update && apt-get install -y \
    libgomp1 && rm -rf /var/lib/apt/lists/*
COPY --from=llm-builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=llm-builder /usr/local/bin/ /usr/local/bin/
COPY llm/llm_local.py llm/config.py llm/__init__.py /app/
CMD ["uvicorn", "llm_local:app", "--host", "0.0.0.0", "--port", "5005"]

# ===== vector_db =====
FROM base AS vector_db-builder
RUN apt-get update && apt-get install -y \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*
COPY config/requirements/vector_db.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r vector_db.txt

FROM base AS vector_db
COPY --from=vector_db-builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=vector_db-builder /usr/local/bin/ /usr/local/bin/
COPY vector_db/chroma_db.py vector_db/__init__.py /app/
CMD ["uvicorn", "chroma_db:app", "--host", "0.0.0.0", "--port", "5004"]

# ===== main =====
FROM base AS main
COPY config/requirements/main.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r main.txt
COPY main/main.py main/__init__.py /app/
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

