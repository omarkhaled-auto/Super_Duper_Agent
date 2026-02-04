# Calculator Module Specification

## Overview
Build a Python calculator module with basic arithmetic operations and a command-line interface.

## Requirements

### Core Module (`calculator.py`)
1. Implement an `add(a, b)` function that returns the sum of two numbers
2. Implement a `subtract(a, b)` function that returns the difference of two numbers
3. Implement a `multiply(a, b)` function that returns the product of two numbers

### CLI (`main.py`)
4. Read two numbers and an operator (+, -, *) from `sys.argv`
5. Print the result to stdout in the format: `Result: <value>`
6. Display a usage message if incorrect arguments are provided

### Validation
7. Validate that inputs are valid numbers (not strings)
8. Validate that the operator is one of +, -, *
