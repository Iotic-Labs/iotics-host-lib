# Copyright 2022 Iotic Labs Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/Iotic-Labs/iotics-host-lib/blob/master/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import re
from os.path import join
from typing import Callable, Dict, List, Optional, Set

import requests
from iotic.web.rest.client.qapi import ApiClient
from iotics.host.testing.const import REST_EXT_API_HOST, REST_QAPI_HOST
from requests import HTTPError, Response
from retry.api import retry_call


def wait_until(condition: Callable, error_message: str = 'Not state change', tries=60, delay=0.5, **kwargs):
    def func():
        if not condition(**kwargs):
            raise ValueError(error_message)

    retry_call(func, tries=tries, delay=delay)


def drop_none_values(data: dict) -> dict:
    return {k: v for k, v in data.items() if v is not None}


def reports_cleared():
    try:
        # Clear the qapi server report and the ext api report
        resp = requests.delete(join(REST_QAPI_HOST, 'fakes/qapi'))
        resp.raise_for_status()
        resp = requests.delete(join(REST_EXT_API_HOST, 'fakes/reports'))
        resp.raise_for_status()

        # assert both reports are cleaned
        report = get_faked_qapi_report()
        ext_report = get_faked_ext_report()
        return len(report) == 2 and not ext_report.get('replies')
    except (HTTPError, KeyError):
        return False


def register_qapi_reply(path: str, reply: Optional[object] = None, error: Optional[int] = None,
                        reply_code: Optional[int] = None) -> Response:
    """
    Register a fake qapi reply
    """
    data = {'path': path,
            'reply': ApiClient().sanitize_for_serialization(reply) if reply else None,
            'error': error,
            'reply_code': reply_code}
    resp = requests.post(join(REST_QAPI_HOST, 'fakes/qapi'), json=drop_none_values(data))
    resp.raise_for_status()
    return resp.json()


def get_faked_ext_report() -> dict:
    """
    Get fake ext api server call report
    """
    resp = requests.get(join(REST_EXT_API_HOST, 'fakes'))
    resp.raise_for_status()
    return resp.json()


def get_faked_qapi_report() -> dict:
    """
    Get fake qapi server call report
    """
    resp = requests.get(join(REST_QAPI_HOST, 'fakes/qapi'))
    resp.raise_for_status()
    return resp.json()


def get_report_entries(pattern: str, report: dict) -> List[dict]:
    return [value for key, value in report.items() if re.match(pattern, key)]


def get_distinct_entries(pattern: str, method: str, report: dict) -> Set[dict]:
    return {key for key, value in report.items() if method in value and re.match(pattern, key)}


def get_ext_call_data(content_type, headers, loop, path, payload, status_code):
    data = {'path': path,
            'headers': headers,
            'payload': payload,
            'content_type': content_type,
            'loop': loop,
            'status_code': status_code}
    return drop_none_values(data)


def register_external_call_path(path: str, headers: Dict[str, str] = None, payload: str = None,
                                content_type: str = None, status_code: int = None, loop: bool = False):
    """ register a fake response to an external call. If loop == True the reply will be reused for a further call
    """
    data = get_ext_call_data(content_type, headers, loop, path, payload, status_code)
    resp = requests.post(join(REST_EXT_API_HOST, 'fakes'), json=data)
    resp.raise_for_status()
    return resp.json()


def register_external_call_rule(rule: str, headers: Dict[str, str] = None, payload: str = None,
                                content_type: str = None, status_code: int = None, loop: bool = False):
    """ register a fake response to an external call matching the provided rule.
    If loop == True the reply will be reused for a further call
    """
    data = get_ext_call_data(content_type, headers, loop, rule, payload, status_code)
    resp = requests.post(join(REST_EXT_API_HOST, 'fakes/rules'), json=data)
    resp.raise_for_status()
    return resp.json()
