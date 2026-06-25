"""
Streaming chat service — calls Claude via the Anthropic API and dispatches
tool calls through the MCP protocol (Streamable HTTP transport).

Tool discovery is fully automatic: the assistant connects to each MCP server
listed in MCP_SERVERS, reads its tool catalogue, and passes the schemas to
Claude. Adding a new @mcp.tool() in mcp_server.py is sufficient — no
registry or schema updates are needed here.

To add another MCP server append an entry to MCP_SERVERS.
"""
import asyncio
import json
import os
from datetime import timedelta
from typing import AsyncGenerator

from anthropic import AsyncAnthropic
from mcp import types as mcp_types
from mcp.client.session_group import ClientSessionGroup, StreamableHttpParameters

SYSTEM_PROMPT = (
    "You are a personal running assistant built into the Running Shoe Deal Finder. "
    "You help the user manage their shoe rotation, track mileage, find deals, and make "
    "smart decisions about their running gear. You have access to tools to query owned shoes, "
    "run history, shoe notes, and current deals. Always use your tools to get current data "
    "rather than making assumptions. Be concise and direct — the user is a competitive runner, "
    "running terminology is fine. Flag proactively when a shoe is approaching its mileage limit."
)

# MCP servers the assistant can reach. Each entry needs a `name` and a `url`.
# When two servers expose a tool with the same name, pass a component_name_hook
# to ClientSessionGroup to namespace them:
#   component_name_hook=lambda name, info: f"{info.name}__{name}"
MCP_SERVERS: list[dict] = [
    {
        "name": "rundeals",
        "url": os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp"),
    },
]


def _to_anthropic_tool(tool: mcp_types.Tool) -> dict:
    """Convert an MCP Tool object to the Anthropic messages API format."""
    return {
        "name": tool.name,
        "description": tool.description or "",
        "input_schema": tool.inputSchema,
    }


def _extract_result_text(call_result: mcp_types.CallToolResult) -> str:
    """
    Pull text from an MCP CallToolResult.

    FastMCP serialises dict/list returns as pretty-printed JSON inside a
    TextContent block, so joining all text blocks gives the full payload.
    """
    if call_result.isError:
        return json.dumps({"error": "Tool call failed"})
    return "\n".join(
        block.text for block in call_result.content if block.type == "text"
    ) or "{}"


async def _run_chat(messages: list, model: str, queue: asyncio.Queue) -> None:
    """
    Runs the MCP + Claude loop in an isolated asyncio Task.

    All anyio cancel scopes created by ClientSessionGroup live entirely within
    this task, preventing the cancel-scope ordering conflict that occurs when
    the context manager straddles sse-starlette's generator iteration boundary.
    Events are pushed to `queue`; the generator in stream_chat reads them.
    A sentinel value of None signals the generator to stop.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        await queue.put({"type": "error", "message": "ANTHROPIC_API_KEY is not configured on the server."})
        await queue.put(None)
        return

    client = AsyncAnthropic(api_key=api_key)
    running_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

    try:
        async with ClientSessionGroup() as group:
            for server in MCP_SERVERS:
                url = server.get("url", "")
                if not url:
                    continue
                try:
                    await group.connect_to_server(
                        StreamableHttpParameters(
                            url=url,
                            headers=server.get("headers"),
                            timeout=timedelta(seconds=10),
                            sse_read_timeout=timedelta(seconds=300),
                        )
                    )
                except Exception as exc:
                    print(f"[chat] MCP server '{server['name']}' unavailable: {exc}")

            if not group.tools:
                await queue.put({"type": "error", "message": "No tools available from any MCP server."})
                await queue.put(None)
                return

            tool_schemas = [_to_anthropic_tool(t) for t in group.tools.values()]

            while True:
                tool_uses_by_index: dict[int, dict] = {}

                async with client.messages.stream(
                    model=model,
                    max_tokens=4096,
                    system=SYSTEM_PROMPT,
                    tools=tool_schemas,
                    messages=running_messages,
                ) as stream:
                    async for event in stream:
                        if event.type == "content_block_start":
                            if event.content_block.type == "tool_use":
                                tool_uses_by_index[event.index] = {
                                    "id": event.content_block.id,
                                    "name": event.content_block.name,
                                    "input_str": "",
                                }
                                await queue.put({"type": "tool_call", "tool": event.content_block.name})

                        elif event.type == "content_block_delta":
                            if event.delta.type == "text_delta":
                                await queue.put({"type": "text", "content": event.delta.text})
                            elif event.delta.type == "input_json_delta":
                                if event.index in tool_uses_by_index:
                                    tool_uses_by_index[event.index]["input_str"] += (
                                        event.delta.partial_json
                                    )

                        elif event.type == "content_block_stop":
                            if event.index in tool_uses_by_index:
                                tu = tool_uses_by_index[event.index]
                                try:
                                    tu["input"] = (
                                        json.loads(tu["input_str"]) if tu["input_str"] else {}
                                    )
                                except json.JSONDecodeError:
                                    tu["input"] = {}

                    final_message = await stream.get_final_message()

                tool_use_blocks = [
                    b for b in (final_message.content or []) if b.type == "tool_use"
                ]
                if not tool_use_blocks:
                    await queue.put({"type": "done"})
                    await queue.put(None)
                    return

                assistant_content = []
                for b in final_message.content:
                    if b.type == "text":
                        assistant_content.append({"type": "text", "text": b.text})
                    elif b.type == "tool_use":
                        assistant_content.append(
                            {"type": "tool_use", "id": b.id, "name": b.name, "input": b.input}
                        )
                running_messages.append({"role": "assistant", "content": assistant_content})

                tool_results: list[dict] = []
                for block in tool_use_blocks:
                    try:
                        mcp_result = await group.call_tool(block.name, block.input or {})
                        result_text = _extract_result_text(mcp_result)
                        success = not mcp_result.isError
                    except Exception as exc:
                        result_text = json.dumps({"error": str(exc)})
                        success = False

                    await queue.put({"type": "tool_result", "tool": block.name, "success": success})
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        }
                    )

                running_messages.append({"role": "user", "content": tool_results})

    except Exception as exc:
        await queue.put({"type": "error", "message": str(exc)})
    finally:
        await queue.put(None)


async def stream_chat(messages: list, model: str) -> AsyncGenerator:
    """
    Async generator that streams a Claude response as SSE event dicts.

    Spawns _run_chat in a separate asyncio Task so that ClientSessionGroup's
    anyio cancel scopes are confined to that task and never cross the SSE
    generator boundary (which would raise "Attempted to exit a cancel scope
    that isn't the current task's current cancel scope").

    Sequence of yielded events:
      {"type": "tool_call",   "tool": "get_owned_shoes"}
      {"type": "tool_result", "tool": "get_owned_shoes", "success": True}
      {"type": "text",        "content": "token…"}
      {"type": "done"}
      {"type": "error",       "message": "…"}
    """
    queue: asyncio.Queue = asyncio.Queue()
    task = asyncio.create_task(_run_chat(messages, model, queue))
    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event
    finally:
        if not task.done():
            task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
