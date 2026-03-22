"""
MCP Client Manager

Connects to multiple MCP servers via SSE and exposes their tools
in a format compatible with Ollama's tool-calling API.
"""

import json
import traceback
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client


class MCPManager:
    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}
        self.tool_map: dict[str, tuple[ClientSession, object]] = {}
        self._exit_stack = AsyncExitStack()

    async def connect(self, servers: list[dict]):
        """Connect to a list of MCP servers defined in config."""
        for server in servers:
            name = server["name"]
            url = server["url"]
            print(f"Connecting to '{name}' at {url} ...")
            try:
                read, write = await self._exit_stack.enter_async_context(
                    sse_client(url, sse_read_timeout=30)
                )
                session = await self._exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
                await session.initialize()

                resp = await session.list_tools()
                self.sessions[name] = session

                for tool in resp.tools:
                    self.tool_map[tool.name] = (session, tool)
                    print(f"  + {tool.name}")

                print(f"  Connected ({len(resp.tools)} tools)")
            except Exception as exc:
                print(f"  Failed to connect to '{name}': {exc}")
                traceback.print_exc()

    def get_tools_for_ollama(self) -> list[dict]:
        """Convert MCP tools to Ollama / OpenAI function-calling format."""
        result = []
        for name, (_, tool) in self.tool_map.items():
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": (
                        tool.inputSchema
                        if tool.inputSchema
                        else {"type": "object", "properties": {}}
                    ),
                },
            })
        return result

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Call a tool by name and return its text result."""
        if name not in self.tool_map:
            return json.dumps({"error": f"Unknown tool: {name}"})

        session, _ = self.tool_map[name]
        result = await session.call_tool(name, arguments)

        texts = []
        for item in result.content:
            if hasattr(item, "text"):
                texts.append(item.text)
            else:
                texts.append(str(item))

        return "\n".join(texts) if texts else "OK"

    async def close(self):
        await self._exit_stack.aclose()
