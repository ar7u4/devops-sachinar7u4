def add(a: int, b: int) -> int:
    """Returns the sum of a and b."""
    return a + b


def multiply(a: int, b: int) -> int:
    """Returns the product of a and b."""
    return a * b


def subtract(a: int, b: int) -> int:
    """Returns the difference of a and b."""
    return a - b


if __name__ == "__main__":
    number1 = 50
    number2 = 100

    result = add(number1, number2)
    result2 = multiply(number1, number2)
    result3 = subtract(number1, number2)

    print("The sum of", number1, "and", number2, "is:", result)
    print("The product of", number1, "and", number2, "is:", result2)
    print("The difference of", number1, "and", number2, "is:", result3)
