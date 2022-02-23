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
from iotic.web.rest.client.qapi import Configuration

from iotics.host.api.twin_api import get_twin_api, TwinApi
from iotics.host.api.feed_api import get_feed_api, FeedApi
from iotics.host.api.search_api import get_search_api, SearchAPI
from iotics.host.api.follow_api import get_follow_api, FollowAPI
from iotics.host.api.interest_api import get_interest_api, InterestApi

from iotics.host.auth import AgentAuth
from iotics.host.conf.base import DataSourcesConfBase


class QApiFactory:

    def __init__(
            self, config: DataSourcesConfBase, agent_auth: AgentAuth, client_app_id: str = None,
    ):
        self.client_app_id = client_app_id
        self.agent_auth = agent_auth
        self.config = config

    def get_twin_api(self, client_app_id: str = None) -> TwinApi:
        """Get a TwinApi instance for creating and managing digital twins

        Args:
            client_app_id (str): header to be added to all requests made with this API, providing a namespace for the
            application within which all the requests/responses are grouped

        Returns: TwinApi

        """
        token = self.agent_auth.make_agent_auth_token()
        config = self.get_rest_config(self.config, token)
        return get_twin_api(config, client_app_id or self.client_app_id, self.agent_auth)

    def get_feed_api(self, client_app_id: str = None) -> FeedApi:
        """Get a FeedApi instance for creating and managing the feeds provided by twins

        Args:
            client_app_id (str): header to be added to all requests made with this API, providing a namespace for the
            application within which all the requests/responses are grouped

        Returns: FeedApi

        """
        token = self.agent_auth.make_agent_auth_token()
        config = self.get_rest_config(self.config, token)
        return get_feed_api(config, client_app_id or self.client_app_id, self.agent_auth)

    def get_interest_api(self, client_app_id: str = None) -> InterestApi:
        """Get an InstanceApi instance for getting the most recently shared data from feeds which allow this

        Args:
            client_app_id (str): header to be added to all requests made with this API, providing a namespace for the
            application within which all the requests/responses are grouped

        Returns: InterestApi

        """
        token = self.agent_auth.make_agent_auth_token()
        config = self.get_rest_config(self.config, token)
        return get_interest_api(config, client_app_id or self.client_app_id, self.agent_auth)

    def get_search_api(self, client_app_id: str = None) -> SearchAPI:
        """Get a SearchApi instance for searching Iotic space for twins which match various criteria

        Args:
            client_app_id (str): header to be added to all requests made with this API, providing a namespace for the
            application within which all the requests/responses are grouped

        Returns: SearchApi

        """
        return get_search_api(self.config, self.agent_auth, client_app_id or self.client_app_id, )

    def get_follow_api(self, client_app_id: str = None) -> FollowAPI:
        """Get a FollowApi instance for subscribing to feeds and receiving their data as it is shared

        Args:
            client_app_id (str): header to be added to all requests made with this API, providing a namespace for the
            application within which all the requests/responses are grouped

        Returns: FollowApi

        """
        return get_follow_api(self.config, self.agent_auth, client_app_id or self.client_app_id)

    def get_rest_config(self, config: DataSourcesConfBase, access_token: str = None) -> Configuration:
        """Get a Configuration instance required by the ApiClient class wrapped by the REST Apis (TwinApi, FeedApi and
        InterestApi)

        Args:
            config (DataSourcesConfBase): Pydantic config model to be converted
            access_token (str): An auth token to be added to the config

        Returns: Configuration

        """
        config = Configuration(host=config.qapi_url)
        config.access_token = access_token
        config.verify_ssl = self.config.verify_ssl
        return config
