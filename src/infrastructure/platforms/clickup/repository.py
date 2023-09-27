from typing import Optional
from pytz import timezone
import logging
from dotenv import load_dotenv
import requests

# from konnector.domain.item.repositories import ItemRepository
from domain.platforms.clickup.item_datetime import ClickupDatetime
from domain.platforms.clickup.priority import ClickupPriority
from domain.platforms.clickup.item import ClickupItem


load_dotenv()

# TIMEZONE = os.environ["TIMEZONE"]
logger = logging.getLogger("gunicorn.error")


class ClickupRepository:
    name = "clickup"
    apiUrl = "https://api.clickup.com/api/v2"

    def __init__(self, accessToken: str, local_tz: timezone):
        self.accessToken = accessToken
        self.local_tz = local_tz
        self.headers = {
            "Authorization": accessToken,
            "Content-Type": "application/json",
        }

    def __str__(self) -> str:
        return f"{self.name}"

    def _send_request(
        self,
        url,
        reqType: str = "GET",
        params: dict = {},
        data: dict = {},
    ):
        """
        Send a http request to Clickup's API.
        Requires a URL. Optionally requires a request type, parameters and request data.
        Returns the request JSON response or an empty response.
        """

        headers = self.headers
        fullUrl = self.apiUrl + url
        try:
            if not data:
                response = requests.request(
                    reqType, fullUrl, headers=headers, params=params, timeout=5
                )
            else:
                response = requests.request(
                    reqType,
                    fullUrl,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=5,
                )

            # Raise exception if error code returned
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.warning(e)
            raise
        if response.status_code == 204:
            return

        return response.json()

    def get_items(self, list_id: str) -> list[ClickupItem]:
        """
        Retrieve a list of items from the platform's API.

        Arguments:
            list_id: The ID of a list that items should be taken from

        Returns:
            A list of (Item) objects
        """

        # TODO Test if required
        # # Listname required for clickup
        # if list_name is None:
        #     raise Exception("A list name is required to get items from Clickup")

        try:
            retrieved_items = self._send_request(f"/list/{list_id}/task", "GET", {})[
                "tasks"
            ]
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                logger.warning(f"No Clickup items found in list: {list_id}")
                return []
            raise
        except requests.exceptions.RequestException:
            raise

        logger.debug(f"{len(retrieved_items)} Clickup tasks retrieved.")
        return [
            ClickupItemMapper.to_entity(retrieved_item, self.local_tz)
            for retrieved_item in retrieved_items
        ]

    def get_item_by_id(self, item_id: str) -> Optional[ClickupItem]:
        """
        Retrieve a specific item from the platform's API and convert to a item object.
        Either a itemId or a item containing an Id can be used to fetch the item.

        Arguments:
            item_id: The ID of the item to be retrieved from the platform

        Returns:
            The item retrieved from Clickup, converted to a ClickupItem entity,
                or None if the item does not exist
        """

        logger.debug(f"Trying to get an item from Clickup. Item ID: {item_id}")

        try:
            retrieved_item = self._send_request(f"/task/{item_id}", "GET", {})
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                logger.warning(f"No Clickup item found with ID: {item_id}")
                return None
            raise
        except requests.exceptions.RequestException:
            raise

        clickup_item = ClickupItemMapper.to_entity(retrieved_item, self.local_tz)

        logger.debug(f"Clickup item retrieved. Item: ${clickup_item}")
        return clickup_item

    def create_item(self, item: ClickupItem, list_id: str) -> ClickupItem:
        """
        Create a new item on Clickup's API from a item object.

        Arguments:
            item: The item object to be sent to the API
            list_id: The ID of a list that the item should be added to

        Returns:
            The created item
        """

        logger.debug(f"Trying to create item in Clickup list: {list_id}. Item: {item}")

        if item.name is None:
            raise ValueError("Content is required to create a new Todoist item")

        item_properties = ClickupItemMapper.from_entity(item)

        try:
            created_item = self._send_request(
                f"/list/{list_id}/task", "POST", {}, item_properties
            )
        except requests.exceptions.RequestException:
            raise

        clickup_item = ClickupItemMapper.to_entity(created_item, self.local_tz)

        logger.debug(f"Clickup item created. Item: {clickup_item}")
        return clickup_item

    def update_item(self, item: ClickupItem) -> ClickupItem:
        """
        Update the properties of an existing item on the platform's API.

        Arguments:
            item: An item containing the updated properties

        Returns:
            The updated item
        """

        logger.debug(f"Trying to update item on Clickup. Item: {item}")

        item_properties = ClickupItemMapper.from_entity(item)

        try:
            update_item_properties = self._send_request(
                f"/task/{item.id}", "PUT", {}, item_properties
            )
        except requests.exceptions.RequestException as err:
            raise Exception(
                f"Error updating Clickup item with details: {item_properties}. "
                f"Error: {err}"
            )

        logger.debug(f"Clickup item updated. Item: {item}")

        # Clickup requires custom field updates to use a different endpoint
        updated_item = ClickupItemMapper.to_entity(
            update_item_properties, self.local_tz
        )

        changed_custom_fields_item = item - updated_item

        if changed_custom_fields_item.custom_fields:
            return self.update_custom_fields(changed_custom_fields_item)
        else:
            return updated_item

    def delete_item_by_id(self, item_id: ClickupItem) -> bool:
        """
        Delete a item on Clickup's API.

        Arguments:
            item: The item to be deleted.

        Returns:
            If the operation was successful
        """

        logger.debug(f"Trying to delete item from Clickup. Item_id: {item_id}")

        try:
            self._send_request(f"/task/{item_id}", "DELETE", {})
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                logger.warning(f"No Clickup item found with ID: {item_id}")
                return False
            raise
        except requests.exceptions.RequestException:
            raise

        logger.debug(f"Clickup item deleted. Item_id: {item_id}")

        return True

    def set_item_complete(self, item: ClickupItem) -> ClickupItem:
        """
        Mark an existing item as complete on the Clickup's API.

        Arguments:
            item: The item to be completed.

        Returns:
            The completed item
        """

        logger.info(f"Trying to mark Clickup item as complete. Item: {item}")

        retrievedItem = self.get_item_by_id(item.id)
        if retrievedItem is None:
            # TODO create a GetItemException or NotFoundException?
            raise Exception(f"Error getting item from Clickup. Item: {item}")
        if retrievedItem.is_complete:
            raise Exception("Clickup item already complete")

        item_to_update = ClickupItem(id=item.id)
        item_to_update.is_complete = True

        item_properties = ClickupItemMapper.from_entity(item_to_update)

        try:
            updated_item = self._send_request(
                f"/task/{item.id}", "PUT", {}, item_properties
            )
        except requests.exceptions.RequestException:
            raise

        clickup_item = ClickupItemMapper.to_entity(updated_item, self.local_tz)
        logger.debug(f"Clickup item completed. Item: {clickup_item}")

        return clickup_item

    def update_custom_fields(self, item: ClickupItem) -> ClickupItem:
        """
        Update the custom fields of an existing Clickup item

        Arguments:
            item: The item to be updated.

        Returns:
            The updated clickup item
        """

        logger.debug(f"Trying to update item custom fields on Clickup. Item: {item}.")

        if not item.custom_fields:
            raise Exception(f"No Clickup custom fields found in item. Item: {item}")

        for field_id, field_value in item.custom_fields.items():
            try:
                self._send_request(
                    f"/task/{item.id}/field/{field_id}",
                    "POST",
                    {},
                    {"value": field_value},
                )
            except requests.exceptions.RequestException as err:
                raise Exception(
                    f"Error updating Clickup item custom fields. Field ID: {field_id}. "
                    f"Error: {err}"
                )

        logger.debug(f"Updated custom fields on Clickup item. Item: {item}")

        return ClickupItemMapper.to_entity(self.get_item_by_id(item.id), self.local_tz)


