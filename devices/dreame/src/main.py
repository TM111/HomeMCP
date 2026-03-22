


"""
main.py - Dreame Vacuum CLI

This script provides a command-line interface to control a Dreame Vacuum via Home Assistant.
It supports the following commands:
    - go_to_point: Move the vacuum to specific X, Y coordinates
    - list_rooms: List all available rooms
    - clean_rooms: Clean one or more rooms by their IDs

Usage examples:
    python main.py go_to_point 100 200
    python main.py list_rooms
    python main.py clean_rooms 1 2 --repeats 2

Environment variables:
    - TOKEN: Bearer token for Home Assistant API (can be set in .env)
    - HA_URL: Home Assistant base URL (optional, default: http://homeassistant:8123)
    - ENTITY_ID: Vacuum entity ID (optional, default: vacuum.mochi)
"""

import argparse
import os
from dotenv import load_dotenv
from commands import go_to_point, list_rooms, clean_rooms
from typing import Any

def main():

    # Argument parser setup
    parser = argparse.ArgumentParser(description="Control Dreame Vacuum via Home Assistant")
    parser.add_argument('--ha-url', default=os.getenv('HA_URL', 'http://homeassistant:8123'), help='Home Assistant URL')
    parser.add_argument('--token', default=None, help='Authentication token (if not provided, read from .env)')
    parser.add_argument('--entity-id', default=None, help='Vacuum entity ID')

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', required=True)

    # go_to_point command
    parser_goto = subparsers.add_parser('go_to_point', help='Move to X Y coordinates')
    parser_goto.add_argument('x', type=int, help='X coordinate')
    parser_goto.add_argument('y', type=int, help='Y coordinate')

    # list_rooms command
    parser_rooms = subparsers.add_parser('list_rooms', help='List available rooms')

    # clean_rooms command
    parser_clean = subparsers.add_parser('clean_rooms', help='Clean one or more rooms')
    parser_clean.add_argument('rooms', nargs='+', type=int, help='IDs of rooms to clean')
    parser_clean.add_argument('--repeats', type=int, default=1, help='Number of cleaning passes (1-3)')

    args = parser.parse_args()

    # Load environment variables from .env if present
    load_dotenv('.env')
    token = args.token or os.getenv('TOKEN')
    ha_url = args.ha_url
    entity_id = args.entity_id or os.getenv('ENTITY_ID')

    if not token:
        print('Token not provided and not found in .env')
        exit(1)

    if not entity_id:
        print('Entity ID not provided and not found in .env')
        exit(1)

    # Command dispatch
    if args.command == 'go_to_point':
        # Move the vacuum to the specified coordinates
        result: Any = go_to_point(ha_url, token, args.x, args.y, entity_id)
        if isinstance(result, dict) and 'error' in result:
            print(f"Error: {result['error']} (HTTP {result['status']})")
            exit(1)
        else:
            print(f"Status: {result}")
    elif args.command == 'list_rooms':
        # List all available rooms
        result: Any = list_rooms(ha_url, token, entity_id)
        if isinstance(result, dict) and 'error' in result:
            print(f"Error: {result['error']} (HTTP {result['status']})")
            exit(1)
        else:
            print(result)
    elif args.command == 'clean_rooms':
        # Start cleaning the specified rooms
        result: Any = clean_rooms(ha_url, token, args.rooms, args.repeats, entity_id)
        if isinstance(result, dict) and 'error' in result:
            print(f"Error: {result['error']} (HTTP {result['status']})")
            exit(1)
        else:
            print(f"Status: {result}")

if __name__ == "__main__":
    main()
