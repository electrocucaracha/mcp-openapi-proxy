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

"""Test module that validates parser functionatily."""

import pytest
from openapi_parser import parse

from mcp_proxy.parser import get_function_template


@pytest.fixture(name="upsert_summary_summaries__post")
def get_upsert_summary_summaries__post_tool():
    """Fixture for the get upsert_summary_summaries__post function as string."""

    return """@self._mcp.tool()
def upsert_summary_summaries__post(id: int|None, url: str, content: str = '') -> dict:
    '''
    Upsert Summary

    Parameters:
        id (int|None): Id
        url (str): Url
        content (str): Content

    Returns:
        dict
    '''
    import requests

    data={'id': id, 'url': url, 'content': content}
    response = requests.request('POST', f"http://localhost:8080/v1/summaries/", json=data)

    return response.json()
    """


@pytest.fixture(name="read_summaries_summaries__get")
def get_read_summaries_summaries__get_tool():
    """Fixture for the get read_summaries_summaries__get function as string."""

    return """@self._mcp.tool()
def read_summaries_summaries__get() -> dict:
    '''
    Read Summaries

    Returns:
        dict
    '''
    import requests

    data={}
    response = requests.request('GET', f"http://localhost:8080/v1/summaries/", json=data)

    return response.json()
    """


@pytest.fixture(name="read_summary_summaries__id__get")
def get_read_summary_summaries__id__get_tool():
    """Fixture for the get read_summary_summaries__id__get function as string."""

    return """@self._mcp.tool()
def read_summary_summaries__id__get(id: int) -> dict:
    '''
    Read Summary

    Parameters:
        id (int): Id

    Returns:
        dict
    '''
    import requests

    data={'id': id}
    response = requests.request('GET', f"http://localhost:8080/v1/summaries/{id}", json=data)

    return response.json()
    """


def test_get_upsert_summary_summaries__post_operation(
    upsert_summary_summaries__post,
):
    """Test that the function template is generated correctly."""
    openapi_spec = parse("./tests/data/summary.json")
    func_template = get_function_template(
        'f"http://localhost:8080/v1/summaries/"', openapi_spec.paths[1].operations[1]
    )

    assert func_template == upsert_summary_summaries__post


def test_get_read_summaries_summaries__get_operation(
    read_summaries_summaries__get,
):
    """Test that the function template is generated correctly."""
    openapi_spec = parse("./tests/data/summary.json")
    func_template = get_function_template(
        'f"http://localhost:8080/v1/summaries/"', openapi_spec.paths[1].operations[0]
    )

    assert func_template == read_summaries_summaries__get


def test_get_read_summary_summaries__id__get_operation(
    read_summary_summaries__id__get,
):
    """Test that the function template is generated correctly."""
    openapi_spec = parse("./tests/data/summary.json")
    func_template = get_function_template(
        'f"http://localhost:8080/v1/summaries/{id}"',
        openapi_spec.paths[2].operations[0],
    )

    assert func_template == read_summary_summaries__id__get
