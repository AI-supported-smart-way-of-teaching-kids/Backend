def test_basic_pass():
    if 1 != 1:
        raise AssertionError("Expected 1 to equal 1")
