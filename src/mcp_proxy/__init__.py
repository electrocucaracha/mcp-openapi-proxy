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

import asyncio
import os

import click

from mcp_proxy.mcp import Server


@click.command()
@click.option(
    "--openapi-spec-url",
    help="Open API URL. (Default env variable OPENAPI_SPEC_URL)",
    default=os.environ.get("OPENAPI_SPEC_URL", ""),
)
@click.option(
    "--transport",
    help="Transport type",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    default="streamable-http",
)
@click.option(
    "--host",
    help="Server bind host",
    default="127.0.0.1",
)
@click.option(
    "--port",
    help="Server port number",
    type=click.IntRange(1024, 49151),
    default=8000,
)
def cli(openapi_spec_url: str, transport: str, host: str, port: int) -> None:
    server = Server(
        url=openapi_spec_url, name="OpenAPI MCP proxy", host=host, port=port
    )
    asyncio.run(server.mcp.run(transport=transport))
