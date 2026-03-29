# Type hints
Always add type hints to your Python code. This helps with readability and allows type checkers to catch potential bugs. For example, instead of writing:

```python
def add(a, b):
    return a + b
```
You should write:
```python
def add(a: int, b: int) -> int:
    return a + b
```

# Code formatting
After the code has been modified and the request from the user has been fulfilled, run `ty` and `ruff` to format the code and check for linting and typing errors:

```bash
uv run ty check
uv run ruff format
```
If either of these commands reports errors, fix them and run the command again until there are no errors.
