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

"""Module providing MCP server basing on OpenAPI specification."""

import logging
from types import FunctionType
from urllib.parse import urlparse

from mcp.server.fastmcp import FastMCP
from openapi_parser import parse

from mcp_proxy.parser import get_function_template

logger = logging.getLogger()


class Server:
    """
    This class generates MCP tools using a OpenAPI spec definition.
    """

    def __init__(
        self,
        url: str,
        host: str = "127.0.0.1",
        port: int = 8000,
        skip_tool: list[dict] | None = None,
    ):
        self._mcp = FastMCP(name="OpenAPI MCP proxy", host=host, port=port)

        parsed_url = urlparse(url)
        openapi_spec = parse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        if len(openapi_spec.servers) > 0:
            base_url = openapi_spec.servers[0].url

        for path in openapi_spec.paths:
            for operation in path.operations:
                if skip_tool and operation.operation_id in skip_tool:
                    continue
                func_name = operation.operation_id
                func_template = get_function_template(
                    f'f"{base_url}{path.url}"', operation
                )
                new_func = compile(func_template, "<string>", "exec")
                for co_consts in new_func.co_consts:
                    if hasattr(co_consts, "co_name") and co_consts.co_name == func_name:
                        mcp_func = FunctionType(co_consts, globals(), func_name)

                        # Register MCP tool function
                        self._mcp.add_tool(
                            fn=mcp_func,
                            name=func_name,
                            description=operation.summary,
                        )
                        logger.info("%s MCP tool registered", func_name)
                        break

    @property
    def mcp(self) -> FastMCP:
        """
        Get FastMCP server created based on the OpenAPI specification.

        Returns:
            FastMCP
        """
        return self._mcp

    def run(self, transport: str = "streamable-http"):
        """
        Initiate the FastMCP server created.
        """
        self._mcp.run(transport=transport)
