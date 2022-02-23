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
import json

from iotic.web.rest.client.qapi import RpcStatus

from iotics.host.api.utils import get_stomp_error_message


def test_should_get_stomp_error_from_error_field():
    error_body = {
        'error': 'a stomp error',
        'details': 'some details'
    }
    stomp_error_message = get_stomp_error_message(json.dumps(error_body))
    assert stomp_error_message == error_body['error']


def test_should_get_stomp_error_from_rpc_status():
    rpc_status = RpcStatus(code=12, details='some details', message='a stomp error')
    stomp_error_message = get_stomp_error_message(json.dumps(rpc_status.to_dict()))
    assert stomp_error_message == rpc_status.message


def test_get_stomp_error_message_should_return_none_if_no_message():
    stomp_error_message = get_stomp_error_message('{}')
    assert not stomp_error_message
