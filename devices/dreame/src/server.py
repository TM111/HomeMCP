"""
mcp.py - Dreame Vacuum MCP Server

Exposes dreame vacuum commands as MCP tools using FastMCP.
Reads configuration from environment variables (or .env file).

Usage:
    python mcp.py

Environment variables:
    TOKEN     - Home Assistant Bearer token
    ENTITY_ID - Vacuum entity ID (e.g. vacuum.mochi)
    HA_URL    - Home Assistant URL (default: http://homeassistant:8123)
"""

import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from commands import go_to_point, list_rooms, clean_rooms

load_dotenv(".env")

HA_URL    = os.getenv("HA_URL", "http://homeassistant:8123")
TOKEN     = os.getenv("TOKEN")
ENTITY_ID = os.getenv("ENTITY_ID")

if not TOKEN:
    raise RuntimeError("TOKEN not set in .env or environment")
if not ENTITY_ID:
    raise RuntimeError("ENTITY_ID not set in .env or environment")

mcp = FastMCP("Dreame Vacuum")


@mcp.tool
def vacuum_list_rooms() -> dict:
    """List all rooms available on the vacuum map, with their IDs and names."""
    result = list_rooms(HA_URL, TOKEN, ENTITY_ID)
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(f"Failed to list rooms: {result['error']} (HTTP {result['status']})")
    return result


@mcp.tool
def vacuum_clean_rooms(
    room_ids: list[int],
    repeats: int = 1,
) -> str:
    """
    Start cleaning one or more rooms.

    Args:
        room_ids: List of room IDs to clean (get them from vacuum_list_rooms).
        repeats:  Number of cleaning passes, 1 to 3.
    """
    result = clean_rooms(HA_URL, TOKEN, room_ids, ENTITY_ID, repeats=repeats)
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(f"Failed to start cleaning: {result['error']} (HTTP {result['status']})")
    return f"Cleaning started for rooms {room_ids} (repeats={repeats})"


@mcp.tool
def vacuum_go_to_point(x: int, y: int) -> str:
    """
    Move the vacuum to a specific point on the map.

    Args:
        x: X coordinate on the map.
        y: Y coordinate on the map.
    """
    result = go_to_point(HA_URL, TOKEN, x, y, ENTITY_ID)
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(f"Failed to go to point: {result['error']} (HTTP {result['status']})")
    return f"Vacuum moving to ({x}, {y})"


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=6278)
