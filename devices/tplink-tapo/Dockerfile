FROM python:3.11-slim

WORKDIR /app

# net-tools for arp (MAC -> IP resolution)
RUN apt-get update && \
    apt-get install -y --no-install-recommends net-tools iputils-ping && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    plugp100>=5.1.0 \
    mcp>=1.6.0 \
    starlette>=0.37.0 \
    uvicorn>=0.29.0

CMD ["python", "server.py"]
