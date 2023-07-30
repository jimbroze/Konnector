from __future__ import annotations
from attrs import define, field
from datetime import datetime, date, time
from pytz import timezone


@define
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
        dt = datetime.combine(date_obj, time.min.replace(hour=4), timezone("UTC"))
        return cls(dt.timestamp() * 1000, False)

    @classmethod
    def from_datetime(
        cls, datetime_obj: datetime, time_included: bool = None
    ) -> ClickupDatetime:
        utc_dt = datetime_obj.astimezone(timezone("UTC"))
        return cls(int(utc_dt.timestamp()) * 1000, time_included)

    def __attrs_post_init__(self) -> ClickupDatetime:
        if self.time_included is False:
            self.remove_time()

    def remove_time(self) -> ClickupDatetime:
        dt = datetime.utcfromtimestamp(self.timestamp / 1000).replace(
            hour=4, minute=0, second=0, microsecond=0
        )
        self.timestamp = dt.timestamp() * 1000
        return self

    def to_int(self) -> int:
        return self.timestamp
