from __future__ import annotations
from abc import ABC, abstractmethod
import logging

from activity_date_time import ActivityDateTime

logger = logging.getLogger("gunicorn.error")


class Activity(ABC):
    """
    A class to represent an activity in a list.

    ...

    Attributes
    ----------
    id : str
        A unique identifier for the activity.
    name : str
        The name of the activity.
    description : str
        A description of the activity.
    priority : int
        The activity's importance. 1 is highest, 4 is lowest, 3 is default.
    start_datetime : str
        When the activity starts
    end_datetime : str
        When the activity ends
    """

    def __init__(
        self,
        id: str = None,
        name: dict = None,
        description: bool = None,
        priority: int = None,
        start_datetime: ActivityDateTime = None,
        end_datetime: ActivityDateTime = None,
    ):
        """
        Parameters
        ----------
        id : str
            A unique identifier for the activity.
        name : str
            The name of the activity.
        description : str
            A description of the activity.
        priority : int
            The activity's importance. 1 is highest, 4 is lowest, 3 is default.
        start_datetime : str
            When the activity starts
        end_datetime : str
            When the activity ends
        """

        if id is not None:
            self.id = id
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if priority is not None:
            self.priority = priority
        if start_datetime is not None:
            self.start_datetime = start_datetime
        if end_datetime is not None:
            self.end_datetime = end_datetime

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return (
            f"Activity(name={self.name}, description={self.description},"
            f" priority={self.priority}, start_datetime={self.start_datetime},"
            f" end_datetime={self.end_datetime})"
        )