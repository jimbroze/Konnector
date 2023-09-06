from attrs import frozen, field, validators


def to_int_disallow_float(priority):
    if float(priority) != int(priority):
        raise ValueError("priority must be an integer")
    return int(priority)


@frozen
class TodoistPriority:
    """1 (low, default) to 4 (urgent)"""

    priority: int = field(
        default=1,
        converter=to_int_disallow_float,
        validator=[validators.ge(1), validators.le(4)],
    )

    def to_int(self) -> int:
        return self.priority
