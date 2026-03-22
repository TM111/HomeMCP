# HomeMCP - Smart Home Assistant

Modular smart home orchestrator: a local LLM (Ollama) that uses MCP modules to control devices.

## Architecture

```
┌─────────────────────────────────────────────┐
│  Orchestrator (Ollama + LLM)                │
│  - Interactive chat                         │
│  - Tool calling to MCP modules              │
└───────┬─────────────────────┬───────────────┘
        │                     │
   ┌────▼─────┐         ┌────▼─────┐
   │ Dreame   │         │ Tapo     │
   │ MCP :6278│         │ MCP :6279│
   └──────────┘         └──────────┘
```

## Quick Start

### 1. Start device modules

```bash
# Dreame (robot vacuum)
cd devices/dreame
# Configure devices/dreame/.env with TOKEN, ENTITY_ID, HA_URL
docker compose up -d

# Tapo P105 (smart plug)
cd devices/tplink-tapo
# Configure devices/tplink-tapo/.env with TAPO_MAC, TAPO_EMAIL, TAPO_PASSWORD, TAPO_IP
docker compose up -d
```

### 2. Start the orchestrator + Ollama

```bash
# From the root folder
docker compose up -d             # start Ollama
docker compose run orchestrator  # start interactive chat
```

On first run, the model will be downloaded automatically.

### 3. Chat

```
You: Clean the living room
  [tool] vacuum_list_rooms({})
  [result] {1: "Living Room", 2: "Bedroom", ...}
  [tool] vacuum_clean_rooms({"room_ids": [1]})
  [result] Cleaning started for rooms [1] (repeats=1)
Assistant: I started cleaning the living room!
```

## Adding a new module

1. **Create a folder** `devices/my-device/` with `server.py`, `Dockerfile`, `docker-compose.yml`, and `.env`
2. **Write the MCP server** — expose your tools via SSE transport using `mcp.server.Server` + `SseServerTransport` + Starlette/Uvicorn. See `devices/tplink-tapo/server.py` as a reference
3. **Pick a port** — dreame uses `6278`, tapo uses `6279`. Use the next available (e.g. `6280`)
4. **Dockerize** — use `python:3.11-slim`, install `mcp>=1.6.0`, `starlette`, `uvicorn`, and your device library. Expose your chosen port in `docker-compose.yml`
5. **Register** — add an entry to `orchestrator/config/mcp_servers.json`:
   ```json
   { "name": "my-device", "url": "http://host.docker.internal:6280/sse" }
   ```
6. **Start** — `docker compose up -d` in your module folder, then `docker compose run orchestrator` from the root

## GPU (optional)

To enable NVIDIA GPU for Ollama, uncomment the `deploy` section in the root `docker-compose.yml`.