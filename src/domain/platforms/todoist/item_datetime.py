from __future__ import annotations
from attrs import define, field, validators
from item_datetime import datetime, date, tzinfo, timedelta, timezone as offset_timezone
from pytz import timezone, utc, UnknownTimeZoneError
from re import match


def get_timezone_from_offset(offset: str) -> tzinfo:
    sign, hours, minutes = match(r"UTC([+\-])(\d{2}):(\d{2})", offset).groups()
    sign = -1 if sign == "-" else 1
    hours, minutes = int(hours), int(minutes)

    return offset_timezone(sign * timedelta(hours=hours, minutes=minutes))


@define
class TodoistDatetime:
    """
    Date, timezone and (optionally) datetime in UTC.

    Todoist provides a date and (optionally) a datetime and timezone.

    Todoist expects a local date or utc datetime

    Timezone defaults to utc if not given.
    """

    date_obj: date = field(validator=validators.instance_of(date))
    datetime_utc: datetime = field(
        default=None, validator=validators.optional(validators.instance_of(datetime))
    )
    timezone: timezone = field(
        default=utc,
        eq=False,
        validator=validators.instance_of(tzinfo),
    )

    @classmethod
    def from_date(cls, date_obj: date, tz: timezone = utc) -> TodoistDatetime:
        """Defaults to utc if timezone is not provided"""

        return cls(date_obj, None, tz)

    @classmethod
    def from_datetime(
        cls, datetime_obj: datetime, time_included: bool = True
    ) -> TodoistDatetime:
        """Defaults to utc if timezone is not set on datetime_obj"""

        date_obj = datetime_obj.date()

        local_datetime = (
            datetime_obj if datetime_obj.tzinfo else utc.localize(datetime_obj)
        )
        datetime_utc = local_datetime.astimezone(utc) if time_included else None

        return cls(date_obj, datetime_utc, local_datetime.tzinfo)

    @classmethod
    def from_strings(
        cls,
        date_string: str = None,
        timezone_string: str = "UTC",
        datetime_string_utc: str = None,
    ) -> TodoistDatetime:
        """
        Either a date string or datetime string must be provided.

        Timezone defaults to UTC.
        """

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

        date_obj = (
            date.fromisoformat(date_string) if date_string else datetime_obj.date()
        )

        try:
            tz = timezone(timezone_string)
        except UnknownTimeZoneError:
            tz = get_timezone_from_offset(timezone_string)

        return cls(date_obj, datetime_obj, tz)

    def to_date_string(self) -> bool:
        return self.date_obj.isoformat()

    def to_datetime_string_utc(self) -> bool:
        return self.to_datetime_utc().isoformat("T", "microseconds")

    def to_datetime_string_local(self) -> bool:
        return (
            utc.localize(self.datetime_utc)
            .astimezone(timezone(self.timezone_string))
            .isoformat()
        )

    def to_date(self) -> date:
        return self.date_obj

    def to_datetime_utc(self) -> datetime:
        return (
            self.datetime_utc
            if self.datetime_utc
            else datetime.combine(self.date_obj, datetime.min.time(), self.timezone)
        )

    def contains_time(self) -> bool:
        return self.datetime_utc is not None
