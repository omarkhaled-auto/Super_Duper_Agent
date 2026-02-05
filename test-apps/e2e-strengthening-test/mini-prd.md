# Mini E2E Test PRD

A minimal PRD to verify E2E strengthening fixes work correctly.

## Milestone 1: Greeting Module
Create a simple Python greeting module.

### Requirements
- Create `greet.py` with a `hello(name)` function that returns "Hello, {name}!"
- The function should handle empty names by returning "Hello, World!"

## Milestone 2: CLI Interface
Create a command-line interface for the greeting module.

### Requirements
- Create `main.py` that imports and uses `hello()` from greet.py
- Accept a name from command line arguments (sys.argv)
- Print the greeting to stdout
- Show usage message if no name provided
