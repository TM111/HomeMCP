# Tapo P105 - MCP Module

MCP module to control a TP-Link Tapo P105 smart plug through the HomeMCP orchestrator.

## Exposed Tools

| Tool | Description |
|------|-------------|
| `turn_on` | Turns on the plug |
| `turn_off` | Turns off the plug |
| `toggle` | Toggles state (on → off, off → on) |
| `get_status` | Current status: on/off, name, model, Wi-Fi, firmware |

## Configuration

### 1. Create the `.env` file

Copy and fill in the `.env` file in the `tplink-tapo/` folder:

```env
TAPO_MAC=CC:BA:BD:9D:00:18
TAPO_EMAIL=your@email.com
TAPO_PASSWORD=your_password

# Direct IP (optional, skips ARP scan)
# TAPO_IP=192.168.1.4
```

| Variable | Required | Description |
|----------|:---:|-------------|
| `TAPO_MAC` | ✅ | Plug MAC address (found in the Tapo app) |
| `TAPO_EMAIL` | ✅ | Your TP-Link / Tapo account email |
| `TAPO_PASSWORD` | ✅ | Your TP-Link / Tapo account password |
| `TAPO_IP` | ❌ | Plug local IP. If not set, it is automatically resolved from MAC |

### 2. Start the container

**On Linux** (recommended — direct access to local network):

```bash
chmod +x start.sh
./start.sh
```

The `start.sh` script:
1. Reads `TAPO_MAC` from `.env`
2. Runs a ping sweep on the `192.168.1.0/24` subnet
3. Looks up the MAC in the ARP table and finds the correct IP
4. Starts the container with the resolved IP

Alternatively, if you set `TAPO_IP` in `.env`:

```bash
docker compose up -d
```

### 3. Verify

Test the connection to the plug:

```bash
docker exec tapo-mcp python -c "
import urllib.request
try:
    r = urllib.request.urlopen('http://localhost:6279/test/status')
    print(r.read().decode())
except Exception as e:
    print(e.read().decode())
"
```

Expected output:

```json
{"ok": true, "result": "State    : OFF ⛔\nName     : Soyosauce\nModel    : P105\n..."}
```

## Architecture

```
┌──────────────────────────┐
│  Orchestrator (LLM)      │
│  port 6279/sse           │
└──────────┬───────────────┘
           │ SSE
┌──────────▼───────────────┐
│  tapo-mcp (this module)  │
│  server.py :6279         │
└──────────┬───────────────┘
           │ LAN
┌──────────▼───────────────┐
│  Tapo P105 Smart Plug    │
│  192.168.1.x             │
└──────────────────────────┘
```

## Files

| File | Description |
|------|-------------|
| `server.py` | MCP server with SSE transport (used by Docker) |
| `Dockerfile` | Python 3.11 image + plugp100 + net-tools |
| `docker-compose.yml` | Docker service definition |
| `start.sh` | Startup script with MAC → IP resolution |
| `.env` | Credentials (do not commit!) |

## Notes

- Port **6279** is already registered in the orchestrator (`orchestrator/config/mcp_servers.json`)
- If the plug IP changes (DHCP), re-run `./start.sh`
- To add more Tapo plugs, duplicate the module with a different port and name
