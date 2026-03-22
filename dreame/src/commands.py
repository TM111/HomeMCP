"""
commands.py - Dreame Vacuum API functions

This module provides functions to interact with a Dreame Vacuum via Home Assistant's HTTP API.
All functions are pure and require explicit parameters for Home Assistant URL, token, and entity ID.
"""

from typing import Any, Dict, List, Union
import requests

def go_to_point(
    ha_url: str,
    token: str,
    x: int,
    y: int,
    entity_id: str
) -> Union[int, Dict[str, Any]]:
    """
    Move the Dreame vacuum to a specific (x, y) coordinate.

    Args:
        ha_url: Home Assistant base URL.
        token: Bearer token for authentication.
        x: X coordinate.
        y: Y coordinate.
        entity_id: The entity ID of the vacuum.

    Returns:
        HTTP status code on success, or a dict with 'status' and 'error' on failure.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        f"{ha_url}/api/services/dreame_vacuum/vacuum_goto",
        headers=headers,
        json={
            "entity_id": entity_id,
            "x": x,
            "y": y,
        },
    )
    if 200 <= response.status_code < 300:
        return response.status_code
    else:
        try:
            error = response.json()
        except Exception:
            error = response.text
        print(f"go_to_point error: HTTP {response.status_code} - {error}")
        return {"status": response.status_code, "error": error}

def list_rooms(
    ha_url: str,
    token: str,
    entity_id: str
) -> Union[Dict[int, str], Dict[str, Any]]:
    """
    Retrieve the list of rooms from the Dreame vacuum.

    Args:
        ha_url: Home Assistant base URL.
        token: Bearer token for authentication.
        entity_id: The entity ID of the vacuum.

    Returns:
        Dictionary mapping room IDs to names, or a dict with 'status' and 'error' on failure.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.get(
        f"{ha_url}/api/states/{entity_id}",
        headers=headers,
    )
    if 200 <= response.status_code < 300:
        attributes = response.json().get("attributes", {})
        rooms_data = attributes.get("rooms", {})
        rooms: Dict[int, str] = {}
        for map_name, room_list in rooms_data.items():
            print(f"🗺️  Map: {map_name}")
            for room in room_list:
                print(f"  ID {room['id']}: {room['name']}")
                rooms[room['id']] = room['name']
        return rooms
    else:
        try:
            error = response.json()
        except Exception:
            error = response.text
        print(f"list_rooms error: HTTP {response.status_code} - {error}")
        return {"status": response.status_code, "error": error}

def clean_rooms(
    ha_url: str,
    token: str,
    rooms: List[int],
    entity_id: str,
    repeats: int = 1
) -> Union[int, Dict[str, Any]]:
    """
    Start cleaning for one or more rooms.

    Args:
        ha_url: Home Assistant base URL.
        token: Bearer token for authentication.
        rooms: List of room IDs to clean.
        repeats: Number of cleaning passes (1-3).
        entity_id: The entity ID of the vacuum.

    Returns:
        HTTP status code on success, or a dict with 'status' and 'error' on failure.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        f"{ha_url}/api/services/dreame_vacuum/vacuum_clean_segment",
        headers=headers,
        json={
            "entity_id": entity_id,
            "segments": rooms,
            "repeats": repeats,
        },
    )
    if 200 <= response.status_code < 300:
        print(f"Cleaning started for rooms {rooms} → HTTP {response.status_code}")
        return response.status_code
    else:
        try:
            error = response.json()
        except Exception:
            error = response.text
        print(f"clean_rooms error: HTTP {response.status_code} - {error}")
        return {"status": response.status_code, "error": error}