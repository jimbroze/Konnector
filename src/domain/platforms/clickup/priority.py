from attrs import frozen, field, validators


@frozen
class ClickupPriority:
    """4 (low) to 1 (urgent). 3 is default"""

    priority: int = field(
        default=3, converter=int, validator=[validators.ge(1), validators.le(4)]
    )

    def to_int(self) -> int:
        return self.priority
