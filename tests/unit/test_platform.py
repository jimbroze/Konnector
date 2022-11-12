def test_new_platform(new_platform):
    """
    GIVEN a platform model
    WHEN a new platform is created
    THEN check the propertyMappings are defined correctly
    """
    assert new_platform.propertyMappings["name"] == "name"
    assert new_platform.propertyMappings["description"] == "description"
    assert new_platform.propertyMappings["priority"] == "priority"
    assert new_platform.propertyMappings["due_date"] == "due_date"
