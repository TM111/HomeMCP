# HomeMCP

Smart home assistant powered by a local LLM that controls devices through MCP (Model Context Protocol) servers — all from a Telegram bot.

## Architecture

```
Telegram
   │
   ▼
┌──────────────────────────────────┐
│  Goose  (AI assistant)           │
│  ├─ Telegram gateway             │
│  └─ Ollama provider (local LLM)  │
└──────┬──────────────┬────────────┘
       │              │
  ┌────▼─────┐  ┌────▼─────┐
  │ Dreame   │  │  Tapo    │
  │ MCP :6278│  │ MCP :6279│
  └──────────┘  └──────────┘
```

```mermaid
graph TD
  T[Telegram] --> G[Goose \n(AI assistant)]

  subgraph Goose
    G1[Telegram gateway]
    G2[Ollama provider \n(local LLM)]
    G --> G1
    G --> G2
  end

  G1 --> D[Dreame \nMCP :6278]
  G2 --> D

  G2 --> TAP[Tapo \nMCP :6279]
```

**Goose** is the AI runtime that handles conversation, tool calling, and the Telegram gateway.
**Ollama** runs the LLM locally with GPU acceleration, or proxies to [cloud models](https://ollama.com/blog/cloud-models) for larger models.
Each device is an independent **MCP server** that exposes tools via Streamable HTTP.

## Prerequisites

- Docker + Docker Compose
- NVIDIA GPU with drivers installed (for Ollama GPU acceleration)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- A Telegram bot token (create one via [@BotFather](https://t.me/BotFather))

> Without an NVIDIA GPU, remove the `deploy` block from `docker-compose.yml` under the `ollama` service. Ollama will fall back to CPU.

## Quick Start

### 1. Create the `.env` file

In the project root, create a `.env` file:

```env
TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
OLLAMA_MODEL=qwen2.5:7b
```

| Variable             | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| `TELEGRAM_BOT_TOKEN` | Token from BotFather for the Telegram bot                                   |
| `OLLAMA_MODEL`       | Ollama model — local (e.g. `qwen2.5:7b`) or cloud (e.g. `gpt-oss:20b-cloud`) |

### 2. Start the MCP device servers

Each device under `devices/` has its own README with setup instructions. Start them before Goose:

```bash
cd devices/dreame && docker compose up -d
cd devices/tplink-tapo && docker compose up -d
```

### 3. Start Ollama + Goose

```bash
# From the project root
docker compose up -d
```

On the first run, Ollama will automatically pull the configured model. This may take a few minutes for local models.

#### Using cloud models

Ollama supports [cloud models](https://ollama.com/blog/cloud-models) (e.g. `gpt-oss:20b-cloud`, `qwen3-coder:480b-cloud`) that run on remote hardware. To use them:

1. Set a cloud model in `.env`:
   ```env
   OLLAMA_MODEL=gpt-oss:20b-cloud
   ```
2. Start the stack: `docker compose up -d`
3. Sign in to ollama.com from inside the container:
   ```bash
   docker exec -it ollama ollama signin
   ```
   This prints a URL — open it in your browser to authenticate. The session is saved in the `ollama_data` volume and persists across restarts.
4. Restart to auto-pull the model: `docker compose restart ollama goose`

> You only need to sign in once. The auth token is persisted in the `ollama_data` Docker volume.

### 4. Pair your Telegram account

Generate a pairing code:

```bash
docker exec goose goose gateway pair telegram
```

Send the code as a message to your bot on Telegram. Once paired, the bot will respond to your messages.

> Pairings are cleared on every restart. After each `docker compose up -d` you need to re-pair.

### 5. Chat

Send a message to your bot on Telegram:

```
You: Turn off the smart plug
Bot: Done! The Tapo P105 plug is now off.

You: Clean the living room
Bot: Starting vacuum cleaning in the living room.
  [result] {1: "Living Room", 2: "Bedroom", ...}
  [tool] vacuum_clean_rooms({"room_ids": [1]})
  [result] Cleaning started for rooms [1] (repeats=1)
Assistant: I started cleaning the living room!
```

## Configuration — `goose.yaml`

All Goose settings are in a single file: [`goose.yaml`](goose.yaml). Edit it and restart to apply:

```bash
docker compose restart goose
```

### Platform Extensions

Built-in Goose capabilities. All disabled by default — enable only what you need:

```yaml
platform_extensions:
  developer: false         # File editing and shell commands
  code_execution: false    # Tool calls via code execution (saves tokens)
  chatrecall: false        # Search past conversation history
  analyze: false           # Code structure analysis
  summon: false            # Delegate tasks to subagents
  todo: false              # Todo list tracking
```

### MCP Extensions

Add or remove MCP device servers:

```yaml
mcp_extensions:
  dreame-vacuum:
    enabled: true
    type: streamable_http
    name: Dreame Vacuum
    description: Control the Dreame robot vacuum
    uri: http://localhost:6278/mcp

  tapo-plug:
    enabled: true
    type: streamable_http
    name: Tapo P105
    description: Control the Tapo P105 smart plug
    uri: http://localhost:6279/mcp
```

### System Prompt

Optionally add a custom system prompt:

```yaml
system_prompt: "You are a helpful home automation assistant. Answer in Italian."
```

## Adding a New Device

1. Create a folder `devices/<my-device>/` with its own `server.py`, `Dockerfile`, `docker-compose.yml`, and `.env`
2. Implement an MCP server using [FastMCP](https://github.com/jlowin/fastmcp) with `streamable-http` transport. See `devices/tplink-tapo/` as a reference
3. Pick an available port (e.g. `6280`)
4. Start it: `cd devices/<my-device> && docker compose up -d`
5. Register it in `goose.yaml`:
   ```yaml
   mcp_extensions:
     my-device:
       enabled: true
       type: streamable_http
       name: My Device
       description: What this device does
       uri: http://localhost:6280/mcp
   ```
6. Restart Goose: `docker compose restart goose`
