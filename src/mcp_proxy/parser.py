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

"""Module the converts OpenAPI types to Python code."""

import logging

from openapi_parser.enumeration import DataType
from openapi_parser.specification import AnyOf, Operation, Schema

logger = logging.getLogger()

# OpenAPI 3.0 Data Types mapping
# (https://swagger.io/docs/specification/v3_0/data-models/data-types/)
data_type = {
    DataType.STRING: "str",
    DataType.INTEGER: "int",
    DataType.NUMBER: "float",
    DataType.BOOLEAN: "bool",
    DataType.OBJECT: "dict",
    DataType.ARRAY: "list",
    DataType.NULL: "None",
}


def get_function_template(url_path: str, operation: Operation) -> str:
    """
    Get the python function definition for the MCP tool.

    Returns:
        str
    """

    inputs = _get_inputs(operation)
    func_name = operation.operation_id

    params = ", ".join(
        [f"{input.name}: {input.type}{input.default}" for input in inputs]
    )
    params_docstring = ""
    if len(inputs) > 0:
        params_docstring = (
            "\n    Parameters:\n"
            + "\n".join(
                [
                    f"        {input.name} ({input.type}): {input.title}"
                    for input in inputs
                ]
            )
            + "\n"
        )
    data_template = "{%s}" % ", ".join(
        [f"'{input.name}': {input.name}" for input in inputs]
    )
    return f"""def {func_name}({params}) -> dict:
    '''
    {operation.summary}
    {params_docstring}
    Returns:
        dict
    '''
    import requests

    data={data_template}
    response = requests.request('{operation.method.name}', {url_path}, json=data)

    return response.json()
    """


class Input:
    """
    This class convers OpenAPI paramaters in Python inputs.
    """

    def __init__(self, name: str, schema: Schema):
        self._name = name
        if isinstance(schema, AnyOf):
            self._type = "|".join([self._get_type(s.type) for s in schema.schemas])
        else:
            self._type = self._get_type(schema.type)
        self._default = schema.default
        self._title = schema.title

    def _get_type(self, _type: DataType, required: bool = True) -> str:
        if _type in data_type:
            return data_type[_type] if required else f"{data_type[_type]}|None"
        return ""

    @property
    def name(self) -> str:
        """
        Get name of the input.

        Returns:
            str
        """
        return self._name

    @property
    def type(self) -> str:
        """
        Get type of the input.

        Returns:
            str
        """
        return self._type

    @property
    def title(self) -> str:
        """
        Get title of the input.

        Returns:
            str
        """
        return self._title

    @property
    def default(self) -> str:
        """
        Get default value of the input.

        Returns:
            str
        """
        if self._default is not None:
            if str(self._default) == "":
                return " = ''"
            return f" = {self._default}"
        return ""


def _get_inputs(operation: Operation) -> list[Input]:
    inputs = [
        Input(param.name, param.schema)
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
                        Input(prop.name, prop.schema)
                        for prop in content.schema.properties
                    ]
                )
    return inputs
