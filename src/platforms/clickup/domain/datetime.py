from __future__ import annotations
from attrs import frozen, field
from datetime import datetime, date, time
from pytz import timezone


@frozen
class ClickupDatetime:
    timestamp: int = field(converter=int)
    time_included: bool

    @classmethod
    def from_time_unknown(cls, timestamp: int, clickupTz: timezone) -> ClickupDatetime:
        """
        Calculates if a timestamp includes time.
        Clickup sets null times to 4am in the local timezone.
        """
        dt = datetime.fromtimestamp(int(timestamp) / 1000, timezone("UTC"))
        localDt = dt.astimezone(clickupTz)
        time_included = not (
            localDt.microsecond == 0
            and localDt.second == 0
            and localDt.minute == 0
            and localDt.hour == 4
        )
        return cls(timestamp, time_included)

    @classmethod
    def from_date(cls, date_obj: date) -> ClickupDatetime:
        dt = datetime.combine(date_obj, time.min.replace(hour=4))
        return cls(dt.timestamp() * 1000, False)

    @classmethod
    def from_datetime(
        cls, datetime_obj: datetime, time_included: bool = None
    ) -> ClickupDatetime:
        return cls(int(datetime_obj.timestamp()) * 1000, time_included)

    def to_int(self) -> int:
        return self.timestamp
