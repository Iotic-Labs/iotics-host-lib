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
