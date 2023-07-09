from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ItemDateTime:
    date_time: datetime
    time_included: bool


@dataclass(frozen=True)
class ItemPriority:
    priority: int = 3

    def __post_init__(self):
        if not 0 <= self.priority <= 4:
            raise ValueError("Value should be between 0 and 4 inclusive")