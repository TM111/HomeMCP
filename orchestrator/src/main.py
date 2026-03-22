"""
HomeMCP Orchestrator - Main entry point

Connects to Ollama LLM and multiple MCP servers to provide
a unified smart home assistant via interactive chat.

Environment variables:
    OLLAMA_HOST  - Ollama API URL (default: http://localhost:11434)
    OLLAMA_MODEL - Model name (default: qwen2.5:7b)
    MCP_CONFIG   - Path to MCP servers config (default: config/mcp_servers.json)
"""

import asyncio
import json
import os
import sys

from ollama import AsyncClient as OllamaClient
from ollama import ResponseError
from mcp_client import MCPManager

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
MCP_CONFIG = os.getenv("MCP_CONFIG", "config/mcp_servers.json")

SYSTEM_PROMPT = (
    "You are a smart home assistant called HomeMCP. "
    "You can control devices in the house using the available tools. "
    "When the user asks you to do something, use the appropriate tools. "
    "Always respond in the same language the user is using."
)


async def wait_for_ollama(client: OllamaClient, retries: int = 30, delay: float = 2.0):
    """Wait until Ollama is reachable."""
    for i in range(retries):
        try:
            await client.list()
            return
        except Exception:
            if i < retries - 1:
                print(f"Waiting for Ollama... ({i + 1}/{retries})")
                await asyncio.sleep(delay)
    raise RuntimeError("Could not connect to Ollama after multiple attempts")


async def ensure_model(client: OllamaClient, model: str):
    """Pull the model if it is not already available locally."""
    try:
        await client.show(model)
        print(f"Model '{model}' ready.")
    except Exception:
        print(f"Pulling model '{model}', this may take a while...")
        await client.pull(model)
        print(f"Model '{model}' pulled successfully.")


async def verify_cloud_auth(client: OllamaClient, model: str):
    """If using a cloud model, verify auth works. Guide user through signin if needed."""
    try:
        await client.chat(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
        )
        print("Cloud auth OK.")
    except ResponseError as e:
        if e.status_code != 401:
            raise
        print("\n" + "=" * 55)
        print("  CLOUD MODEL - Authentication required!")
        print("=" * 55)
        print(f"  Model '{model}' is a cloud model.")
        print("  You need to sign in to ollama.com.")
        print()
        print("  Run this in another terminal:")
        print()
        print("    docker exec -it homemcp-ollama ollama signin")
        print()
        print("  Follow the instructions, then come back here.")
        print("=" * 55)

        while True:
            try:
                ans = input("\nPress Enter after signing in (or 'q' to quit): ").strip()
            except (EOFError, KeyboardInterrupt):
                sys.exit(1)
            if ans.lower() in ("q", "quit", "exit"):
                sys.exit(0)

            try:
                await client.chat(
                    model=model,
                    messages=[{"role": "user", "content": "hi"}],
                )
                print("Auth verified! Continuing...\n")
                return
            except ResponseError as retry_err:
                if retry_err.status_code == 401:
                    print("  Still unauthorized. Make sure 'ollama signin' completed successfully.")
                else:
                    raise


def load_config(path: str) -> list[dict]:
    with open(path, "r") as f:
        return json.load(f).get("mcp_servers", [])


async def chat_loop(client: OllamaClient, model: str, mcp: MCPManager):
    tools = mcp.get_tools_for_ollama()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("\n=== HomeMCP - Smart Home Assistant ===")
    print(f"  Model:   {model}")
    print(f"  Servers: {', '.join(mcp.sessions.keys()) or 'none'}")
    tool_names = [t["function"]["name"] for t in tools]
    print(f"  Tools:   {', '.join(tool_names) or 'none'}")
    print("  Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            break

        messages.append({"role": "user", "content": user_input})

        try:
            response = await client.chat(
                model=model,
                messages=messages,
                tools=tools or None,
            )
        except Exception as e:
            print(f"  Error: {e}")
            messages.pop()  # remove failed user message
            continue

        # Tool-calling loop
        while response.message.tool_calls:
            messages.append(response.message)

            for tc in response.message.tool_calls:
                name = tc.function.name
                args = tc.function.arguments
                print(f"  [tool] {name}({json.dumps(args, ensure_ascii=False)})")

                result_text = await mcp.call_tool(name, args)
                print(f"  [result] {result_text}")

                messages.append({"role": "tool", "content": result_text})

            try:
                response = await client.chat(
                    model=model,
                    messages=messages,
                    tools=tools or None,
                )
            except Exception as e:
                print(f"  Error: {e}")
                break

        content = response.message.content
        messages.append({"role": "assistant", "content": content})
        print(f"Assistant: {content}\n")


async def main():
    servers = load_config(MCP_CONFIG)

    ollama = OllamaClient(host=OLLAMA_HOST)
    await wait_for_ollama(ollama)
    await ensure_model(ollama, OLLAMA_MODEL)
    await verify_cloud_auth(ollama, OLLAMA_MODEL)

    mcp = MCPManager()
    await mcp.connect(servers)

    try:
        await chat_loop(ollama, OLLAMA_MODEL, mcp)
    finally:
        await mcp.close()
        print("Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
