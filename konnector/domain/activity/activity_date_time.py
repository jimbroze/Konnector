from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ActivityDateTime:
    date_time: datetime
    time_included: bool
