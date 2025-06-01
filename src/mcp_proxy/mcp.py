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

from types import FunctionType
from urllib.parse import urlparse

from mcp.server.fastmcp import FastMCP
from openapi_parser import parse


class Server:
    def __init__(self, url: str, name: str, host: str = "127.0.0.1", port: int = 8000):
        self.mcp = FastMCP(name=name, host=host, port=port)

        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        openapi_spec = parse(url)

        for path in openapi_spec.paths:
            for operation in path.operations:
                func_name = operation.operation_id
                url_path = f'f"{base_url}{path.url}"'

                # Retrieve the operation inputs
                inputs = [
                    param.name for param in operation.parameters if param.required
                ]
                if operation.request_body and operation.request_body.required:
                    for content in operation.request_body.content:
                        for prop in content.schema.properties:
                            inputs.append(prop.name)

                # Generate MCP tool function
                data_template = "{%s}" % ", ".join(
                    [f"'{input}': {input}" for input in inputs]
                )
                func_template = f"""def {func_name}({", ".join(inputs)}):
                    import requests
                    data={data_template}
                    response = requests.request('{operation.method.name}', {url_path}, json=data)
                    return response.json()
                """
                new_func = compile(func_template, "<string>", "exec")
                mcp_func = FunctionType(new_func.co_consts[0], globals(), func_name)

                # Register MCP tool function
                self.mcp.add_tool(
                    fn=mcp_func,
                    name=func_name,
                    description=operation.summary,
                )
