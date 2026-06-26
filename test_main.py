from main import add, multiply, subtract


def test_add():
    assert add(5, 5) == 10
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_multiply():
    assert multiply(5, 5) == 25
    assert multiply(-1, 5) == -5
    assert multiply(0, 100) == 0


def test_subtract():
    assert subtract(10, 5) == 5
    assert subtract(-1, -1) == 0
    assert subtract(0, 5) == -5
