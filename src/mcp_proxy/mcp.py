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
from openapi_parser.specification import Operation

logger = logging.getLogger()

# OpenAPI 3.0 Data Types mapping
# (https://swagger.io/docs/specification/v3_0/data-models/data-types/)
data_type = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "object": "dict",
    "array": "list",
}


def _get_function_template(url_path: str, operation: Operation) -> str:
    inputs = _get_inputs(operation)
    func_name = operation.operation_id

    params = ", ".join(
        [f"{input['name']}: {input['type']}{input['default']}" for input in inputs]
    )
    params_docstring = "\n".join(
        [
            f"        {input['name']} ({input['type']}): {input['title']}"
            for input in inputs
        ]
    )
    data_template = "{%s}" % ", ".join(
        [f"'{input['name']}': {input['name']}" for input in inputs]
    )
    return f"""def {func_name}({params}) -> dict:
    '''
    {operation.summary}

    Parameters:
{params_docstring}

    Returns:
        dict
    '''
    import requests

    data={data_template}
    response = requests.request('{operation.method.name}', {url_path}, json=data)

    return response.json()
    """


def _get_inputs(operation: Operation) -> list:
    inputs = [
        {
            "name": param.name,
            "type": data_type[param.schema.type.value],
            "default": (
                " = " + str(param.schema.default) if param.schema.default else ""
            ),
            "title": param.schema.title,
        }
        for param in operation.parameters
        if param.required
    ]
    if (
        hasattr(operation, "request_body")
        and operation.request_body
        and operation.request_body.required
    ):
        for content in operation.request_body.content:
            if content.schema.required:
                inputs.extend(
                    [
                        {
                            "name": prop.name,
                            "type": data_type[
                                (
                                    prop.schema.type.value
                                    if prop.schema.type.value != "anyOf"
                                    else prop.schema.schemas[0].type.value
                                )
                            ],
                            "default": (
                                " = " + str(prop.schema.default)
                                if prop.schema.default
                                else ""
                            ),
                            "title": prop.schema.title,
                        }
                        for prop in content.schema.properties
                    ]
                )
    return inputs


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
                func_template = _get_function_template(
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
