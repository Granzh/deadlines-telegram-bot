FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install uv && \
    uv sync --frozen --no-dev

COPY . .

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uv", "run", "python", "main.py"]
