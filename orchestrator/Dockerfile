FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    mcp[cli]>=1.6.0 \
    httpx-sse>=0.4.0 \
    httpx>=0.27.0 \
    ollama>=0.4.0

CMD ["python", "src/main.py"]
