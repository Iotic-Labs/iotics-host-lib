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
import random
import string
import time
from datetime import datetime, timezone
from uuid import uuid4

from iotic.web.rest.client.qapi import LangLiteral
from iotic.web.rest.client.qapi.models.value import Value
from iotics.host.api.data_types import BasicDataTypes
{% else %}
import logging
from uuid import uuid4
{% endif %}
from iotics.host.api.qapi import QApiFactory
from iotics.host.auth import AgentAuthBuilder, AgentAuth
from iotics.host.exceptions import DataSourcesConfigurationError, DataSourcesError, DataSourcesQApiError
from {{cookiecutter.module_name}}.exceptions import {{cookiecutter.publisher_class_name}}BaseException
from {{cookiecutter.module_name}}.conf import {{cookiecutter.publisher_class_name}}Conf

logger = logging.getLogger(__name__)
{% if cookiecutter.add_example_code == "YES" %}
TWIN_NAME = 'Random letter twin'
{% endif %}

def is_enabled_for_debug():
    return logger.isEnabledFor(logging.DEBUG)


class {{cookiecutter.publisher_class_name}}:
{% if cookiecutter.add_example_code == "NO" %}
    def __init__(self, agent_auth: AgentAuth, qapi_factory: QApiFactory):
        # TODO: update the publisher parameters
        self.qapi_factory = qapi_factory
        self.agent_auth = agent_auth

    def run(self):
        logger.info('Publisher started')
        # TODO: implement publisher loop
{% else %}
    def __init__(self, agent_auth: AgentAuth, qapi_factory: QApiFactory, update_frequency_seconds: float):
        self.update_frequency_seconds = update_frequency_seconds
        self.qapi_factory = qapi_factory
        self.agent_auth = agent_auth

    def _create_twin(self) -> str:
        # Create an twin id in the registerer
        twin_id, _, _ = self.agent_auth.make_twin_id(TWIN_NAME)

        # Create the twin
        api = self.qapi_factory.get_twin_api()
        api.create_twin(twin_id)
        return twin_id

    def _set_twin_meta(self, twin_id: str):
        label = 'Random awesome twin'
        description = 'Awesome twin for random data'
        api = self.qapi_factory.get_twin_api()
        api.update_twin(
            twin_id,
            add_tags=['random', 'awesome'],
            add_labels=[LangLiteral(value=label, lang='en')],
            add_comments=[LangLiteral(value=description, lang='en')]
        )

    def _create_feed(self, twin_id: str) -> str:
        api = self.qapi_factory.get_feed_api()
        feed_name = 'random_letter_feed'
        api.create_feed(twin_id, feed_name)
        return feed_name

    def _set_feed_meta(self, twin_id: str, feed_name: str):
        label = 'Random letter feed'
        description = f'Awesome feed generating a letter each {self.update_frequency_seconds} seconds'
        api = self.qapi_factory.get_feed_api()

        api.update_feed(
            twin_id, feed_name,
            add_labels=[LangLiteral(value=label, lang='en')],
            add_comments=[LangLiteral(value=description, lang='en')],
            store_last=True,
            add_tags=['random', 'awesome'],
            add_values=[
                Value(label='letter', data_type=BasicDataTypes.STRING.value, comment='a random letter'),
            ]
        )

    def _share_feed_data(self, twin_id: str, feed_name: str):
        non_encoded_data = {
            'letter': random.choice(string.ascii_letters)
        }
        json_data = json.dumps(non_encoded_data)
        try:
            base64_encoded_data = base64.b64encode(json_data.encode()).decode()
        except TypeError as err:
            raise RandomLetPublisherBaseException(
                f'Can not encode data to share from {twin_id}/{feed_name}: {err}, {json_data}'
            ) from err

        api = self.qapi_factory.get_feed_api()
        api.share_feed_data(
            twin_id, feed_name,
            data=base64_encoded_data, mime='application/json',
            occurred_at=datetime.now(tz=timezone.utc).isoformat()
        )

        return non_encoded_data

    def setup(self):
        """Create an twin and set its metadata. Create a feed an set its metadata."""

        logger.info('Publisher setup')
        twin_id = self._create_twin()
        self._set_twin_meta(twin_id)

        feed_name = self._create_feed(twin_id)
        self._set_feed_meta(twin_id, feed_name)

        return twin_id, feed_name

    def publish(self, twin_id: str, feed_name: str):
        """Publish a new random letter."""

        try:
            non_encoded_data = self._share_feed_data(twin_id, feed_name)
        except DataSourcesQApiError as err:
            logger.error('Publishing QAPI error: %s', err, exc_info=is_enabled_for_debug())
        else:
            logger.info('Published %s', non_encoded_data)

    def run(self):
        logger.info('Publisher started')
        twin_id, feed_name = self.setup()
        while True:
            self.publish(twin_id, feed_name)
            logger.info('End of loop, will sleep for %s seconds', self.update_frequency_seconds)
            time.sleep(self.update_frequency_seconds)
{% endif %}

def run_publisher():
    """Publisher entry point called by the console script declared in the setup.cfg."""

    try:
        conf = {{cookiecutter.publisher_class_name}}Conf.get_conf()
        logging.basicConfig(
            format={{"'%(asctime)s %(levelname)s [%(name)s] {%(threadName)s} %(message)s'"}}, level=conf.root_log_level
        )
        agent_auth = AgentAuthBuilder.build_agent_auth(conf.auth.resolver_host, conf.auth.seed, conf.auth.user)
        qapi_factory = QApiFactory(conf, agent_auth, client_app_id=f'{{cookiecutter.module_name}}_{uuid4()}')
{% if cookiecutter.add_example_code == "NO" %}
        # TODO: update the publisher instantiation
        publisher = {{cookiecutter.publisher_class_name}}(agent_auth, qapi_factory){% else %}
        publisher = {{cookiecutter.publisher_class_name}}(agent_auth, qapi_factory, conf.update_frequency_seconds){% endif %}
        publisher.run()
    except {{cookiecutter.publisher_class_name}}BaseException as err:
        logger.error('Publisher error: %s', err, exc_info=is_enabled_for_debug())
    except DataSourcesConfigurationError as err:
        logger.error('Configuration error: %s', err, exc_info=is_enabled_for_debug())
    except DataSourcesError as err:
        logger.error('{{cookiecutter.publisher_class_name}}} error: %s', err, exc_info=is_enabled_for_debug())
    except Exception as err:  # pylint: disable=W0703
        logger.error('Unexpected error: %s', err, exc_info=is_enabled_for_debug())


if __name__ == '__main__':
    run_publisher()
