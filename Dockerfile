FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl bzip2 libgomp1 nodejs npm net-tools iputils-ping && \
    rm -rf /var/lib/apt/lists/* && \
    curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | CONFIGURE=false bash && \
    pip install --no-cache-dir PyYAML==6.0.3

ENV PATH="/root/.local/bin:$PATH"

COPY entrypoint.py /entrypoint.py

ENTRYPOINT ["python", "/entrypoint.py"]
CMD ["session"]