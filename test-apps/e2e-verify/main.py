"""
CLI calculator application.

Usage: python main.py <num1> <operator> <num2>

Supported operators: +, -, *
"""

import sys
import calculator


# Operator mapping to calculator functions
OPERATORS = {
    '+': calculator.add,
    '-': calculator.subtract,
    '*': calculator.multiply
}


def validate_argument_count(args):
    """
    Validate that exactly 3 arguments are provided.

    Args:
        args: List of command line arguments (excluding program name)

    Returns:
        tuple: (is_valid, error_message or None)
    """
    if len(args) < 3:
        return False, "Error: Missing arguments. Usage: python main.py <num1> <operator> <num2>"
    if len(args) > 3:
        return False, "Error: Too many arguments. Usage: python main.py <num1> <operator> <num2>"
    return True, None


def validate_number(value, position):
    """
    Validate that a value can be converted to a number.

    Args:
        value: String value to validate
        position: Description of which argument (for error message)

    Returns:
        tuple: (is_valid, parsed_number or None, error_message or None)
    """
    try:
        return True, float(value), None
    except ValueError:
        return False, None, f"Error: Invalid number '{value}' for {position}"


def validate_operator(op):
    """
    Validate that the operator is supported.

    Args:
        op: Operator string to validate

    Returns:
        tuple: (is_valid, error_message or None)
    """
    if op not in OPERATORS:
        return False, f"Error: Invalid operator '{op}'. Use +, -, or *"
    return True, None


def main():
    """Main entry point for the CLI calculator."""
    args = sys.argv[1:]

    # Validate argument count
    valid, error = validate_argument_count(args)
    if not valid:
        print(error)
        sys.exit(1)

    num1_str, operator, num2_str = args

    # Validate first number
    valid, num1, error = validate_number(num1_str, "first argument")
    if not valid:
        print(error)
        sys.exit(1)

    # Validate operator
    valid, error = validate_operator(operator)
    if not valid:
        print(error)
        sys.exit(1)

    # Validate second number
    valid, num2, error = validate_number(num2_str, "second argument")
    if not valid:
        print(error)
        sys.exit(1)

    # Perform calculation
    operation = OPERATORS[operator]
    result = operation(num1, num2)

    # Format output - show integer if result is whole number, otherwise float
    if result == int(result):
        print(int(result))
    else:
        print(result)

    sys.exit(0)


if __name__ == "__main__":
    main()
