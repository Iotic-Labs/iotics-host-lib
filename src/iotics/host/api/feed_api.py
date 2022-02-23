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
from uuid import uuid4

from iotic.web.rest.client.qapi import ApiClient, CreateFeedRequestPayload, CreateFeedResponsePayload, \
    DeleteFeedResponsePayload, DescribeFeedResponsePayload, FeedApi as FeedClient, FeedData, FeedID, \
    ListAllFeedsResponsePayload, ShareFeedDataRequestPayload, UpdateFeedRequestPayload, \
    UpdateFeedResponsePayload, Value, Values, ModelProperty, PropertyUpdate

from iotics.host import metrics
from iotics.host.api.utils import check_and_retry_with_new_token, fill_refs, ListOrTuple
from iotics.host.auth import AgentAuth


class FeedApi:
    def __init__(self, rest_api_client: FeedClient, client_app_id: str, agent_auth: AgentAuth = None):
        self.rest_api_client = rest_api_client
        self.agent_auth = agent_auth
        self.client_app_id = client_app_id

    @metrics.add()
    @check_and_retry_with_new_token
    @fill_refs
    def create_feed(
            self, twin_id: str, feed_id: str, client_ref: str = None, transaction_ref: str = None
    ) -> CreateFeedResponsePayload:
        """Create a new feed on the given twin.

        Args:
            twin_id (str): the ID of the twin providing the feed
            feed_id (str): a unique identifier for the feed, scoped per-twin
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char

        Returns: CreateFeedResponsePayload, with structure as follows:
            already_created (bool): Whether the feed existed before this request
            feed (Feed):
                id (FeedID): has sole attribute `value`, containing the feed's ID as a string
                twin_id (TwinID): has sole attribute `value`, containing the twin's ID as a string

        """
        payload = CreateFeedRequestPayload(feed_id=FeedID(value=feed_id))
        return self.rest_api_client.create_feed(
            body=payload,
            twin_id=twin_id,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )

    @metrics.add()
    @check_and_retry_with_new_token
    @fill_refs
    def list_feeds(
            self, twin_id: str, client_ref: str = None, transaction_ref: str = None
    ) -> ListAllFeedsResponsePayload:
        """List all feeds belonging to a given twin.

        Args:
            twin_id (str): the ID of the twin whose feeds you want to list
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char

        Returns: ListAllFeedsResponsePayload, whose sole attribute `feeds` is a list of Feed objects with id and twin_id

        """
        return self.rest_api_client.list_all_feeds(
            twin_id=twin_id,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )

    @metrics.add()
    @check_and_retry_with_new_token
    @fill_refs
    def delete_feed(
            self, twin_id: str, feed_id: str, client_ref: str = None, transaction_ref: str = None
    ) -> DeleteFeedResponsePayload:
        """Delete a feed, identified by its id and twin_id.

        Args:
            twin_id (str): the ID of the twin providing the feed
            feed_id (str): a unique identifier for the feed, scoped per-twin
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char

        Returns: DeleteFeedResponsePayload, with sole attribute `feed` identifying the deleted feed by id and twin_id

        """
        return self.rest_api_client.delete_feed(
            twin_id=twin_id,
            feed_id=feed_id,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )

    @metrics.add()
    @check_and_retry_with_new_token
    @fill_refs
    def describe_feed(
            self, twin_id: str, feed_id: str, client_ref: str = None, transaction_ref: str = None
    ) -> DescribeFeedResponsePayload:
        """Get metadata describing a feed.

        Args:
            twin_id (str): the ID of the twin providing the feed
            feed_id (str): a unique identifier for the feed, scoped per-twin
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char

        Returns: DescribeFeedResponsePayload, with structure as follows:
            remote_host_id (HostID): has sole attribute `value`, containing a string identifying the host the twin is on
            feed (Feed):
                id (FeedID): has sole attribute `value`, containing the feed's ID as a string
                twin_id (TwinID): has sole attribute `value`, containing the twin's ID as a string
            result (MetaResult):
                store_last (bool): Whether this feed's most recent data can be retrieved via the InterestApi
                values (list[Value]): What sort of data to expect in each feed share. Non-binding. Value structure (all
                        optional strings):
                    comment: A human-readable description of the value. Language-specific, eg "Engine oil temperature"
                    data_type: the xsd type in shorthand notation, eg "integer" or "dateTime"
                    label: the unique identifier of the value. It is language-neutral, eg "temp"
                    unit: the fully qualified ontology string URI of the unit, eg
                        http://purl.obolibrary.org/obo/UO_0000027

        """
        return self.rest_api_client.describe_feed(
            twin_id=twin_id,
            feed_id=feed_id,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )

    @metrics.add()
    @check_and_retry_with_new_token
    @fill_refs
    def describe_remote_feed(
            self, twin_id: str, feed_id: str, remote_host_id: str,
            client_ref: str = None, transaction_ref: str = None
    ) -> DescribeFeedResponsePayload:
        """Get metadata describing a remote feed.

        Args:
            twin_id (str): the ID of the twin providing the feed
            feed_id (str): a unique identifier for the feed, scoped per-twin
            remote_host_id (str): the ID of the remote host whose feed you want to describe
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char

        Returns: DescribeFeedResponsePayload, with structure as follows:
            remote_host_id (HostID): has sole attribute `value`, containing a string identifying the host the twin is on
            feed (Feed):
                id (FeedID): has sole attribute `value`, containing the feed's ID as a string
                twin_id (TwinID): has sole attribute `value`, containing the twin's ID as a string
            result (MetaResult):
                store_last (bool): Whether this feed's most recent data can be retrieved via the InterestApi
                values (list[Value]): What sort of data to expect in each feed share. Non-binding. Value structure (all
                        optional strings):
                    comment: A human-readable description of the value. Language-specific, eg "Engine oil temperature"
                    data_type: the xsd type in shorthand notation, eg "integer" or "dateTime"
                    label: the unique identifier of the value. It is language-neutral, eg "temp"
                    unit: the fully qualified ontology string URI of the unit, eg
                        http://purl.obolibrary.org/obo/UO_0000027

        """
        return self.rest_api_client.describe_remote_feed(
            twin_id=twin_id,
            feed_id=feed_id,
            host_id=remote_host_id,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )

    @metrics.add()
    @check_and_retry_with_new_token
    @fill_refs
    def update_feed(
            self, twin_id: str, feed_id: str,
            add_props: ListOrTuple[ModelProperty] = None, del_props: ListOrTuple[ModelProperty] = None,
            del_props_by_key: ListOrTuple[str] = None, clear_all_props: bool = False,
            add_values: ListOrTuple[Value] = None, del_values: ListOrTuple[str] = None,
            store_last: bool = None, client_ref: str = None, transaction_ref: str = None
    ) -> UpdateFeedResponsePayload:
        """Update the semantic description of feed, including its values.

        Args:
            twin_id (str): the ID of the twin providing the feed
            feed_id (str): a unique identifier for the feed, scoped per-twin
            add_props: (list/tuple[ModelProperty], optional): List of semantic properties to be added to the feed. Each
                property has a key (string, corresponding to the property's predicate), and one of several value types
                corresponding to the property's object: LangLiteral, StringLiteral, Literal, or Uri
            del_props: (list/tuple[ModelProperty], optional): List of semantic properties to be removed from the feed.
            del_props_by_key (list/tuple[str], optional): List of keys (predicates) for which all matching properties
                will be deleted from the twin
            clear_all_props (bool, optional): Whether to remove all non-internal properties. Defaults to False
            add_values: (list/tuple[Value], optional): List of Values, a datatype describing what sort of information to
                expect from the feed, to be added. If a Value's label appears in del_values (below) it will not be added
            del_values: (list/tuple[str], optional): Any Values with a label among these strings will be removed
            store_last (boolean, optional): whether to store the last shared value, making it available for retrieval by
                the InterestApi
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char

        Returns: UpdateFeedResponsePayload, with sole attribute `feed` identifying the updated feed by id and twin_id

        """

        payload = UpdateFeedRequestPayload(
            values=Values(added=add_values, deleted_by_label=del_values),
            store_last=store_last if store_last else None,
            properties=PropertyUpdate(
                added=add_props, deleted=del_props, cleared_all=clear_all_props, deleted_by_key=del_props_by_key
            )
        )
        return self.rest_api_client.update_feed(
            twin_id=twin_id,
            feed_id=feed_id,
            body=payload,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )

    @metrics.add()
    @check_and_retry_with_new_token
    @fill_refs
    def share_feed_data(
            self, twin_id: str, feed_id: str, data: str = None, mime: str = None, occurred_at: str = None,
            client_ref: str = None, transaction_ref: str = None
    ):
        """Share a new sample of data for the given feed. which any subscribers can receive.

        Args:
            twin_id (str): the ID of the twin providing the feed
            feed_id (str): a unique identifier for the feed, scoped per-twin
            data (str, optional): the actual set of datapoints, encoded according the the mime type. The data should
                follow the feed's value definitions but that is not enforced
            mime: (str, optional): the mime type of the encoded data.
            occurred_at (str, optional): the UTC timestamp of the sample. Typically this is either the time at which an
                application shared this sample or the time applicable to the sample itself (such as an hourly weather
                observation)
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char

        Returns: None

        """
        payload = ShareFeedDataRequestPayload(sample=FeedData(data=data, mime=mime, occurred_at=occurred_at))

        return self.rest_api_client.share_feed_data(
            twin_id=twin_id,
            feed_id=feed_id,
            body=payload,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )


def get_feed_api(config, app_id: str = None, agent_auth: AgentAuth = None) -> FeedApi:
    app_id = app_id if app_id else f'feed_api_{str(uuid4())}'
    return FeedApi(
        FeedClient(api_client=ApiClient(configuration=config)),
        client_app_id=app_id,
        agent_auth=agent_auth
    )
