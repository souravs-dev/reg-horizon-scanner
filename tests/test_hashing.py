from app.hashing import content_hash


def test_same_input_same_hash():
    assert content_hash("a", "b", "c") == content_hash("a", "b", "c")


def test_different_input_different_hash():
    assert content_hash("a", "b", "c") != content_hash("a", "b", "d")


def test_field_boundary_matters():
    # "ab", "c" must not hash the same as "a", "bc"
    assert content_hash("ab", "c") != content_hash("a", "bc")
