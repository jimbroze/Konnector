# Postponed evaluation allows static typing reference to class within itself
from __future__ import annotations
import logging
from konnector.lib.platform.platform import Platform

logger = logging.getLogger("gunicorn.error")


class Task:
    """
    A class to represent a task in a productivity list.

    ...

    Attributes
    ----------
    properties : dict
        A dictionary of task properties. These are:
            name : str
                The name of the task.
            description : str
                A description of the task.
            priority : int
                The task's importance. 1 is highest, 4 is lowest, 3 is default.
            due_date : str
                When the task must be completed by.
            due_time_included : boo
                If due_date includes a time.
    new : bool
        If the task has just been created.
    lists : dict
        A dictionary containing lists that this task is in, indexed by the productivity
        platform that the list exists on. Currently tasks can only be in one list per
        platform.
    completed : dict
        A dictionary of booleans that indicate if this task has been completed on a
        productivity platform. Indexed by the platform.
    ids : dict
        A dictionary containing IDs that reference this task on a productivity platform.
        Indexed by the platform.
    """

    def __init__(
        self,
        properties: dict = None,
        new: bool = None,
        lists: dict[Platform, str] = None,
        completed: dict[Platform, str] = None,
        ids: dict[Platform, str] = None,
    ):
        """
        Parameters
        ----------
        properties : dict
            A dictionary of task properties. These are:
                name : str
                    The name of the task.
                description : str
                    A description of the task.
                priority : int
                    The task's importance. 1 is highest, 4 is lowest, 3 is default.
                due_date : str
                    When the task must be completed by.
                due_time_included : boo
                    If due_date includes a time.
        new : bool
            If the task has just been created.
        lists : dict
            A dictionary containing list names that this task is in. An object
            representing the platform is used as the key.
        completed : dict
            A dictionary of booleans that indicate if this task has been completed on a
            productivity platform. An object representing the platform is used as the
            key.
        ids : dict
            A dictionary containing IDs that reference this task on a productivity
            platform. An object representing the platform is used as the key.
        """
        # Defaults
        self.properties = {
            "name": None,
            "description": None,
            "priority": None,  # 1 highest, 4 lowest. 3 is default.
            "due_date": None,  # time since epoch in ms
            "due_time_included": None,
        }
        # TODO make new private to prevent update!
        self.new = False
        self.lists = {}  # {Platform: "listName"}
        self.completed = {}  # {Platform: bool}
        self.ids = {}  # {Platform: "id"}

        if properties is not None:
            for propName in properties:
                if properties[propName] is not None:
                    self.properties[propName] = properties[propName]
                    if propName in ("priority", "due_date"):
                        self.properties[propName] = int(self.properties[propName])
        if new is not None:
            self.new = new
            if new is True:
                self.properties["priority"] = 3  # Default priority on new tasks is 3
        if lists is not None:
            self.lists = lists
        if completed is not None:
            self.completed = completed
        if ids is not None:
            for idPlatform in ids:
                self.ids[idPlatform] = str(ids[idPlatform])

    def __str__(self):
        return f"{self.get_property('name')}"

    def __repr__(self):
        return (
            f"Task(properties={self.get_all_properties()}, new={self.new},"
            f" lists={self.get_all_lists()}, completed={self.get_all_completed()},"
            f" ids={self.get_all_ids()})"
        )

    def __sub__(self, other: Task) -> Task:
        """
        Subtraction method. Return a task with properties, lists, ids and "completed"
        booleans that are in the first task but not the second (in this task but not the
        other).
        """
        propDiffs = {
            k: (
                self.get_property(k)
                if self.get_property(k) != other.get_property(k)
                else None
            )
            for k in self.get_all_properties()
        }
        listDiffs = {
            k: self.get_list(k)
            for k in self.get_all_lists()
            if k not in other.get_all_lists() or self.get_list(k) != other.get_list(k)
        }
        completedDiffs = {
            k: self.get_completed(k)
            for k in self.get_all_completed()
            if k not in other.get_all_completed()
            or self.get_completed(k) != other.get_completed(k)
        }
        idDiffs = {
            k: self.get_id(k)
            for k in self.get_all_ids()
            if k not in other.get_all_ids() or self.get_id(k) != other.get_id(k)
        }
        newTask = Task(
            properties=propDiffs,
            lists=listDiffs,
            completed=completedDiffs,
            ids=idDiffs,
        )
        return newTask

    def get_all_properties(self) -> dict[str, any]:
        """Get the full dictionary of task properties."""
        return self.properties

    def get_property(self, propName: str):
        """Get a single property value using the property name."""
        if propName in self.properties:
            return self.properties[propName]
        else:
            raise Exception(f"Unknown property name: {propName}")

    def set_property(self, propName: str, propValue) -> None:
        """Set the value of a task property."""
        self.properties[propName] = propValue

    def get_all_lists(self) -> dict[Platform, str]:
        """Get the full dictionary of platform task lists that this task is in."""
        return self.lists

    def get_list(self, platform: Platform) -> str:
        """Return the list name for a given platform in this task."""
        return self.lists[platform] if platform in self.lists else None

    def add_list(self, platform: Platform, listName: str) -> None:
        """Add the name of a list, to the task object, that the task is stored in on a
        productivity platform"""
        self.lists[platform] = listName

    def remove_list(self, platform: Platform) -> None:
        """Remove a list, from the task object, that the task is stored in on a
        productivity platform"""
        del self.lists[platform]

    def get_all_completed(self) -> dict[Platform, bool]:
        """Get the full dictionary of booleans that indicate if the task is completed"""
        return self.completed

    def get_completed(self, platform: Platform) -> bool:
        """Check if this task is completed on a given platform."""
        return self.completed[platform] if platform in self.completed else None

    def get_all_ids(self) -> dict[Platform, str]:
        """Get the full dictionary of ids that can be used to fetch this task from
        productivity platforms."""
        return self.ids

    def get_id(self, platform: Platform) -> str:
        """Return the ID that is used to fetch this task from a given productivity
        platform"""
        return self.ids[platform] if platform in self.ids else None

    def add_id(self, platform: Platform, id: str) -> None:
        """Add an ID to the task object that can be used to fetch this task from a
        productivity platform"""
        self.ids[platform] = id

    def remove_id(self, platform: Platform) -> None:
        """Remove an ID used to fetch this task from a given productivity platform"""
        del self.ids[platform]

    def count_ids(self) -> int:
        """Return the number of ids with a length > 0"""
        return len([v for v in self.get_all_ids().values() if len(v) > 0])
