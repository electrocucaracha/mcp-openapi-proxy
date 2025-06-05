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

logger = logging.getLogger()


class Server:
    def __init__(
        self,
        url: str,
        name: str,
        host: str = "127.0.0.1",
        port: int = 8000,
        skip_tool: list = [],
    ):
        self.mcp = FastMCP(name=name, host=host, port=port)

        parsed_url = urlparse(url)
        openapi_spec = parse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        if len(openapi_spec.servers) > 0:
            base_url = openapi_spec.servers[0].url

        for path in openapi_spec.paths:
            for operation in path.operations:
                if operation.operation_id in skip_tool:
                    continue
                func_name = operation.operation_id
                url_path = f'f"{base_url}{path.url}"'

                # Retrieve the operation inputs
                inputs = [
                    {
                        "name": param.name,
                        "type": param.schema.type.value,
                        "default": param.schema.default,
                    }
                    for param in operation.parameters
                    if param.required
                ]

                # OpenAPI 3.0 Data Types mapping (https://swagger.io/docs/specification/v3_0/data-models/data-types/)
                data_type = {
                    "string": "str",
                    "integer": "int",
                    "number": "float",
                    "boolean": "bool",
                    "object": "dict",
                    "array": "list",
                }

                # Generate MCP tool function
                params = ", ".join(
                    [
                        f"{input['name']}: {data_type[input['type']]}{' = ' + input['default'] if input['default'] else ''}"
                        for input in inputs
                    ]
                )
                data_template = "{%s}" % ", ".join(
                    [f"'{input['name']}': {input['name']}" for input in inputs]
                )
                func_template = f"""def {func_name}({params}) -> dict:
    import requests

    data={data_template}
    response = requests.request('{operation.method.name}', {url_path}, json=data)

    return response.json()
                """
                new_func = compile(func_template, "<string>", "exec")
                for co_consts in new_func.co_consts:
                    if hasattr(co_consts, "co_name") and co_consts.co_name == func_name:
                        mcp_func = FunctionType(co_consts, globals(), func_name)

                        # Register MCP tool function
                        self.mcp.add_tool(
                            fn=mcp_func,
                            name=func_name,
                            description=operation.summary,
                        )
                        logger.info(f"{func_name} MCP tool registered")
                        break
