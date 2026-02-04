"""
Calculator module with basic arithmetic operations.

This module provides pure functions for add, subtract, and multiply operations.
No input validation is performed - functions expect numeric inputs.
"""


def add(a, b):
    """
    Adds two numbers.

    Args:
        a: First number (int or float)
        b: Second number (int or float)

    Returns:
        The sum of a and b
    """
    return a + b


def subtract(a, b):
    """
    Subtracts b from a.

    Args:
        a: First number (int or float)
        b: Second number to subtract (int or float)

    Returns:
        The difference (a - b)
    """
    return a - b


def multiply(a, b):
    """
    Multiplies two numbers.

    Args:
        a: First number (int or float)
        b: Second number (int or float)

    Returns:
        The product of a and b
    """
    return a * b
