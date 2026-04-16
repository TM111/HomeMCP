#!/bin/sh
# Ollama entrypoint: starts the server, pulls the model if needed, then waits.

# Start ollama server in background
ollama serve &
OLLAMA_PID=$!

# Wait for server to be ready
echo "[ollama-entrypoint] Waiting for Ollama server..."
for i in $(seq 1 30); do
    if ollama list >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Pull model if not already present
if [ -n "$OLLAMA_MODEL" ]; then
    if ollama list | grep -q "$(echo "$OLLAMA_MODEL" | cut -d: -f1)"; then
        echo "[ollama-entrypoint] Model $OLLAMA_MODEL already available."
    else
        echo "[ollama-entrypoint] Pulling $OLLAMA_MODEL ..."
        ollama pull "$OLLAMA_MODEL" || echo "[ollama-entrypoint] WARNING: Failed to pull $OLLAMA_MODEL. For cloud models, run: docker exec -it ollama ollama signin"
    fi
fi

# Wait for server process
wait $OLLAMA_PID
