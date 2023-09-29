from typing import Optional
from pytz import timezone
import logging
from dotenv import load_dotenv
import requests

# from konnector.domain.item.repositories import ItemRepository
from domain.platforms.todoist.item_datetime import TodoistDatetime
from domain.platforms.todoist.priority import TodoistPriority
from domain.platforms.todoist.item import TodoistItem


load_dotenv()

# TIMEZONE = os.environ["TIMEZONE"]
logger = logging.getLogger("gunicorn.error")


class TodoistRepository:
    name = "todoist"
    apiUrl = "https://api.todoist.com/rest/v2"

    def __init__(self, accessToken: str, local_tz: timezone):
        self.accessToken = accessToken
        self.local_tz = local_tz
        self.headers = {
            "Authorization": f"Bearer {accessToken}",
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

    def get_items(self, project_id: str = None) -> list[TodoistItem]:
        """
        Retrieve a list of items from the platform's API.

        Arguments:
            project_id: The optional ID of a list that items should be taken from

        Returns:
            A list of (Item) objects
        """

        request_params = {project_id: project_id} if project_id else {}

        try:
            retrieved_items = self._send_request("/tasks", "GET", request_params)
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                logger.warning(
                    "No Todoist items found"
                    + (f" in project with ID {project_id}" if project_id else "")
                )
                return []
            raise
        except requests.exceptions.RequestException:
            raise

        logger.debug(f"{len(retrieved_items)} Todoist tasks retrieved.")
        return [
            TodoistItemMapper.to_entity(retrieved_item, self.local_tz)
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
            retrieved_item = self._send_request(f"/tasks/{item_id}", "GET", {})
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                logger.warning(f"No Todoist item found with ID: {item_id}")
                return None
            raise
        except requests.exceptions.RequestException:
            raise

        todoist_item = TodoistItemMapper.to_entity(retrieved_item, self.local_tz)

        logger.debug(f"Todoist item retrieved. Item: ${todoist_item}")
        return todoist_item

    def create_item(self, item: TodoistItem, project_id: str = None) -> TodoistItem:
        """
        Create a new item on Todoist's API from a item object.

        Arguments:
            item: The item object to be sent to the API
            project_id: The ID of a list that the item should be added to

        Returns:
            The created item
        """

        logger.debug(
            "Trying to create item in Todoist"
            + (f" project with ID: {project_id}" if project_id else "")
            + f". Item: {item}"
        )

        if item.content is None:
            raise ValueError("Content is required to create a new Todoist item")

        item_properties = TodoistItemMapper.from_entity(item)
        if project_id:
            item_properties["project_id"] = project_id

        try:
            created_item = self._send_request("/tasks", "POST", {}, item_properties)
        except requests.exceptions.RequestException:
            raise

        todoist_item = TodoistItemMapper.to_entity(created_item, self.local_tz)

        logger.debug(f"Todoist item created. Item: {todoist_item}")
        return todoist_item

    def update_item(self, item: TodoistItem) -> TodoistItem:
        """
        Update the properties of an existing item in Todoist.

        Arguments:
            item: An item containing the updated properties

        Returns:
            The updated item
        """

        logger.debug(f"Trying to update item on Todoist. Item: {item}")

        item.project_id = None

        item_properties = TodoistItemMapper.from_entity(item)

        try:
            updated_item_properties = self._send_request(
                f"/tasks/{item.id}", "POST", {}, item_properties
            )
        except requests.exceptions.RequestException as err:
            raise Exception(
                f"Error updating Todoist item with details: {item_properties}. "
                f"Error: {err}"
            )

        logger.debug(f"Todoist item updated. Item: {item}")

        return TodoistItemMapper.to_entity(updated_item_properties, self.local_tz)

    def delete_item_by_id(self, item_id: str) -> bool:
        logger.debug(f"Trying to delete item from Todoist. Item_id: {item_id}")

        try:
            self._send_request(f"/tasks/{item_id}", "DELETE", {})
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                logger.warning(f"No Todoist item found with ID: {item_id}")
                return False
            raise
        except requests.exceptions.RequestException:
            raise

        logger.debug(f"Todoist item deleted. Item_id: {item_id}")

        return True

    def set_item_complete(self, item_id: str) -> TodoistItem:
        """
        Mark an existing item as complete on the Todoist's API.

        Arguments:
            item: The item to be completed.

        Returns:
            The completed item
        """

        logger.info(f"Trying to mark Todoist item as complete. ID: {item_id}")

        retrievedItem = self.get_item_by_id(item_id)
        if retrievedItem is None:
            # TODO create a GetItemException or NotFoundException?
            raise Exception(f"Error getting item from Todoist. ID: {item_id}")
        if retrievedItem.is_completed:
            raise Exception("Todoist item already complete")

        try:
            self._send_request(f"/tasks/{item_id}/close", "POST", {})
        except requests.exceptions.RequestException:
            raise

        todoist_item = self.get_item_by_id(item_id)
        logger.debug(f"Todoist item completed. Item: {todoist_item}")

        return todoist_item


class TodoistItemMapper:
    """A class that maps Todoist Items from Todoist API data"""

    # TODO change names to match Todoist. Task, due etc.
    @staticmethod
    def to_entity(todoist_response: dict, tz: timezone) -> TodoistItem:
        end_datetime = (
            TodoistDatetime.from_strings(
                todoist_response["due"].get("date"),
                todoist_response["due"].get("timezone", None) or str(tz),
                todoist_response["due"].get("datetime", None),
            )
            if todoist_response["due"] is not None
            else None
        )

        print(end_datetime)

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
            created_datetime=TodoistDatetime.from_strings(
                datetime_string_utc=todoist_response["created_at"]
            ),
            is_completed=todoist_response["is_completed"],
            project_id=todoist_response["project_id"],
        )

    @staticmethod
    def from_entity(item: TodoistItem) -> dict:
        todoist_dict = {
            "content": item.content,
        }

        if item.description:
            todoist_dict["description"] = item.description

        if item.priority:
            todoist_dict["priority"] = item.priority.priority

        if item.end_datetime is None:
            todoist_dict["due_string"] = "no date"
        elif item.end_datetime.contains_time():
            todoist_dict["due_datetime"] = item.end_datetime.to_datetime_string_utc()
        else:
            todoist_dict["due_date"] = item.end_datetime.to_date_string()

        if item.project_id:
            todoist_dict["project_id"] = item.project_id

        return todoist_dict
