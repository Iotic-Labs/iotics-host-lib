# -*- coding: utf-8 -*-
# Copyright (c) 2020 Iotic Labs Ltd. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/Iotic-Labs/py-IoticBulkData/blob/master/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
{% if cookiecutter.add_example_code == "YES" %}
import base64
import json
import logging
from time import sleep
from uuid import uuid4

from iotics.host.api.qapi import QApiFactory
from iotics.host.auth import AgentAuthBuilder, AgentAuth
from iotics.host.exceptions import (
    DataSourcesConfigurationError, DataSourcesError, DataSourcesSearchTimeout,
    DataSourcesStompError, DataSourcesStompNotConnected
)
{% else %}
import logging
from uuid import uuid4

from iotics.host.api.qapi import QApiFactory
from iotics.host.auth import AgentAuthBuilder, AgentAuth
from iotics.host.exceptions import DataSourcesConfigurationError, DataSourcesError
{% endif %}
from {{cookiecutter.module_name}}.exceptions import {{cookiecutter.follower_class_name}}BaseException
from {{cookiecutter.module_name}}.conf import {{cookiecutter.follower_class_name}}Conf

logger = logging.getLogger(__name__)
# turn down stomp logging
logging.getLogger('stomp.py').setLevel(level=logging.ERROR)


def is_enabled_for_debug():
    return logger.isEnabledFor(logging.DEBUG)


class {{cookiecutter.follower_class_name}}:
{% if cookiecutter.add_example_code == "NO" %}
    def __init__(self, agent_auth: AgentAuth, qapi_factory: QApiFactory):
        # TODO: update the follower parameters
        self.search_api = qapi_factory.get_search_api()
        self.follow_api = qapi_factory.get_follow_api()
        self.agent_auth = agent_auth

    def run(self):
        logger.info('Follower started')
        # TODO: implement follower loop
{% else %}
    def __init__(self, agent_auth: AgentAuth, qapi_factory: QApiFactory, update_frequency_seconds: float):
        self.twin_api = qapi_factory.get_twin_api()
        self.search_api = qapi_factory.get_search_api()
        self.follow_api = qapi_factory.get_follow_api()
        self.agent_auth = agent_auth
        self.loop_time = update_frequency_seconds
        self.follower_twin_id = None

    def create_follower_twin(self):
        twin_id, _, _ = self.agent_auth.make_twin_id('{{cookiecutter.follower_class_name}}')
        self.twin_api.create_twin(twin_id)
        self.follower_twin_id = twin_id

    @staticmethod
    def follow_callback(header, body):  # pylint: disable=W0613
        decoded_data = base64.b64decode(body.payload.feed_data.data).decode('ascii')
        temperature = json.loads(decoded_data)
        timestamp = body.payload.feed_data.occurred_at.isoformat()

        logger.info('Received temperature data %s at time %s', temperature, timestamp)

    def follow_twins(self):
        """Find and follow twins"""
        found_twins = None
        logger.info('Searching for twins.')
        try:
            found_twins = self.search_api.search_twins(text='Random')
        except DataSourcesSearchTimeout as timeout_ex:
            logger.warning('Timed out searching for twins: %s', timeout_ex)
        except DataSourcesStompError as ex:
            logger.error('Error searching for twins: %s', ex)
        except DataSourcesStompNotConnected:
            logger.warning('Cant search for twins, stomp not currently connected')

        if not found_twins:
            logger.info('No twins found')
            return

        for twin in found_twins:
            subscription_id = None

            try:
                # follow twin's feed
                subscription_id = self.follow_api.subscribe_to_feed(
                    self.follower_twin_id, twin.id.value, 'random_temperature_feed', self.follow_callback
                )
            except DataSourcesStompNotConnected:
                logger.warning('Cant follow twin, stomp not currently connected')
                break

            if subscription_id:
                logger.info('Subscribed to feed on twin %s', twin.id.value)

    def run(self):
        logger.info('Follower started')
        self.create_follower_twin()

        while True:
            self.follow_twins()
            logger.info('Sleeping for %s seconds', self.loop_time)
            sleep(self.loop_time)
{% endif %}

def run_follower():
    """Follower entry point called by the console script declared in the setup.cfg"""

    try:
        conf = {{cookiecutter.follower_class_name}}Conf.get_conf()
        logging.basicConfig(
            format={{"'%(asctime)s %(levelname)s [%(name)s] {%(threadName)s} %(message)s'"}}, level=conf.root_log_level
        )
        agent_auth = AgentAuthBuilder.build_agent_auth(conf.auth.resolver_host, conf.auth.seed, conf.auth.user)
        qapi_factory = QApiFactory(conf, agent_auth, client_app_id=f'{{cookiecutter.module_name}}_{uuid4()}')
{% if cookiecutter.add_example_code == "NO" %}
        # TODO: update the follower instantiation
        follower = {{cookiecutter.follower_class_name}}(agent_auth, qapi_factory){% else %}
        follower = {{cookiecutter.follower_class_name}}(agent_auth, qapi_factory, conf.update_frequency_seconds){% endif %}
        follower.run()
    except {{cookiecutter.follower_class_name}}BaseException as err:
        logger.error('Follower error: %s', err, exc_info=is_enabled_for_debug())
    except DataSourcesConfigurationError as err:
        logger.error('Configuration error: %s', err, exc_info=is_enabled_for_debug())
    except DataSourcesError as err:
        logger.error('{{cookiecutter.follower_class_name}}} error: %s', err, exc_info=is_enabled_for_debug())
    except Exception as err:  # pylint: disable=W0703
        logger.error('Unexpected error: %s', err, exc_info=is_enabled_for_debug())


if __name__ == '__main__':
    run_follower()