class ClickupItemMapper:
    """A date transfer object that maps Clickup Items from Clickup API data"""

    @staticmethod
    def to_entity(clickup_response: dict, local_tz: timezone) -> ClickupItem:
        return ClickupItem(
            id=clickup_response["id"],
            name=clickup_response["name"],
            description=clickup_response["description"],
            priority=ClickupPriority(clickup_response["priority"]["id"])
            if clickup_response["priority"] is not None
            else None,
            start_datetime=ClickupDatetime.from_timestamp(
                clickup_response["start_date"], local_tz
            )
            if clickup_response["start_date"] is not None
            else None,
            end_datetime=ClickupDatetime.from_timestamp(
                clickup_response["due_date"], local_tz
            )
            if clickup_response["due_date"] is not None
            else None,
            created_datetime=ClickupDatetime(clickup_response["date_created"], True),
            updated_datetime=ClickupDatetime(clickup_response["date_updated"], True),
            status=clickup_response["status"]["status"],
            custom_fields={
                field["id"]: (field["value"] if "value" in field else None)
                for field in clickup_response["custom_fields"]
            },
        )

    @staticmethod
    def from_entity(item: ClickupItem) -> dict:
        clickup_dict = {
            "name": item.name,
        }
        if item.description:
            clickup_dict["description"] = item.description
        if item.priority:
            clickup_dict["priority"] = item.priority.to_int()
        if item.start_datetime:
            clickup_dict["start_date"] = item.start_datetime.to_timestamp_milli()
            clickup_dict["start_date_time"] = item.start_datetime.contains_time()
        if item.end_datetime:
            clickup_dict["due_date"] = item.end_datetime.to_timestamp_milli()
            clickup_dict["due_date_time"] = item.end_datetime.contains_time()
        if item.status:
            clickup_dict["status"] = item.status
        if item.custom_fields:
            clickup_dict["custom_fields"] = [
                {"id": id, "value": value} for (id, value) in item.custom_fields.items()
            ]
        return clickup_dict
