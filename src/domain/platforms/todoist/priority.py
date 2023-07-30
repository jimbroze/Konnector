from attrs import frozen, field, validators


def to_int_disallow_float(priority):
    if float(priority) != int(priority):
        raise ValueError("priority must be an integer")
    return int(priority)


@frozen
class TodoistPriority:
    priority: int = field(
        default=1,
        converter=to_int_disallow_float,
        validator=[validators.ge(1), validators.le(4)],
    )
