from __future__ import annotations
from attrs import define, field
from item_datetime import datetime, date, time
from pytz import timezone, utc


@define
class ClickupDatetime:
    """
    Unix time (UTC) in milliseconds

    Clickup provides a utc timestamp. It is set to 4am local if time is not included

    Clickup expects a utc timestamp and (optionally) a time_included flag

    """

    timestamp_milli: int = field(converter=int)
    time_included: bool

    @classmethod
    def from_timestamp(cls, timestamp: int, clickupTz: timezone) -> ClickupDatetime:
        """
        Calculates if a timestamp includes time.
        Clickup sets null times to 4am in the local timezone.
        """
        timestamp_seconds = (
            int(timestamp) / 1000 if len(str(int(timestamp))) >= 12 else int(timestamp)
        )

        dt = datetime.fromtimestamp(timestamp_seconds, timezone("UTC"))
        localDt = dt.astimezone(clickupTz)

        time_included = not (
            localDt.microsecond == 0
            and localDt.second == 0
            and localDt.minute == 0
            and localDt.hour == 4
        )
        return cls(timestamp_seconds * 1000, time_included)

    @classmethod
    def from_date(cls, date_obj: date, tz: timezone = utc) -> ClickupDatetime:
        """Defaults to utc if timezone is not provided"""

        dt = datetime.combine(date_obj, time.min.replace(hour=4), tz)
        return cls(dt.timestamp() * 1000, False)

    @classmethod
    def from_datetime(
        cls, datetime_obj: datetime, time_included: bool = True
    ) -> ClickupDatetime:
        """Defaults to utc if timezone is not set on datetime_obj"""

        local_datetime = (
            datetime_obj if datetime_obj.tzinfo else utc.localize(datetime_obj)
        )

        if not time_included:
            local_datetime = local_datetime.replace(
                hour=4, minute=0, second=0, microsecond=0
            )

        datetime_utc = local_datetime.astimezone(utc)

        return cls(int(datetime_utc.timestamp() * 1000), time_included)

    def to_timestamp_milli(self) -> int:
        return self.timestamp_milli

    def to_timestamp_seconds(self) -> int:
        return self.timestamp_milli / 1000

    def to_datetime_utc(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp_milli / 1000, timezone("UTC"))

    def contains_time(self) -> bool:
        return self.time_included
