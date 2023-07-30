import pytest

from domain.platforms.todoist.priority import TodoistPriority


class TestTodoistPriority:
    @pytest.mark.unit
    def test_priority_can_be_created_with_int(self):
        priority = TodoistPriority(3)

        assert isinstance(priority.priority, int)
        assert priority.priority == 3

    @pytest.mark.unit
    def test_default_is_1(self):
        priority = TodoistPriority()

        assert isinstance(priority.priority, int)
        assert priority.priority == 1

    @pytest.mark.unit
    def test_minimum_is_1(self):
        # GIVEN
        with pytest.raises(ValueError) as excinfo:
            # WHEN
            TodoistPriority(0)

        # THEN
        assert "'priority' must be >= 1: 0" in str(excinfo.value)

    @pytest.mark.unit
    def test_maximum_is_4(self):
        # GIVEN
        with pytest.raises(ValueError) as excinfo:
            # WHEN
            TodoistPriority(5)

        # THEN
        assert "'priority' must be <= 4: 5" in str(excinfo.value)

    @pytest.mark.unit
    def test_string_converts_to_int(self):
        priority = TodoistPriority("3")

        assert isinstance(priority.priority, int)
        assert priority.priority == 3

    @pytest.mark.unit
    def test_floating_point_throws_exception(self):
        # GIVEN
        with pytest.raises(ValueError) as excinfo:
            # WHEN
            TodoistPriority(1.9)

        # THEN
        assert "priority must be an integer" in str(excinfo.value)
