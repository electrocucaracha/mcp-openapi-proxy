# Copyright (c) 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Script created for quick validation of MCP servers funtionality."""

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "asyncclick",
#     "mcp[cli]>=1.8.0",
# ]
# ///
import asyncio
import json
from typing import Any, Mapping

import asyncclick as click
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client


def _headers_to_dict(
    _: click.Context, __: click.Option, attributes: tuple[str, ...]
) -> Mapping[str, str | int]:
    """Click callback that converts headers specified in the form `key=value` to a
    dictionary"""
    result = {}
    for arg in attributes:
        k, v = arg.split("=")
        if k in result:
            raise click.BadParameter(f"Header {k!r} is specified twice")
        try:
            result[k] = int(v)
        except ValueError:
            result[k] = v

    return result


async def _print_tools(
    read: MemoryObjectReceiveStream, write: MemoryObjectSendStream, **kwargs
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
            for content in result.content:
                print(content.text)
        else:
            print("******** Error ********")
            print(result)


actions = {"print-tools": _print_tools, "call-tool": _call_tool}


@click.command()
@click.option("-m", "--mcp-url", default="http://localhost:8080/sse")
@click.option(
    "-a", "--action", default="print-tools", type=click.Choice(actions.keys())
)
@click.option("-t", "--tool", required=False)
@click.option(
    "-i",
    "--inputs",
    multiple=True,
    callback=_headers_to_dict,
)
@click.option(
    "-h",
    "--headers",
    help="Header in the form key=value. Can be specified multiple times.",
    multiple=True,
    callback=_headers_to_dict,
)
async def cli(
    mcp_url: str,
    action: str,
    tool: str,
    inputs: dict[str, str],
    headers: dict[str, str],
):
    """
    Client for the MCP server.
    """
    if "sse" in mcp_url:
        async with sse_client(mcp_url, headers=headers) as streams:
            await actions[action](
                read=streams[0], write=streams[1], name=tool, args=inputs
            )
    elif "mcp" in mcp_url:
        async with streamablehttp_client(mcp_url, headers=headers) as (
            read,
            write,
            _,
        ):
            await actions[action](read=read, write=write, name=tool, args=inputs)


if __name__ == "__main__":
    asyncio.run(cli())
