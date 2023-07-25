from __future__ import annotations
from attrs import define
from datetime import datetime, date
from pytz import timezone, utc


@define
class TodoistDatetime:
    date_string: str
    datetime_string_utc: str = None
    timezone_string: str = "UTC"

    @classmethod
    def from_date(cls, date_obj: date) -> TodoistDatetime:
        date_string = date_obj.strftime("%Y-%m-%d")
        return cls(date_string, None, None)

    @classmethod
    def from_datetime(cls, datetime_obj: datetime) -> TodoistDatetime:
        date_string = datetime_obj.strftime("%Y-%m-%d")

        if datetime_obj.tzinfo:
            timezone_string = str(datetime_obj.tzinfo)
            local_dt = datetime_obj
        else:
            timezone_string = "UTC"
            local_dt = timezone(timezone_string).localize(datetime_obj)

        datetime_string_utc = local_dt.astimezone(utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return cls(date_string, datetime_string_utc, timezone_string)

    def __attrs_post_init__(self) -> TodoistDatetime:
        if self.datetime_string_utc is None:
            self.timezone_string = None

    def to_datetime_utc(self) -> bool:
        return (
            timezone(self.timezone_string)
            .localize(
                datetime.strptime(self.datetime_string_utc, "%Y-%m-%dT%H:%M:%S.%fZ")
            )
            .astimezone(utc)
        )

    def to_datetime_string_local(self) -> bool:
        return (
            timezone(self.timezone_string)
            .localize(
                datetime.strptime(self.datetime_string_utc, "%Y-%m-%dT%H:%M:%S.%fZ")
            )
            .astimezone(timezone(self.timezone_string))
            .strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        )

    def contains_time(self) -> bool:
        return self.datetime_string_utc is not None
