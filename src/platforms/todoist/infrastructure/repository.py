from typing import Optional
from pytz import timezone
import logging
from dotenv import load_dotenv
import requests

# from konnector.domain.item.repositories import ItemRepository
from platforms.todoist.domain.datetime import TodoistDatetime
from platforms.todoist.domain.priority import TodoistPriority
from platforms.todoist.domain.item import TodoistItem


load_dotenv()

# TIMEZONE = os.environ["TIMEZONE"]
logger = logging.getLogger("gunicorn.error")


class TodoistRepository:
    name = "todoist"
    apiUrl = "https://api.todoist.com/api/v2"

    def __init__(self, accessToken: str, localTz: timezone):
        self.accessToken = accessToken
        self.localTz = localTz
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
        Send a http request to Todoist's API.
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

    def get_items(self, list_id: str) -> list[TodoistItem]:
        """
        Retrieve a list of items from the platform's API.

        Arguments:
            list_id: The ID of a list that items should be taken from

        Returns:
            A list of (Item) objects
        """

        # TODO Test if required
        # # Listname required for todoist
        # if list_name is None:
        #     raise Exception("A list name is required to get items from Todoist")

        try:
            retrieved_items = self._send_request(f"/list/{list_id}/task", "GET", {})[
                "tasks"
            ]
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                logger.warning(f"No Todoist items found in list: {list_id}")
                return []
            raise
        except requests.exceptions.RequestException:
            raise

        logger.debug(f"{len(retrieved_items)} Todoist tasks retrieved.")
        return [
            TodoistItemMapper.to_entity(retrieved_item, self.localTz)
            for retrieved_item in retrieved_items
        ]

    def get_item_by_id(self, item_id: str) -> Optional[TodoistItem]:
        """
        Retrieve a specific item from the platform's API and convert to a item object.
        Either a itemId or a item containing an Id can be used to fetch the item.

        Arguments:
            item_id: The ID of the item to be retrieved from the platform

        Returns:
            The item retrieved from Todoist, converted to a TodoistItem entity,
                or None if the item does not exist
        """

        logger.debug(f"Trying to get an item from Todoist. Item ID: {item_id}")

        try:
            retrieved_item = self._send_request(f"/task/{item_id}", "GET", {})
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                logger.warning(f"No Todoist item found with ID: {item_id}")
                return None
            raise
        except requests.exceptions.RequestException:
            raise

        todoist_item = TodoistItemMapper.to_entity(retrieved_item, self.localTz)

        logger.debug(f"Todoist item retrieved. Item: ${todoist_item}")
        return todoist_item

    def create_item(self, item: TodoistItem, list_id: str) -> TodoistItem:
        """
        Create a new item on Todoist's API from a item object.

        Arguments:
            item: The item object to be sent to the API
            list_id: The ID of a list that the item should be added to

        Returns:
            The created item
        """

        logger.debug(f"Trying to create item in Todoist list: {list_id}. Item: {item}")

        item_properties = TodoistItemMapper.from_entity(item)

        try:
            created_item = self._send_request(
                f"/list/{list_id}/task", "POST", {}, item_properties
            )
        except requests.exceptions.RequestException:
            raise

        todoist_item = TodoistItemMapper.to_entity(created_item, self.localTz)

        logger.debug(f"Todoist item created. Item: {todoist_item}")
        return todoist_item

    def update_item(self, item: TodoistItem) -> TodoistItem:
        """
        Update the properties of an existing item on the platform's API.

        Arguments:
            item: An item containing the updated properties

        Returns:
            The updated item
        """

        logger.debug(f"Trying to update item on Todoist. Item: {item}")

        item_properties = TodoistItemMapper.from_entity(item)

        try:
            update_item_properties = self._send_request(
                f"/task/{item.id}", "PUT", {}, item_properties
            )
        except requests.exceptions.RequestException as err:
            raise Exception(
                f"Error updating Todoist item with details: {item_properties}. "
                f"Error: {err}"
            )

        logger.debug(f"Todoist item updated. Item: {item}")

        # Todoist requires custom field updates to use a different endpoint
        updated_item = TodoistItemMapper.to_entity(update_item_properties, self.localTz)

        changed_custom_fields_item = item - updated_item

        if changed_custom_fields_item.custom_fields:
            return self.update_custom_fields(changed_custom_fields_item)
        else:
            return updated_item

    def delete_item_by_id(self, item_id: TodoistItem) -> bool:
        """
        Delete a item on Todoist's API.

        Arguments:
            item: The item to be deleted.

        Returns:
            If the operation was successful
        """

        logger.debug(f"Trying to delete item from Todoist. Item_id: {item_id}")

        try:
            self._send_request(f"/task/{item_id}", "DELETE", {})
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                logger.warning(f"No Todoist item found with ID: {item_id}")
                return False
            raise
        except requests.exceptions.RequestException:
            raise

        logger.debug(f"Todoist item deleted. Item_id: {item_id}")

        return True

    def set_item_complete(self, item: TodoistItem) -> TodoistItem:
        """
        Mark an existing item as complete on the Todoist's API.

        Arguments:
            item: The item to be completed.

        Returns:
            The completed item
        """

        logger.info(f"Trying to mark Todoist item as complete. Item: {item}")

        retrievedItem = self.get_item_by_id(item.id)
        if retrievedItem is None:
            # TODO create a GetItemException or NotFoundException?
            raise Exception(f"Error getting item from Todoist. Item: {item}")
        if retrievedItem.is_completed:
            raise Exception("Todoist item already complete")

        item_to_update = TodoistItem(id=item.id)
        item_to_update.is_completed = True

        item_properties = TodoistItemMapper.from_entity(item_to_update)

        try:
            updated_item = self._send_request(
                f"/task/{item.id}", "PUT", {}, item_properties
            )
        except requests.exceptions.RequestException:
            raise

        todoist_item = TodoistItemMapper.to_entity(updated_item, self.localTz)
        logger.debug(f"Todoist item completed. Item: {todoist_item}")

        return todoist_item


class TodoistItemMapper:
    """A date transfer object that maps Todoist Items from Todoist API data"""

    @staticmethod
    def to_entity(todoist_response: dict) -> TodoistItem:
        end_datetime = (
            TodoistDatetime(
                todoist_response["due"].get("date", None),
                todoist_response["due"].get("datetime", None),
                todoist_response["due"].get("timezone", None),
            )
            if todoist_response["due"] is not None
            else None
        )

        return TodoistItem(
            id=todoist_response["id"],
            content=todoist_response["content"],
            description=todoist_response["description"],
            priority=(
                TodoistPriority(todoist_response["priority"])
                if todoist_response["priority"] is not None
                else None
            ),
            end_datetime=end_datetime,
            created_datetime=TodoistDatetime(None, todoist_response["created_at"]),
            is_completed=todoist_response["is_completed"],
        )

    @staticmethod
    def from_entity(item: TodoistItem) -> dict:
        todoist_dict = {
            "content": item.content,
        }

        if item.description:
            todoist_dict["description"] = item.description

        if item.priority:
            todoist_dict["priority"] = item.priority.to_int()

        if item.end_datetime is None:
            todoist_dict["due_string"] = "no date"
        elif item.end_datetime.contains_time():
            todoist_dict["due_datetime"] = item.end_datetime.datetime_string_utc
        else:
            todoist_dict["due_date"] = item.end_datetime.date_string

        return todoist_dict
