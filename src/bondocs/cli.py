"""Command-line interface for Bondocs.

Provides commands for initializing and running Bondocs.
"""

import subprocess
import sys
from pathlib import Path

import click
from rich import print

from .changelog import update_changelog
from .config import load
from .diff import staged_diff, summarize
from .patcher import apply_patch, generate_patch
from .runbook import update_runbooks


@click.group()
def app():
    """Bondocs – keep your README in sync automatically."""


@app.command()
def init():
    """Initialize bondocs in the current project."""
    # Check if we're in a git repository
    try:
        subprocess.check_call(
            ["git", "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print("[red]Error: Not a git repository. Please run 'git init' first.[/]")
        sys.exit(1)

    # Create .pre-commit-config.yaml if it doesn't exist
    precommit_path = Path(".pre-commit-config.yaml")
    if not precommit_path.exists():
        precommit_content = """default_language_version:
  python: python3

repos:
  - repo: https://github.com/your-org/bondocs
    rev: v0.1.0
    hooks:
      - id: bondocs
        stages: [commit]
        language: system
        entry: bondocs run
        pass_filenames: false
"""
        precommit_path.write_text(precommit_content)
        print("[green]Created .pre-commit-config.yaml[/]")
    else:
        print("[yellow]Warning: .pre-commit-config.yaml already exists[/]")

    # Create .bondocs.toml if it doesn't exist
    bondocs_path = Path(".bondocs.toml")
    if not bondocs_path.exists():
        bondocs_content = """# Bondocs configuration
# LLM Configuration
model = "gpt-3.5-turbo"  # or "mixtral" if using Ollama
max_tokens = 1024        # Maximum tokens for LLM response
temperature = 0.2        # LLM temperature (0.0 to 1.0)

# Documentation Settings
[documentation]
# Files to monitor for changes
watch_files = [
    "src/**/*.py",      # Python source files
    "tests/**/*.py",    # Test files
    "*.md"              # Markdown files
]

# Sections to update in README
sections = [
    "Installation",
    "Usage",
    "API Reference",
    "Examples"
]

# Custom prompt templates
[prompts]
# Custom prompt for specific file types
python = \"\"\"
Update the documentation to reflect changes in the Python code.
Focus on function signatures, parameters, and return types.
\"\"\"

# Ignore patterns for files
[ignore]
patterns = [
    "*.pyc",
    "__pycache__",
    ".git/*",
    "venv/*"
]

# Output formatting
[format]
# Maximum line length for generated documentation
max_line_length = 88
# Whether to use code blocks for examples
use_code_blocks = true
# Whether to include type hints in documentation
include_type_hints = true
"""
        bondocs_path.write_text(bondocs_content)
        print("[green]Created .bondocs.toml[/]")
    else:
        print("[yellow]Warning: .bondocs.toml already exists[/]")

    # Create README.md if it doesn't exist
    readme_path = Path("README.md")
    if not readme_path.exists():
        readme_content = '''# Project Name

[![PyPI version](https://badge.fury.io/py/your-package-name.svg)]
(https://badge.fury.io/py/your-package-name)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]
(https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)]
(https://github.com/psf/black)

Brief description of your project - what it does and why it's useful.

## ✨ Features

- **Feature 1**: Description of the first major feature
- **Feature 2**: Description of the second major feature
- **Feature 3**: Description of the third major feature

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

```bash
# Install from PyPI
pip install your-package-name

# Or install from source
git clone https://github.com/your-username/your-repo.git
cd your-repo
pip install -e .
```

## 📖 Usage

### Basic Usage

```python
from your_package import YourClass

# Create an instance
instance = YourClass()

# Use the instance
result = instance.do_something()
```

### Advanced Usage

```python
# Example of advanced usage
from your_package import advanced_feature

result = advanced_feature(
    param1="value1",
    param2="value2"
)
```

## 🔧 Configuration

The package can be configured using environment variables or a configuration file:

```python
# Using environment variables
export YOUR_PACKAGE_SETTING="value"

# Using configuration file
from your_package import config
config.load("config.yaml")
```

## 📚 API Reference

### Main Classes

#### `YourClass`

The main class of the package.

```python
class YourClass:
    def __init__(self, param1: str, param2: int = 0):
        """
        Initialize the class.

        Args:
            param1: Description of param1
            param2: Description of param2
        """
        pass
```

### Functions

#### `do_something()`

Description of what the function does.

```python
def do_something(param1: str) -> bool:
    """
    Do something with the input.

    Args:
        param1: Description of param1

    Returns:
        bool: Description of return value

    Raises:
        ValueError: Description of when this error occurs
    """
    pass
```

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests
pytest
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- List any credits, inspirations, etc.

## 📞 Support

- GitHub Issues: [Create an issue](https://github.com/your-username/your-repo/issues)
- Email: your-email@example.com
- Discord: [Join our server](https://discord.gg/your-server)

---

Made with ❤️ by [Your Name](https://github.com/your-username)
'''  # noqa: E501
        readme_path.write_text(readme_content)
        print("[green]Created README.md[/]")
    else:
        print("[yellow]Warning: README.md already exists[/]")

    # Install pre-commit hooks
    try:
        subprocess.check_call(
            ["pre-commit", "install"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("[green]Installed pre-commit hooks[/]")
    except subprocess.CalledProcessError:
        print(
            "[yellow]Warning: Failed to install pre-commit hooks. "
            "Please install pre-commit first.[/]"
        )
        print("Run: pip install pre-commit")

    print("\n[bold]Bondocs has been initialized![/]")
    print("Next steps:")
    print("1. Review and customize .bondocs.toml if needed")
    print("2. Make sure pre-commit is installed: pip install pre-commit")
    print("3. Start making changes - Bondocs will keep your README in sync!")


@app.command()
def run():
    """Patch README from staged diff."""
    diff = staged_diff()
    if not diff.strip():
        sys.exit(0)
    summary = summarize(diff)
    patch = generate_patch(summary)
    if not patch.strip():
        print("[yellow]Bondocs: model returned empty patch[/]")
        return
    if apply_patch(patch):
        subprocess.check_call(["git", "add", "README.md"])
        print("[green]Bondocs: README.md updated and re‑staged[/]")
    else:
        print("[red]Bondocs: failed to apply patch[/]")


@app.command()
def changelog():
    """Update CHANGELOG.md based on staged changes."""
    if update_changelog(""):
        subprocess.check_call(["git", "add", "CHANGELOG.md"])
        print("[green]Bondocs: CHANGELOG.md updated and re‑staged[/]")
    else:
        print("[red]Bondocs: failed to update changelog[/]")


@app.command()
def runbook():
    """Update runbooks based on staged changes."""
    if update_runbooks():
        # Add all runbook files
        runbook_dir = Path(".") / "docs" / "runbook"
        if runbook_dir.exists():
            subprocess.check_call(["git", "add", "docs/runbook/*.md"])
        print("[green]Bondocs: Runbooks updated and re‑staged[/]")
    else:
        print("[red]Bondocs: failed to update runbooks[/]")


@app.command()
def diff():
    """Show proposed README patch, don't apply."""
    diff = staged_diff()
    if not diff.strip():
        print("[yellow]Bondocs: no staged changes[/]")
        return
    summary = summarize(diff)
    patch = generate_patch(summary)
    if not patch.strip():
        print("[yellow]Bondocs: model returned empty patch[/]")
        return
    print(patch)


@app.command()
def config():
    """Print effective configuration."""
    config = load()
    print("[bold]Effective configuration:[/]")
    for key, value in config.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    app()
