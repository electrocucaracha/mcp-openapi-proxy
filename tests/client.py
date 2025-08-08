import asyncio
import json
from typing import Any

import asyncclick as click
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client


def _headers_to_dict(
    ctx: click.Context, attribute: click.Option, attributes: tuple[str, ...]
) -> dict[str, str]:
    """Click callback that converts headers specified in the form `key=value` to a
    dictionary"""
    result = {}
    for arg in attributes:
        k, v = arg.split("=")
        if k in result:
            raise click.BadParameter(f"Header {k!r} is specified twice")
        result[k] = v

    return result


async def _print_tools(
    read: MemoryObjectReceiveStream, write: MemoryObjectSendStream
) -> None:
    async with ClientSession(read, write) as session:
        await session.initialize()

        result = await session.list_tools()
        for tool in result.tools:
            print(f"******** {tool.name} ********")
            print(json.dumps(tool.inputSchema, indent=4))


async def _call_tool(
    read: MemoryObjectReceiveStream,
    write: MemoryObjectSendStream,
    name: str,
    args: dict[str, Any],
) -> None:
    async with ClientSession(read, write) as session:
        await session.initialize()

        result = await session.call_tool(name, arguments=args)
        if not result.isError:
            print(result.content[0].text)
        else:
            print("******** Error ********")
            print(result)


@click.command()
@click.option("-m", "--mcp-url", default="http://localhost:8000/mcp")
@click.option(
    "-h",
    "--headers",
    help="Header in the form key=value. Can be specified multiple times.",
    multiple=True,
    callback=_headers_to_dict,
)
async def cli(
    mcp_url: str,
    headers: dict[str, str],
):
    if "sse" in mcp_url:
        async with sse_client(mcp_url, headers=headers) as streams:
            await _print_tools(streams[0], streams[1])
            # await _call_tool(streams[0], streams[1], "upsert_summary_summaries__post", {"id": 1, "url": "http://example.com", "content": "Summary"})
    elif "mcp" in mcp_url:
        async with streamablehttp_client(mcp_url, headers=headers) as (
            read,
            write,
            _,
        ):
            await _print_tools(read, write)
            # await _call_tool(read, write, "upsert_summary_summaries__post", {"id": 1, "url": "http://example.com", "content": "Summary"})


if __name__ == "__main__":
    asyncio.run(cli())
