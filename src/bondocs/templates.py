"""Template strings for Bondocs.

This module contains template strings for various files that Bondocs creates
during initialization.
"""

# Pre-commit config template
PRE_COMMIT_CONFIG = """default_language_version:
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

# Bondocs config template
BONDOCS_CONFIG = """# Bondocs configuration
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

# Default README template
DEFAULT_README = '''# Project Name

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
