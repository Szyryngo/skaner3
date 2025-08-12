import pytest

def test_always_passes():
    """Przykładowy test: zawsze przechodzi."""
    assert True

def test_sum():
    """Test sumowania dwóch liczb."""
    a = 2
    b = 3
    assert a + b == 5

@pytest.mark.parametrize("x, y, expected", [
    (1, 1, 2),
    (2, 2, 4),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_parametrized_sum(x, y, expected):
    """Test parametryzowany."""
    assert x + y == expected
