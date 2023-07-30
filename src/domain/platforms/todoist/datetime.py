from __future__ import annotations
from attrs import define, field, validators
from datetime import datetime, date
from pytz import timezone, utc


@define
class TodoistDatetime:
    # TODO add validation and tests
    date_obj: date = field(validator=validators.optional(validators.instance_of(date)))
    datetime_utc: datetime = field(
        default=None, validator=validators.optional(validators.instance_of(datetime))
    )
    timezone_string: str = field(
        default="UTC",
        eq=False,
        validator=validators.optional(validators.instance_of(str)),
    )  # TODO is this what we want? Need to add test

    @classmethod
    def from_date(cls, date_obj: date) -> TodoistDatetime:
        return cls(date_obj, None, None)

    @classmethod
    def from_datetime(cls, datetime_obj: datetime) -> TodoistDatetime:
        date_obj = datetime_obj.date()

        if datetime_obj.tzinfo:
            timezone_string = str(datetime_obj.tzinfo)
            local_datetime = datetime_obj
        else:
            timezone_string = "UTC"
            local_datetime = timezone(timezone_string).localize(datetime_obj)

        datetime_utc = local_datetime.astimezone(utc)
        return cls(date_obj, datetime_utc, timezone_string)

    @classmethod
    def from_strings(
        cls,
        date_string: str,
        datetime_string_utc: str = None,
        timezone_string: str = "UTC",
    ) -> TodoistDatetime:
        date_obj = date.fromisoformat(date_string) if date_string else None

        if datetime_string_utc is None:
            datetime_obj = None
        else:
            if "Z" in datetime_string_utc:
                datetime_string_utc = datetime_string_utc[:-1]

            format = (
                "%Y-%m-%dT%H:%M:%S.%f"
                if "." in datetime_string_utc
                else "%Y-%m-%dT%H:%M:%S"
            )

            datetime_obj = utc.localize(datetime.strptime(datetime_string_utc, format))

        return cls(date_obj, datetime_obj, timezone_string)

    def __attrs_post_init__(self) -> TodoistDatetime:
        if self.datetime_utc is None:
            self.timezone_string = None

    def to_date_string(self) -> bool:
        return self.date_obj.isoformat()

    def to_datetime_string_utc(self) -> bool:
        return self.datetime_utc.isoformat("T", "microseconds")

    def to_datetime_string_local(self) -> bool:
        return (
            utc.localize(self.datetime_utc)
            .astimezone(timezone(self.timezone_string))
            .isoformat()
        )

    def contains_time(self) -> bool:
        return self.datetime_utc is not None
