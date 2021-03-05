from uuid import uuid4

from iotic.web.rest.client.qapi import ApiClient, FetchInterestResponsePayload, InterestApi as InterestClient

from iotics.host.api.utils import check_and_retry_with_new_token, fill_refs
from iotics.host.auth import AgentAuth


class InterestApi:
    def __init__(self, rest_api_client: InterestClient, client_app_id: str, agent_auth: AgentAuth = None):
        self.rest_api_client = rest_api_client
        self.agent_auth = agent_auth
        self.client_app_id = client_app_id

    @check_and_retry_with_new_token
    @fill_refs
    def get_feed_last_stored_local(
            self, follower_twin_id: str, followed_twin_id: str, feed_id: str,
            client_ref: str = None, transaction_ref: str = None
    ) -> FetchInterestResponsePayload:
        """ Get the latest stored data from a local digital twin feed

        Args:
            follower_twin_id (str): The ID of the twin asking for the data
            followed_twin_id (str): The ID of the twin whose feed has the data
            feed_id (str): The ID of the feed from which data is sought
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char

        Returns: FetchInterestResponsePayload, with the following structure:
            followed_feed (InterestFollowedFeed):
                feed (Feed):
                    id (FeedID), with a single attribute `value`, containing the followed feed's id as a string
                    twin_id (TwinID), with a single attribute `value`, containing the followed twin's id as a string
                host_id (HostID): has attribute `value` containing a string identifying the host
            follower_twin_id (TwinID): has attribute `value` containing the followER twin's id as a string (same as
                followed twin as currently implemented)

        """
        return self.rest_api_client.fetch_last_stored_local(
            follower_twin_id=follower_twin_id,
            followed_twin_id=followed_twin_id,
            followed_feed_id=feed_id,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )

    @check_and_retry_with_new_token
    @fill_refs
    def get_feed_last_stored(
            self, host_id: str, follower_twin_id: str, followed_twin_id: str, feed_id: str,
            client_ref: str = None, transaction_ref: str = None
    ) -> FetchInterestResponsePayload:
        """ Get the latest stored data from a remote digital twin feed

        Args:
            follower_twin_id (str): The ID of the twin asking for the data
            remote_host_id (str): The ID of the host
            followed_twin_id (str): The ID of the twin whose feed has the data
            feed_id (str): The ID of the feed from which data is sought
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char

        Returns: FetchInterestResponsePayload, with the following structure:
            followed_feed (InterestFollowedFeed):
                feed (Feed):
                    id (FeedID), with a single attribute `value`, containing the followed feed's id as a string
                    twin_id (TwinID), with a single attribute `value`, containing the followed twin's id as a string
                host_id (HostID): has attribute `value` containing a string identifying the host
            follower_twin_id (TwinID): has attribute `value` containing the followER twin's id as a string (same as
                followed twin as currently implemented)

        """
        return self.rest_api_client.fetch_last_stored(
            host_id=host_id,
            follower_twin_id=follower_twin_id,
            followed_twin_id=followed_twin_id,
            followed_feed_id=feed_id,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )


def get_interest_api(config, app_id: str = None, agent_auth: AgentAuth = None) -> InterestApi:
    app_id = app_id if app_id else f'interest_api_{uuid4()}'
    return InterestApi(
        InterestClient(api_client=ApiClient(configuration=config)),
        client_app_id=app_id,
        agent_auth=agent_auth
    )
