from konnector.todoist import convert_time_to


def test_time_conversion_to_RFC():
    assert convert_time_to(1675209600000, False) == ("2023-02-01", False)
    assert convert_time_to(1672621323000, True) == ("2023-01-02T01:02:03", True)
