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
# TAPO_IP=192.168.1.4  # Required on Windows/Mac, optional on Linux
```

| Variable      | Required | Description |
|-------------- |:-------:|------------------------------------------------------|
| `TAPO_MAC`    |   ✅    | Plug MAC address (found in the Tapo app)             |
| `TAPO_EMAIL`  |   ✅    | Your TP-Link / Tapo account email                    |
| `TAPO_PASSWORD`|  ✅    | Your TP-Link / Tapo account password                 |
| `TAPO_IP`     | Win/Mac | Plug local IP. **Required on Windows/Mac**. On Linux, if not set, it is automatically resolved from MAC. |




### ⚠️  Platform Notes

- On **Linux**, the server automatically resolves the plug's IP from the MAC address if `TAPO_IP` is not set in `.env` (no extra script needed).
- On **Windows** and **Mac**, you **must** set `TAPO_IP` in `.env` because automatic IP resolution is not supported due to Docker Desktop network limitations.



### 2. Start the container

Start the container normally:

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
