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
from iotic.web.rest.client.qapi import Feed, FeedID, GeoLocationUpdate, TwinID, UpdateFeedResponsePayload, Visibility


class AgentAuthTest:
    # pylint: disable=R0201
    def make_twin_id(self, twin_name):
        return f'{twin_name}_twin_id', 'pk', 'doc'

    def make_twin_auth_token(self, twin_pk, twin_doc):
        return 'a token'


class TwinApiTest:
    def __init__(self, metadata=None):
        self.metadata = metadata
        self.create_calls = []
        self.meta_calls = []
        self.update_calls = []

    def create_twin(self, twin_id: str, name: str, client_ref: str = None):
        self.create_calls.append({k: v for k, v in locals().items() if k != 'self'})

    def update_twin(  # pylint:disable=too-many-arguments,too-many-locals
            self, twin_id: str, client_ref: str = None, transaction_ref: str = None,
            new_visibility: Visibility = None, location: GeoLocationUpdate = None,
            add_tags=None, del_tags=None,
            add_labels=None, del_labels=None,
            add_comments=None, del_comments=None,
            add_props=None, del_props=None,
            del_props_by_key=None, clear_all_props: bool = False
    ):
        self.update_calls.append({k: v for k, v in locals().items() if k != 'self'})


class FeedApiTest:
    def __init__(self, metadata=None):
        self.metadata = metadata
        self.create_calls = []
        self.meta_calls = []
        self.update_calls = []
        self.share_calls = []

    def create_feed(self, twin_id: str, feed_id: str, client_ref: str = None):
        self.create_calls.append({k: v for k, v in locals().items() if k != 'self'})

    def update_feed(self, twin_id: str, feed_id: str,
                    add_labels=None, del_labels=None,
                    add_comments=None, del_comments=None,
                    add_tags=None, del_tags=None,
                    add_values=None, del_values=None,
                    store_last: bool = None, client_ref: str = None) -> UpdateFeedResponsePayload:
        self.update_calls.append({k: v for k, v in locals().items() if k != 'self'})
        return UpdateFeedResponsePayload(feed=Feed(id=FeedID(value=feed_id), twin_id=TwinID(value=twin_id)))

    def update_feed_data(self, twin_id: str, feed_id: str, data: str = None, mime: str = None, occurred_at: str = None,
                         client_ref: str = None, transaction_ref: str = None):
        self.share_calls.append({k: v for k, v in locals().items() if k != 'self'})


class QApiFactoryTest:
    def __init__(self, twin_api: TwinApiTest, feed_api: FeedApiTest):
        self.feed_api = feed_api
        self.twin_api = twin_api

    def get_twin_api(self, client_app_id: str = None):
        return self.twin_api

    def get_feed_api(self, client_app_id: str = None):
        return self.feed_api
