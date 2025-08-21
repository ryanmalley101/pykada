from typeguard import typechecked
from typing import Dict, Any, List

from pykada.helpers import require_non_empty_str
from pykada.endpoints import HELIX_EVENT_TYPE_ENDPOINT, HELIX_EVENT_ENDPOINT, \
    HELIX_SEARCH_ENDPOINT
from pykada.verkada_client import BaseClient
from pykada.verkada_requests import *

class HelixClient(BaseClient):
    """
    Client for interacting with Verkada's Classic Alarms API.
    This client provides methods to retrieve alarm devices and site information.
    """

    @typechecked
    def __init__(self,
                 api_key: Optional[str] = None,
                 token_manager: Optional[VerkadaTokenManager] = None):
        super().__init__(api_key, token_manager)

    @typechecked
    def create_helix_event_type(self, event_schema: Dict[str, str], name: str) -> Dict[
        str, Any]:
        """
        Create a new Helix Event Type.

        :param event_schema: A dictionary defining the event schema (e.g., {"item": "string", "price": "float"}).
                             Maximum number of attributes is 10; each attribute name and type must be non-empty and within length limits.
        :param name: The unique name for the Helix event type.
        :return: JSON response containing the created event type info (including its UID).
        :raises ValueError: If name is empty or event_schema is not valid.
        """
        require_non_empty_str(name, "name")
        if not isinstance(event_schema, dict) or not event_schema:
            raise ValueError("event_schema must be a non-empty dictionary")
        if len(event_schema) > 10:
            raise ValueError(
                "The maximum number of attributes per Event Type is 10")
        for key, value in event_schema.items():
            require_non_empty_str(key, "attribute name")
            require_non_empty_str(value, "attribute type")
            if len(key) > 20 or len(value) > 20:
                raise ValueError(
                    "Each attribute name and type must be at most 20 characters long")

        payload = {
            "event_schema": event_schema,
            "name": name
        }
        return self.request_manager.post(HELIX_EVENT_TYPE_ENDPOINT, payload=payload)


    @typechecked
    def get_helix_event_types(
        self,
        event_type_uid: Optional[str] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve a list of Helix Event Types from the organization.

        This method returns all Helix Event Types along with their associated names and schemas.
        You can optionally narrow down the results by specifying either an event type UID or an event type name.

        :param event_type_uid: (Optional) The unique identifier of the event type to filter by.
        :param name: (Optional) The name of the event type to filter by.
        :return: JSON response containing Helix Event Types.
        :raises ValueError: If event_type_uid or name is provided as an empty string.
        """
        params: Dict[str, Any] = {}
        if event_type_uid is not None:
            require_non_empty_str(event_type_uid, "event_type_uid")
            params["event_type_uid"] = event_type_uid
        if name is not None:
            require_non_empty_str(name, "name")
            params["name"] = name

        return self.request_manager.get(HELIX_EVENT_TYPE_ENDPOINT, params=params)


    @typechecked
    def update_helix_event_type(self,
                                event_type_uid: str, event_schema: Dict[str, str],
                                name: str) -> Dict[str, Any]:
        """
        Update an existing Helix Event Type.

        :param event_type_uid: The unique identifier of the Helix Event Type.
        :param event_schema: A dictionary representing the updated event schema.
        :param name: The updated name for the event type.
        :return: JSON response containing the updated event type information.
        :raises ValueError: If any required parameter is missing or invalid.
        """
        require_non_empty_str(event_type_uid, "event_type_uid")
        require_non_empty_str(name, "name")
        if not isinstance(event_schema, dict) or not event_schema:
            raise ValueError("event_schema must be a non-empty dictionary")

        payload = {"event_schema": event_schema, "name": name}
        params = {"event_type_uid": event_type_uid}
        return self.request_manager.patch(HELIX_EVENT_TYPE_ENDPOINT, params=params,
                             payload=payload)


    @typechecked
    def delete_helix_event_type(self,event_type_uid: str) -> Dict[str, Any]:
        """
        Delete a Helix Event Type from Command.

        :param event_type_uid: The unique identifier of the Helix Event Type to delete.
        :return: JSON response confirming deletion of the event type.
        :raises ValueError: If event_type_uid is empty.
        """
        require_non_empty_str(event_type_uid, "event_type_uid")
        params = {"event_type_uid": event_type_uid}
        return self.request_manager.delete(HELIX_EVENT_TYPE_ENDPOINT, params=params)


    # ---------------------------
    # Helix Event CRUD
    # ---------------------------

    @typechecked
    def create_helix_event(
            self,
            camera_id: str,
            event_type_uid: str,
            time_ms: int,
            flagged: Optional[bool] = False,
            attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Helix Event in Command.

        This method generates a Helix Event by sending a POST request to the Verkada API.
        Required attributes for the event include:
          - camera_id: The unique identifier of the camera.
          - event_type_uid: The unique identifier of the Helix Event Type.
          - time_ms: The event epoch time in milliseconds.

        The 'flagged' attribute is optional and defaults to False. In addition, users can supply any
        extra attributes (that adhere to the pre-defined event schema) via the extra_attributes parameter.
        Attributes not provided are simply omitted from the request.

        :param camera_id: The unique identifier of the camera.
        :param event_type_uid: The unique identifier of the Helix Event Type.
        :param time_ms: The event epoch time in milliseconds.
        :param flagged: Boolean indicating whether the event is flagged (defaults to False).
        :param attributes: Optional dictionary of additional attribute values.
        :return: JSON response containing the created Helix Event details.
        :raises ValueError: If camera_id or event_type_uid is an empty string, or if time_ms is not a positive integer.
        """
        require_non_empty_str(camera_id, "camera_id")
        require_non_empty_str(event_type_uid, "event_type_uid")
        if not isinstance(time_ms, int) or time_ms <= 0:
            raise ValueError(
                "time_ms must be a positive integer representing the event "
                "epoch time in milliseconds")

        payload = {
            "camera_id": camera_id,
            "event_type_uid": event_type_uid,
            "time_ms": time_ms,
            "flagged": flagged,
            "attributes": attributes
        }

        return self.request_manager.post(HELIX_EVENT_ENDPOINT, payload=payload)


    @typechecked
    def get_helix_event(self,
                        camera_id: str,
                        time_ms: int,
                        event_type_uid: str) -> Dict[
        str, Any]:
        """
        Retrieve a Helix Event.

        :param camera_id: The unique identifier of the camera.
        :param time_ms: The event time as a Unix timestamp in milliseconds.
        :param event_type_uid: The UID of the Helix Event Type.
        :return: JSON response containing the event details.
        :raises ValueError: If any required parameter is missing or invalid.
        """
        require_non_empty_str(camera_id, "camera_id")
        require_non_empty_str(event_type_uid, "event_type_uid")
        if not isinstance(time_ms, int) or time_ms <= 0:
            raise ValueError("time_ms must be a positive integer")

        params = {
            "camera_id": camera_id,
            "time_ms": time_ms,
            "event_type_uid": event_type_uid
        }
        return self.request_manager.get(HELIX_EVENT_ENDPOINT, params=params)


    @typechecked
    def update_helix_event(
            self,
            camera_id: str,
            time_ms: int,
            event_type_uid: str,
            flagged: bool,
            extra_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing Helix Event in Command.

        This method updates an already-posted Helix Event. To perform the update,
        you must supply the following query parameters:
          - camera_id: The unique identifier of the camera.
          - time_ms: The event epoch time in milliseconds.
          - event_type_uid: The unique identifier of the event type.

        In the request body, an "attributes" object is provided, which must include the
        required "flagged" boolean parameter. Additional attribute updates can be supplied
        via the extra_attributes parameter.

        :param camera_id: The unique identifier of the camera.
        :param time_ms: The event epoch time in milliseconds (must be a positive integer).
        :param event_type_uid: The unique identifier of the Helix Event Type.
        :param flagged: Boolean indicating whether the event is flagged.
        :param extra_attributes: Optional dictionary of additional attribute key-value pairs to update.
        :return: JSON response containing the updated Helix Event details.
        :raises ValueError: If camera_id or event_type_uid is an empty string, or if time_ms is not positive.
        """
        require_non_empty_str(camera_id, "camera_id")
        require_non_empty_str(event_type_uid, "event_type_uid")
        if not isinstance(time_ms, int) or time_ms <= 0:
            raise ValueError(
                "time_ms must be a positive integer representing the event epoch time in milliseconds")

        attributes: Dict[str, Any] = {}
        if extra_attributes:
            attributes.update(extra_attributes)

        params = {
            "camera_id": camera_id,
            "time_ms": time_ms,
            "event_type_uid": event_type_uid
        }
        payload = {"attributes": attributes, "flagged": flagged}

        return self.request_manager.patch(HELIX_EVENT_ENDPOINT, params=params, payload=payload)


    @typechecked
    def delete_helix_event(self, camera_id: str, time_ms: int, event_type_uid: str) -> \
    Dict[str, Any]:
        """
        Delete a Helix Event from Command.

        :param camera_id: The unique identifier of the camera.
        :param time_ms: The event time as a Unix timestamp in milliseconds.
        :param event_type_uid: The UID of the Helix Event Type.
        :return: JSON response confirming deletion of the event.
        :raises ValueError: If any required parameter is missing or invalid.
        """
        require_non_empty_str(camera_id, "camera_id")
        require_non_empty_str(event_type_uid, "event_type_uid")
        if not isinstance(time_ms, int) or time_ms <= 0:
            raise ValueError("time_ms must be a positive integer")

        params = {"camera_id": camera_id, "time_ms": time_ms,
                  "event_type_uid": event_type_uid}
        return self.request_manager.delete(HELIX_EVENT_ENDPOINT, params=params)


    @typechecked
    def search_helix_events(
            self,
            camera_ids: List[str],
            end_time_ms: int,
            event_type_uid: str,
            flagged: bool,
            keywords: List[str],
            start_time_ms: int,
            attribute_filters: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Search for Helix Events in Command.

        This function sends a POST request to search for one or more Helix Events
            that have already been posted
        to Command. It requires that the API token (provided via headers)
            has Helix permissions.

        The search is refined by specifying:
          - camera_ids: A list of unique camera IDs.
          - end_time_ms: The query end epoch time in milliseconds.
          - event_type_uid: The unique identifier of the event type.
          - flagged: A boolean indicating whether to filter for flagged events.
          - keywords: A list of search keywords.
          - start_time_ms: The query start epoch time in milliseconds.

        :param attribute_filters: Optional list of additional filter objects.
        :param camera_ids: List of unique camera IDs (must be non-empty).
        :param end_time_ms: Query end epoch time in milliseconds (must be positive).
        :param event_type_uid: Unique identifier of the event type
            (non-empty string).
        :param flagged: Boolean indicating whether to filter for flagged events.
        :param keywords: List of search keywords (each must be non-empty).
        :param start_time_ms: Query start epoch time in milliseconds
            (must be positive and <= end_time_ms).
        :return: JSON response containing the search results.
        :raises ValueError: If any required parameter is missing or invalid.
        """
        # Validate camera_ids: must be non-empty list of non-empty strings.
        if not camera_ids:
            raise ValueError("camera_ids must be a non-empty list of strings")
        for idx, cam_id in enumerate(camera_ids):
            require_non_empty_str(cam_id, f"camera_ids[{idx}]")

        # Validate event_type_uid.
        require_non_empty_str(event_type_uid, "event_type_uid")

        # Validate time range.
        if not isinstance(start_time_ms, int) or start_time_ms <= 0:
            raise ValueError("start_time_ms must be a positive integer")
        if not isinstance(end_time_ms, int) or end_time_ms <= 0:
            raise ValueError("end_time_ms must be a positive integer")
        if start_time_ms > end_time_ms:
            raise ValueError(
                "start_time_ms must be less than or equal to end_time_ms")

        # Validate keywords: must be a list of non-empty strings.
        if not isinstance(keywords, list):
            raise ValueError("keywords must be a list")
        for idx, keyword in enumerate(keywords):
            require_non_empty_str(keyword, f"keywords[{idx}]")

        # Construct the base filter object from the required parameters.
        base_filter = {
            "camera_ids": camera_ids,
            "end_time_ms": end_time_ms,
            "event_type_uid": event_type_uid,
            "flagged": flagged,
            "keywords": keywords,
            "start_time_ms": start_time_ms
        }

        # Combine with any additional filters if provided.
        filters = [base_filter]
        if attribute_filters is not None:
            filters.extend(attribute_filters)

        payload = {"attribute_filters": filters}
        return self.request_manager.post(HELIX_SEARCH_ENDPOINT, payload=payload)


@typechecked
def create_helix_event(camera_id: str, event_type_uid: str, time_ms: int, flagged: Optional[bool] = False, attributes: Optional[Dict[str, Any]] = None):
    """
    Create a Helix Event in Command.

    This method generates a Helix Event by sending a POST request to the Verkada API.
    Required attributes for the event include:
      - camera_id: The unique identifier of the camera.
      - event_type_uid: The unique identifier of the Helix Event Type.
      - time_ms: The event epoch time in milliseconds.

    The 'flagged' attribute is optional and defaults to False. In addition, users can supply any
    extra attributes (that adhere to the pre-defined event schema) via the extra_attributes parameter.
    Attributes not provided are simply omitted from the request.

    :param camera_id: The unique identifier of the camera.
    :param event_type_uid: The unique identifier of the Helix Event Type.
    :param time_ms: The event epoch time in milliseconds.
    :param flagged: Boolean indicating whether the event is flagged (defaults to False).
    :param attributes: Optional dictionary of additional attribute values.
    :return: JSON response containing the created Helix Event details.
    :raises ValueError: If camera_id or event_type_uid is an empty string, or if time_ms is not a positive integer.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the HelixClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a HelixClient object directly for better performance.
    """
    return HelixClient().create_helix_event(camera_id, event_type_uid, time_ms, flagged, attributes)

@typechecked
def create_helix_event_type(event_schema: Dict[str, str], name: str):
    """
    Create a new Helix Event Type.

    :param event_schema: A dictionary defining the event schema (e.g., {"item": "string", "price": "float"}).
                         Maximum number of attributes is 10; each attribute name and type must be non-empty and within length limits.
    :param name: The unique name for the Helix event type.
    :return: JSON response containing the created event type info (including its UID).
    :raises ValueError: If name is empty or event_schema is not valid.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the HelixClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a HelixClient object directly for better performance.
    """
    return HelixClient().create_helix_event_type(event_schema, name)

@typechecked
def delete_helix_event(camera_id: str, time_ms: int, event_type_uid: str):
    """
    Delete a Helix Event from Command.

    :param camera_id: The unique identifier of the camera.
    :param time_ms: The event time as a Unix timestamp in milliseconds.
    :param event_type_uid: The UID of the Helix Event Type.
    :return: JSON response confirming deletion of the event.
    :raises ValueError: If any required parameter is missing or invalid.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the HelixClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a HelixClient object directly for better performance.
    """
    return HelixClient().delete_helix_event(camera_id, time_ms, event_type_uid)

@typechecked
def delete_helix_event_type(event_type_uid: str):
    """
    Delete a Helix Event Type from Command.

    :param event_type_uid: The unique identifier of the Helix Event Type to delete.
    :return: JSON response confirming deletion of the event type.
    :raises ValueError: If event_type_uid is empty.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the HelixClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a HelixClient object directly for better performance.
    """
    return HelixClient().delete_helix_event_type(event_type_uid)

@typechecked
def get_helix_event(camera_id: str, time_ms: int, event_type_uid: str):
    """
    Retrieve a Helix Event.

    :param camera_id: The unique identifier of the camera.
    :param time_ms: The event time as a Unix timestamp in milliseconds.
    :param event_type_uid: The UID of the Helix Event Type.
    :return: JSON response containing the event details.
    :raises ValueError: If any required parameter is missing or invalid.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the HelixClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a HelixClient object directly for better performance.
    """
    return HelixClient().get_helix_event(camera_id, time_ms, event_type_uid)

@typechecked
def get_helix_event_types(event_type_uid: Optional[str] = None, name: Optional[str] = None):
    """
    Retrieve a list of Helix Event Types from the organization.

    This method returns all Helix Event Types along with their associated names and schemas.
    You can optionally narrow down the results by specifying either an event type UID or an event type name.

    :param event_type_uid: (Optional) The unique identifier of the event type to filter by.
    :param name: (Optional) The name of the event type to filter by.
    :return: JSON response containing Helix Event Types.
    :raises ValueError: If event_type_uid or name is provided as an empty string.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the HelixClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a HelixClient object directly for better performance.
    """
    return HelixClient().get_helix_event_types(event_type_uid, name)

@typechecked
def search_helix_events(camera_ids: List[str], end_time_ms: int, event_type_uid: str, flagged: bool, keywords: List[str], start_time_ms: int, attribute_filters: Optional[List[Dict[str, Any]]] = None):
    """
    Search for Helix Events in Command.

    This function sends a POST request to search for one or more Helix Events
        that have already been posted
    to Command. It requires that the API token (provided via headers)
        has Helix permissions.

    The search is refined by specifying:
      - camera_ids: A list of unique camera IDs.
      - end_time_ms: The query end epoch time in milliseconds.
      - event_type_uid: The unique identifier of the event type.
      - flagged: A boolean indicating whether to filter for flagged events.
      - keywords: A list of search keywords.
      - start_time_ms: The query start epoch time in milliseconds.

    :param attribute_filters: Optional list of additional filter objects.
    :param camera_ids: List of unique camera IDs (must be non-empty).
    :param end_time_ms: Query end epoch time in milliseconds (must be positive).
    :param event_type_uid: Unique identifier of the event type
        (non-empty string).
    :param flagged: Boolean indicating whether to filter for flagged events.
    :param keywords: List of search keywords (each must be non-empty).
    :param start_time_ms: Query start epoch time in milliseconds
        (must be positive and <= end_time_ms).
    :return: JSON response containing the search results.
    :raises ValueError: If any required parameter is missing or invalid.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the HelixClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a HelixClient object directly for better performance.
    """
    return HelixClient().search_helix_events(camera_ids, end_time_ms, event_type_uid, flagged, keywords, start_time_ms, attribute_filters)

@typechecked
def update_helix_event(camera_id: str, time_ms: int, event_type_uid: str, flagged: bool, extra_attributes: Optional[Dict[str, Any]] = None):
    """
    Update an existing Helix Event in Command.

    This method updates an already-posted Helix Event. To perform the update,
    you must supply the following query parameters:
      - camera_id: The unique identifier of the camera.
      - time_ms: The event epoch time in milliseconds.
      - event_type_uid: The unique identifier of the event type.

    In the request body, an "attributes" object is provided, which must include the
    required "flagged" boolean parameter. Additional attribute updates can be supplied
    via the extra_attributes parameter.

    :param camera_id: The unique identifier of the camera.
    :param time_ms: The event epoch time in milliseconds (must be a positive integer).
    :param event_type_uid: The unique identifier of the Helix Event Type.
    :param flagged: Boolean indicating whether the event is flagged.
    :param extra_attributes: Optional dictionary of additional attribute key-value pairs to update.
    :return: JSON response containing the updated Helix Event details.
    :raises ValueError: If camera_id or event_type_uid is an empty string, or if time_ms is not positive.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the HelixClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a HelixClient object directly for better performance.
    """
    return HelixClient().update_helix_event(camera_id, time_ms, event_type_uid, flagged, extra_attributes)

@typechecked
def update_helix_event_type(event_type_uid: str, event_schema: Dict[str, str], name: str):
    """
    Update an existing Helix Event Type.

    :param event_type_uid: The unique identifier of the Helix Event Type.
    :param event_schema: A dictionary representing the updated event schema.
    :param name: The updated name for the event type.
    :return: JSON response containing the updated event type information.
    :raises ValueError: If any required parameter is missing or invalid.

    ---

    **Note:** This is a functional wrapper for its equivalent method in the HelixClient. It creates a new client instance on every call, making it best for single, convenient operations. For making multiple API calls, instantiate and use a HelixClient object directly for better performance.
    """
    return HelixClient().update_helix_event_type(event_type_uid, event_schema, name)
