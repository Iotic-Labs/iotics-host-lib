from uuid import uuid4

from iotic.web.rest.client.qapi import ApiClient, CommentUpdate, CreateTwinRequestPayload, CreateTwinResponsePayload, \
    DeleteTwinResponsePayload, DescribeTwinResponsePayload, GeoLocationUpdate, LabelUpdate, LangLiteral, \
    ListAllTwinsResponsePayload, ModelProperty, PropertyUpdate, Tags, TwinApi as TwinClient, TwinID, \
    UpdateTwinRequestPayload, UpdateTwinResponsePayload, Visibility, VisibilityUpdate

from iotics.host.api.utils import check_and_retry_with_new_token, fill_refs, ListOrTuple
from iotics.host.auth import AgentAuth


class TwinApi:
    def __init__(self, rest_api_client: TwinClient, client_app_id: str, agent_auth: AgentAuth = None):
        self.client_app_id = client_app_id
        self.rest_api_client = rest_api_client
        self.agent_auth = agent_auth

    @check_and_retry_with_new_token
    @fill_refs
    def create_twin(
            self, twin_id: str, client_ref: str = None, transaction_ref: str = None
    ) -> CreateTwinResponsePayload:
        """Create a digital twin in Iotic space.

        Args:
            twin_id (str): the ID of the twin to be created (unique, in DID format)
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char


        Returns: CreateTwinResponsePayload, with structure as follows:
            already_created (bool): Whether the feed existed before this request
            twin (Twin):
                id (TwinID): has sole attribute `value`, containing the twin's ID as a string
                visibility (Visibility): Either PRIVATE (visible in a LOCAL scope), or PUBLIC (visible in any scope)

        """
        payload = CreateTwinRequestPayload(twin_id=TwinID(value=twin_id))
        return self.rest_api_client.create_twin(
            body=payload,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )

    @check_and_retry_with_new_token
    @fill_refs
    def list_twins(self, client_ref: str = None, transaction_ref: str = None) -> ListAllTwinsResponsePayload:
        """List all twins visible to this agent, up to the default limit of 500 (API allows max limit of 1000 and
        offsets to be specified for pagination, but these parameters are not exposed!)

        Args:
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char

        Returns: ListAllTwinsResponsePayload, whose sole attribute `twins` is a list of Twin objects containing id and
            visibility

        """
        return self.rest_api_client.list_all_twins(
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )

    @check_and_retry_with_new_token
    @fill_refs
    def delete_twin(
            self, twin_id: str, client_ref: str = None, transaction_ref: str = None
    ) -> DeleteTwinResponsePayload:
        """Delete the specified twin from Iotic space. (Idempotent -- will not fail if twin does not exist)

        Args:
            twin_id (str): ID of the twin to delete.
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char

        Returns: DeleteTwinResponsePayload, whose sole attribute `twin` has the deleted twin's id and visibility

        """
        return self.rest_api_client.delete_twin(
            twin_id=twin_id,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )

    @check_and_retry_with_new_token
    @fill_refs
    def describe_twin(
            self, twin_id: str, client_ref: str = None, transaction_ref: str = None
    ) -> DescribeTwinResponsePayload:
        """Get metadata describing a twin.

        Args:
            twin_id (str): ID of the twin to update.
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char

        Returns: DescribeTwinResponsePayload, a deeply nested structure with attributes as below:
            remote_host_id (HostID): has attribute `value` containing a string identifying the host
            twin (Twin): has id and visibility attributes, as in other payloads
            result (TwinMetaResult):
                comments (list[LangLiteral]): all the comments on the twin, max one per language. LangLiteral structure:
                    lang (str): 2-character language code
                    value (str): the text content of the comment
                labels (list[LangLiteral]): all the labels on the twin, max one per language
                location (GeoLocation) - The coordinates on Earth of the non-digital twin:
                    lat (float): Latitude
                    lon (float): Longitude
                properties (list[ModelProperty]): The semantic properties added to the twin. ModelProperty structure:
                    key (str): The predicate of the property. Then, one of the following value (object) types:
                    lang_literal_value (LangLiteral): A string w/ language, see "comments" above for structure
                    literal_value (Literal) - Describes a non-string typed value:
                        data_type (str): short-form xsd type, eg 'integer', 'boolean'
                        value (str): Content of the value as a string
                    string_literal_value (StringLiteral): Describes a string w/o language. One attribute, `value` (str)
                    uri_value (Uri): One attribute, `value`, a string representing a URI
                tags (list[str]): Any tags that have been added to the twin
                feeds (list[FeedMeta]): Each FeedMeta has attributes below:
                    labels (list[LangLiteral]): as above in TwinMetaResult, or below in update_twin
                    store_last (bool): whether you can access the last data shared to this feed via the InterestApi
                    feed_id (FeedID): The id of the feed, whose string value is stored in a `value` attribute

        """
        return self.rest_api_client.describe_twin(
            twin_id=twin_id,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )

    @check_and_retry_with_new_token
    @fill_refs
    def describe_remote_twin(
            self, twin_id: str, remote_host_id: str, client_ref: str = None, transaction_ref: str = None
    ) -> DescribeTwinResponsePayload:
        """Get metadata describing a remote twin.

        Args:
            twin_id (str): ID of the twin to update.
            remote_host_id (str): the ID of the remote host whose twin you want to describe
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char

        Returns: DescribeTwinResponsePayload, a deeply nested structure with attributes as below:
            remote_host_id (HostID): has attribute `value` containing a string identifying the host
            twin (Twin): has id and visibility attributes, as in other payloads
            result (TwinMetaResult):
                comments (list[LangLiteral]): all the comments on the twin, max one per language. LangLiteral structure:
                    lang (str): 2-character language code
                    value (str): the text content of the comment
                labels (list[LangLiteral]): all the labels on the twin, max one per language
                location (GeoLocation) - The coordinates on Earth of the non-digital twin:
                    lat (float): Latitude
                    lon (float): Longitude
                properties (list[ModelProperty]): The semantic properties added to the twin. ModelProperty structure:
                    key (str): The predicate of the property. Then, one of the following value (object) types:
                    lang_literal_value (LangLiteral): A string w/ language, see "comments" above for structure
                    literal_value (Literal) - Describes a non-string typed value:
                        data_type (str): short-form xsd type, eg 'integer', 'boolean'
                        value (str): Content of the value as a string
                    string_literal_value (StringLiteral): Describes a string w/o language. One attribute, `value` (str)
                    uri_value (Uri): One attribute, `value`, a string representing a URI
                tags (list[str]): Any tags that have been added to the twin
                feeds (list[FeedMeta]): Each FeedMeta has attributes below:
                    labels (list[LangLiteral]): as above in TwinMetaResult, or below in update_twin
                    store_last (bool): whether you can access the last data shared to this feed via the InterestApi
                    feed_id (FeedID): The id of the feed, whose string value is stored in a `value` attribute

        """
        return self.rest_api_client.describe_remote_twin(
            twin_id=twin_id,
            host_id=remote_host_id,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )

    @check_and_retry_with_new_token
    @fill_refs
    def update_twin(  # pylint:disable=too-many-arguments,too-many-locals
            self, twin_id: str, client_ref: str = None, transaction_ref: str = None,
            new_visibility: Visibility = None, location: GeoLocationUpdate = None,
            add_tags: ListOrTuple[str] = None, del_tags: ListOrTuple[str] = None,
            add_labels: ListOrTuple[LangLiteral] = None, del_labels: ListOrTuple[str] = None,
            add_comments: ListOrTuple[LangLiteral] = None, del_comments: ListOrTuple[str] = None,
            add_props: ListOrTuple[ModelProperty] = None, del_props: ListOrTuple[ModelProperty] = None,
            del_props_by_key: ListOrTuple[str] = None, clear_all_props: bool = False
    ) -> UpdateTwinResponsePayload:
        """Update the metadata describing a twin.

        Args:
            twin_id (str): ID of the twin to update
            client_ref (str, optional): to be deprecated, must be unique for each request
            transaction_ref (str, optional): Used to loosely link requests/responses in a distributed env't. Max 36 char
            new_visibility (Visibility, optional): Can either be PRIVATE (visible in a LOCAL scope), or PUBLIC (visible
                in any scope)
            location (GeoLocationUpdate, optional): Where on earth (lat/lon) the non-digital twin is located
                e.g. GeoLocationUpdate(location=GeoLocation(lat=10, lon=10))
            add_tags: (list/tuple[str], optional): List of tags to be added
            del_tags: (list/tuple[str], optional): List of tags to be deleted
            add_labels (list/tuple[LangLiteral], optional): List of labels to be added. Only one label per language is
                stored, i.e. any existing ones with the same language will be replaced
            del_labels (list/tuple[str], optional): List of languages for which languages should be removed
            add_comments (list/tuple[LangLiteral], optional): List of comments to be added. Same language caveat as for
                labels.
            del_comments: (list/tuple[str], optional): List of languages for which comments should be deleted
            add_props: (list/tuple[ModelProperty], optional): List of semantic properties to be added to the twin. Each
                property has a key (string, corresponding to the property's predicate), and one of several value types
                corresponding to the property's object: LangLiteral, StringLiteral, Literal, or Uri
            del_props: (list/tuple[ModelProperty], optional): List of semantic properties to be removed from the twin.
            del_props_by_key (list/tuple[str], optional): List of keys (predicates) for which all matching properties
                will be deleted from the twin
            clear_all_props (bool, optional): Whether to remove all non-internal properties. Defaults to False

        Returns: UpdateTwinResponsePayload, whose sole attribute `twin` has the deleted twin's id and visibility

        """
        payload = UpdateTwinRequestPayload(
            new_visibility=VisibilityUpdate(visibility=new_visibility) if new_visibility else None,
            location=location or None,
            labels=LabelUpdate(added=add_labels, deleted_by_lang=del_labels),
            comments=CommentUpdate(added=add_comments, deleted_by_lang=del_comments),
            tags=Tags(added=add_tags, deleted=del_tags),
            properties=PropertyUpdate(
                added=add_props, deleted=del_props, cleared_all=clear_all_props, deleted_by_key=del_props_by_key
            )
        )
        return self.rest_api_client.update_twin(
            twin_id=twin_id,
            body=payload,
            iotics_client_app_id=self.client_app_id,
            iotics_client_ref=client_ref,
            iotics_transaction_ref=transaction_ref
        )


def get_twin_api(config, app_id: str = None, agent_auth: AgentAuth = None) -> TwinApi:
    app_id = app_id if app_id else f'twin_api_{str(uuid4())}'
    return TwinApi(
        TwinClient(api_client=ApiClient(configuration=config)), client_app_id=app_id, agent_auth=agent_auth
    )
