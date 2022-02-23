# Copyright © 2021 to 2022 IOTIC LABS LTD. info@iotics.com
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
import time

import prometheus_client

METRIC_API_CALL = prometheus_client.Histogram(
    'api_call',
    'Histogram of API calls.',
    labelnames=('module', 'function', 'failed'),
)


def measure(func, *args, **kwargs):
    start = time.monotonic()
    try:
        result = func(*args, **kwargs)
    except:  # noqa: E722
        METRIC_API_CALL.labels(
            module=func.__module__, function=func.__name__, failed=True
        ).observe(time.monotonic() - start)
        raise

    METRIC_API_CALL.labels(
        module=func.__module__, function=func.__name__, failed=False
    ).observe(time.monotonic() - start)
    return result


def add():
    """Decorator adding Prometheus metrics to the decorated function or method."""

    def inner(func):
        def wrapper(*args, **kwargs):
            return measure(func, *args, **kwargs)

        return wrapper

    return inner
