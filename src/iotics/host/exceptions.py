from iotic.web.rest.client.qapi import ApiException


class DataSourcesError(Exception):
    """
    Data sources base exception
    """


class DataSourcesAuthException(DataSourcesError):
    """
    Data sources auth agent exception
    """


class DataSourcesQApiError(DataSourcesError):
    """
    Data sources QAPI exception
    """


class DataSourcesQApiHttpError(DataSourcesQApiError):
    """
    Data sources QAPI Http exception
    """

    def __init__(self, http_error: ApiException):
        super().__init__()
        self.http_error = http_error


class DataSourcesConfigurationError(DataSourcesError):
    """
    Data sources Configuration exception
    """


class DataSourcesSearchTimeout(DataSourcesError):
    """
    Search timeout exception
    """


class DataSourcesFollowTimeout(DataSourcesError):
    """
    Follow timeout exception
    """


class DataSourcesStompError(DataSourcesError):
    """
    Stomp error message received. This causes stomp to disconnect and reconnect
    """


class DataSourcesStompNotConnected(DataSourcesError):
    """
     Stomp not connected
    """
