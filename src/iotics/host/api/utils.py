from collections import namedtuple
import contextlib
from functools import wraps
from http import HTTPStatus
from typing import List, T, Tuple, Union

from shortuuid import uuid
from iotic.web.rest.client.qapi import ApiClient, ApiException
from iotics.host.exceptions import DataSourcesQApiError, DataSourcesQApiHttpError


ListOrTuple = Union[List[T], Tuple[T, ...]]


@contextlib.contextmanager
def check_call():
    try:
        yield
    except ApiException as err:
        raise DataSourcesQApiHttpError(err) from err
    except Exception as err:  # pylint: disable=W0703
        raise DataSourcesQApiError(err) from err


def check_and_retry_with_new_token(func):
    """A decorator function that allows methods of the FeedApi and TwinApi classes, which use the REST QApi, to get
    a new token and try again if the first attempt returns a 401 error"""
    @check_call()
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ApiException as ex:
            if ex.status == HTTPStatus.UNAUTHORIZED and self.agent_auth is not None:
                new_token = self.agent_auth.make_agent_auth_token()
                self.rest_api_client.api_client.configuration.access_token = new_token
                return func(self, *args, **kwargs)
            raise ex
    return wrapper


def fill_refs(func):
    """Provide random values for the client and transaction ref header for a request if none was specified"""
    @wraps(func)
    def wrapper(*args, client_ref: str = None, transaction_ref: str = None, **kwargs):
        ref = str(uuid())
        client_ref = client_ref or f'cref-{ref}'
        transaction_ref = transaction_ref or f'txref-{ref}'
        return func(*args, client_ref=client_ref, transaction_ref=transaction_ref, **kwargs)
    return wrapper


_API_CLIENT = ApiClient()
Resp = namedtuple('Resp', 'data')


# These ought to be class methods and there is no reason to initialize multiple ApiClient instances to handle them
def deserialize(body, response_type):
    return _API_CLIENT.deserialize(Resp(body), response_type)


def sanitize_for_serialization(payload):
    return _API_CLIENT.sanitize_for_serialization(payload)
