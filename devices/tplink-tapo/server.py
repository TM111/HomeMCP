
"""
MCP Server for Tapo P105 - SSE transport

Exposes Tapo P105 smart plug commands as MCP tools via SSE.

Environment variables:
    TAPO_MAC      - Plug MAC address (e.g. XX:XX:XX:XX:XX:XX)
    TAPO_IP       - Plug local IP (optional, skips ARP scan)
    TAPO_EMAIL    - Tapo account email
    TAPO_PASSWORD - Tapo account password
"""

import asyncio
import subprocess
import re
import logging
import os

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp import types
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

from plugp100.common.credentials import AuthCredential
from plugp100.new.device_factory import connect, DeviceConnectConfiguration

import uvicorn

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


# ── Load credentials ──────────────────────────────────────────────────────────
def _load_credentials() -> dict:
    data = {
        "mac":      os.environ.get("TAPO_MAC"),
        "ip":       os.environ.get("TAPO_IP"),
        "email":    os.environ.get("TAPO_EMAIL"),
        "password": os.environ.get("TAPO_PASSWORD"),
    }
    required = {"mac", "email", "password"}
    missing = {k for k in required if not data.get(k)}
    if missing:
        raise KeyError(f"Missing environment variables: {missing}")
    log.debug(f"Credentials loaded: mac={data['mac']}, ip={data.get('ip', 'auto')}")
    return data


# ── Resolve IP from MAC ───────────────────────────────────────────────────────
def _normalize_mac(mac: str) -> str:
    return re.sub(r"[:\-]", "", mac).lower()


def _find_ip_by_mac(target_mac: str) -> str:
    log.debug(f"Looking up IP for MAC: {target_mac}")

    try:
        subprocess.run(
            ["ping", "-b", "-c", "1", "-W", "1", "192.168.1.255"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        log.warning("ping not available, skipping broadcast")

    try:
        output = subprocess.check_output(["arp", "-a"], text=True)
    except FileNotFoundError:
        raise RuntimeError("Command 'arp' not found. Install net-tools.")

    target = _normalize_mac(target_mac)

    for line in output.splitlines():
        match = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([0-9a-fA-F:\-]{17})", line)
        if not match:
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:\-]{17})", line)
        if match:
            ip = match.group(1)
            mac = _normalize_mac(match.group(2))
            if mac == target:
                log.debug(f"IP found: {ip}")
                return ip

    raise RuntimeError(
        f"Device with MAC {target_mac} not found on the network.\n"
        "Make sure the plug is powered on and connected to Wi-Fi."
    )


# ── Connection ────────────────────────────────────────────────────────────────
async def _connect(ip: str, email: str, password: str):
    log.debug(f"Connecting to {ip}")
    credentials = AuthCredential(email, password)
    attempts = [
        dict(device_type="SMART.TAPOPLUG", encryption_type="klap",        encryption_version=2),
        dict(device_type="SMART.TAPOPLUG", encryption_type="klap",        encryption_version=1),
        dict(device_type="SMART.TAPOPLUG", encryption_type="passthrough", encryption_version=1),
    ]
    last_error = None
    for params in attempts:
        try:
            config = DeviceConnectConfiguration(host=ip, credentials=credentials, **params)
            device = await connect(config)
            await device.update()
            return device
        except Exception as e:
            log.warning(f"Attempt failed ({params}): {e}")
            last_error = e
    raise RuntimeError(f"Connection failed on {ip}: {last_error}")


async def _get_device():
    c = _load_credentials()
    ip = c.get("ip") or _find_ip_by_mac(c["mac"])
    return await _connect(ip, c["email"], c["password"])


# ── Plug logic ────────────────────────────────────────────────────────────────
async def _turn_on() -> str:
    device = await _get_device()
    result = await device.turn_on()
    result.get_or_raise()
    await device.client.close()
    return "Plug turned ON ✅"


async def _turn_off() -> str:
    device = await _get_device()
    result = await device.turn_off()
    result.get_or_raise()
    await device.client.close()
    return "Plug turned OFF ⛔"


async def _toggle() -> str:
    device = await _get_device()
    is_on = device.is_on
    if is_on:
        result = await device.turn_off()
        msg = "Plug turned OFF ⛔ (was on)"
    else:
        result = await device.turn_on()
        msg = "Plug turned ON ✅ (was off)"
    result.get_or_raise()
    await device.client.close()
    return msg


async def _get_status() -> str:
    device = await _get_device()
    state = "ON ✅" if device.is_on else "OFF ⛔"
    msg = (
        f"State    : {state}\n"
        f"Name     : {device.nickname}\n"
        f"Model    : {device.model}\n"
        f"Wi-Fi    : {device.wifi_info}\n"
        f"Firmware : {device.firmware_version}"
    )
    await device.client.close()
    return msg


# ── MCP Server ────────────────────────────────────────────────────────────────
server = Server("tapo-p105")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="turn_on",
            description="Turns on the Tapo P105 smart plug",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="turn_off",
            description="Turns off the Tapo P105 smart plug",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="toggle",
            description="Toggles the plug state: turns it off if on, turns it on if off",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_status",
            description="Returns the current plug status (on/off, model, firmware, Wi-Fi)",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    log.debug(f"call_tool: {name}")
    try:
        if name == "turn_on":
            result = await _turn_on()
        elif name == "turn_off":
            result = await _turn_off()
        elif name == "toggle":
            result = await _toggle()
        elif name == "get_status":
            result = await _get_status()
        else:
            result = f"Unknown tool: {name}"
    except Exception as e:
        log.error(f"Error in call_tool {name}: {e}", exc_info=True)
        result = f"Error: {e}"

    return [types.TextContent(type="text", text=result)]


# ── SSE Transport ─────────────────────────────────────────────────────────────
sse = SseServerTransport("/messages/")


async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def handle_test_status(request):
    """GET /test/status — quick test for get_status (no MCP client needed)."""
    try:
        result = await _get_status()
        return JSONResponse({"ok": True, "result": result})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
        Route("/test/status", endpoint=handle_test_status),
    ],
)


if __name__ == "__main__":
    log.info("Tapo MCP Server started (SSE on port 6279)")
    uvicorn.run(app, host="0.0.0.0", port=6279)
