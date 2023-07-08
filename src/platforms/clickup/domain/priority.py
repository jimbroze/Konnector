from attrs import frozen, field


@frozen
class ClickupPriority:
    priority: int = field(default=3, converter=int)

    @priority.validator
    def priority_between_values(self, attribute, value):
        if not 0 < value <= 4:
            raise ValueError("Value should be between 0 and 4 inclusive")

    def to_int(self) -> int:
        return self.priority
