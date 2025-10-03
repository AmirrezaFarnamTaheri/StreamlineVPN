# Contributing

Contributions are welcome! Please follow these guidelines to contribute to the project.

## Development Setup

1.  **Fork the repository** and clone it to your local machine.
2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements-dev.txt
    ```
4.  **Set up pre-commit hooks:**
    ```bash
    pre-commit install
    ```

## Code Style

-   This project follows the [Black](https://github.com/psf/black) code style.
-   Use `isort` to sort imports.
-   Docstrings should follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#3.8-comments-and-docstrings).

## Submitting a Pull Request

1.  Create a new branch for your feature or bug fix.
2.  Write tests for your changes and ensure all existing tests pass.
3.  Ensure your code passes all pre-commit checks.
4.  Submit a pull request with a clear description of your changes.

## Reporting Bugs

-   Please open an issue on GitHub with a clear description of the bug, including steps to reproduce it.
-   Include any relevant logs or error messages.

Thank you for your contributions!