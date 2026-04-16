#!/usr/bin/env python3
"""
Entrypoint for Goose container.
Reads goose.yaml (single config), builds the full Goose config,
and starts Goose with a single process.
"""
import sys
import os
import yaml
from pathlib import Path

GOOSE_CONFIG = Path("/root/.config/goose/config.yaml")
USER_CONFIG = Path("/goose.yaml")

# Platform extension metadata
PLATFORM_META = {
    "developer": {
        "display_name": "Developer",
        "description": "Write and edit files, and execute shell commands",
    },
    "code_execution": {
        "display_name": "Code Mode",
        "description": "Goose will make extension calls through code execution, saving tokens",
    },
    "chatrecall": {
        "display_name": "Chat Recall",
        "description": "Search past conversations and load session summaries for contextual memory",
    },
    "analyze": {
        "display_name": "Analyze",
        "description": "Analyze code structure with tree-sitter: directory overviews, file details, symbol call graphs",
    },
    "summon": {
        "display_name": "Summon",
        "description": "Load knowledge and delegate tasks to subagents",
    },
    "todo": {
        "display_name": "Todo",
        "description": "Enable a todo list for goose so it can keep track of what it is doing",
    },
}


def build_config():
    """Build Goose config.yaml from goose.yaml."""
    if not USER_CONFIG.exists():
        print("[entrypoint] No goose.yaml found, starting with defaults.")
        return None

    user_cfg = yaml.safe_load(USER_CONFIG.read_text()) or {}

    # Load existing config to preserve gateway pairings
    existing = {}
    if GOOSE_CONFIG.exists():
        existing = yaml.safe_load(GOOSE_CONFIG.read_text()) or {}

    extensions = {}

    # Platform extensions
    for name, meta in PLATFORM_META.items():
        enabled = user_cfg.get("platform_extensions", {}).get(name, False)
        extensions[name] = {
            "available_tools": [],
            "bundled": True,
            "description": meta["description"],
            "display_name": meta["display_name"],
            "enabled": bool(enabled),
            "name": name,
            "type": "platform",
        }

    # MCP extensions
    mcp_ext = user_cfg.get("mcp_extensions", {})
    for key, val in mcp_ext.items():
        if not val.get("enabled", True):
            continue
        extensions[key] = {
            "enabled": True,
            "type": val.get("type", "streamable_http"),
            "name": val.get("name", key),
            "description": val.get("description", ""),
            "uri": val["uri"],
        }

    # Do NOT inject gateway_configs here — Goose reads it from CLI args.
    # Having it in both config AND CLI causes dual polling loops.
    config = {
        "extensions": extensions,
    }

    # System prompt
    system_prompt = user_cfg.get("system_prompt")
    if system_prompt:
        config["GOOSE_SYSTEM_PROMPT"] = system_prompt

    GOOSE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    GOOSE_CONFIG.write_text(yaml.dump(config, default_flow_style=False, allow_unicode=True))

    mcp_names = [k for k in mcp_ext if mcp_ext[k].get("enabled", True)]
    platform_on = [k for k, v in user_cfg.get("platform_extensions", {}).items() if v]
    print(f"[entrypoint] Platform extensions enabled: {platform_on or 'none'}")
    print(f"[entrypoint] MCP extensions: {mcp_names or 'none'}")


if __name__ == "__main__":
    build_config()

    args = sys.argv[1:]
    os.execvp("goose", ["goose"] + args)
