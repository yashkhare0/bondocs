# Bondocs

> **Git‑native, LLM‑powered documentation guardrails.**
> Keep your `README.md` (and soon run‑books & changelogs) automatically in sync with every commit.

![PyPI](https://img.shields.io/pypi/v/bondocs) ![License](https://img.shields.io/github/license/KizunaUX/bondocs) ![CI](https://github.com/KizunaUX/bondocs/actions/workflows/ci.yml/badge.svg)

---

## ✨ Why Bondocs?

* **No more stale READMEs** – a pre‑commit hook watches your staged diff, summarises the changes, and asks an LLM to surgically patch the docs.
* **Runs locally or offline** – prefers a local [Ollama](https://ollama.ai) daemon; falls back to your configured provider (OpenAI, Anthropic, Azure, etc.).
* **Git‑native workflow** – output is a regular unified diff applied by `patch`, then auto‑staged. No databases, no portals.
* **Zero‑friction adoption** – add two lines to `.pre‑commit‑config.yaml`, install once, done.
* **Extensible** – the same engine will soon handle `CHANGELOG.md`, run‑books, and multi‑language translations.

---

## 🚀 Quick start

```bash
pipx install bondocs                  # or: poetry add --dev bondocs
pre‑commit install                    # installs local hooks
```

Add Bondocs to **`.pre‑commit‑config.yaml`**:

```yaml
default_language_version:
  python: python3

repos:
  - repo: https://github.com/KizunaUX/bondocs
    rev: v0.1.0
    hooks:
      - id: bondocs
        stages: [commit]
        language: system
        entry: bondocs run
        pass_filenames: false
```

Now make a code change and commit:

```bash
$ echo "print('bondocs')" > src/app.py
$ git add src/app.py
$ git commit -m "feat: add greeting script"
Bondocs: README.md updated and re‑staged ✨
[main abc1234] feat: add greeting script
 2 files changed, 6 insertions(+)
```

Your README now contains a new *Usage* snippet referencing `src/app.py` – automatically generated.

---

## 🖥️ CLI usage

```bash
bondocs init          # initialize project with necessary files
bondocs run           # patch README from staged diff
bondocs diff          # show proposed README patch, don't apply
bondocs show_config   # print effective configuration
bondocs changelog     # update CHANGELOG.md (experimental)
bondocs runbook       # update runbooks (experimental)
```

Run with `--help` for all options.

---

## 🔧 Configuration

### Environment Variables

Bondocs can be configured using environment variables. Create a `.env` file in your project root with the following variables:

```bash
# LLM Provider Configuration
# Choose one of: ollama, openai, anthropic, azure
BONDOCS_PROVIDER=ollama

# Fallback Provider (if primary provider is unavailable)
# Choose one of: openai, anthropic, azure
BONDOCS_FALLBACK_PROVIDER=openai

# Model Configuration
# For Ollama: e.g., mistral-small3.1:latest, mixtral:latest
# For OpenAI: e.g., gpt-3.5-turbo, gpt-4
# For Anthropic: e.g., claude-3-opus-20240229, claude-3-sonnet-20240229
# For Azure: Your deployment name
BONDOCS_MODEL=mistral-small3.1:latest

# API Configuration
# For Ollama: Custom API URL (default: http://localhost:11434)
API_URL=http://localhost:11434

# API Keys (required for cloud providers)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
AZURE_AI_API_KEY=your-azure-api-key
```

### Configuration File

The package can also be configured using a `.bondocs.toml` file:

| Source | Key                      | Default               | Description                                |
| ------ | ------------------------ | --------------------- | ------------------------------------------ |
| Env    | `BONDOCS_PROVIDER`       | `ollama`              | Primary LLM provider                       |
| Env    | `BONDOCS_FALLBACK_PROVIDER` | `openai`           | Fallback provider if primary unavailable   |
| Env    | `BONDOCS_MODEL`          | `mistral-small3.1:latest` | Model name for provider                |
| Env    | `OPENAI_API_KEY`         | –                     | OpenAI key when using OpenAI provider      |
| Env    | `ANTHROPIC_API_KEY`      | –                     | Anthropic key when using Anthropic provider|
| Env    | `AZURE_AI_API_KEY`       | –                     | Azure key when using Azure provider        |
| TOML   | `provider`               | `ollama`              | Primary LLM provider                       |
| TOML   | `fallback_provider`      | `openai`              | Fallback provider if primary unavailable   |
| TOML   | `model`                  | same as env           | Override model per‑repo                    |
| TOML   | `max_tokens`             | `1024`                | Response size cap                          |

Example `.bondocs.toml`:

```toml
provider = "ollama"           # use local Ollama
fallback_provider = "openai"  # fall back to OpenAI if Ollama unavailable
model = "mixtral"             # use local Mixtral on Ollama
max_tokens = 800              # shorter patches
```

The provided example `.bondocs.toml` includes additional configuration options for documentation sections, prompts, ignore patterns, and formatting.

---

## 🛠️ Architecture

```bash
                      +----------------+
    git diff          | git/diff.py    |  summarize
  --------------->    |                +----+
                      +----------------+    |
                                            | prompt
                                            v
  +------------------+    +----------------+   +---------------+
  | core/errors.py   |--->| providers/llm  |-->| LLM backend   |
  | error handling   |    | provider mgmt  |   | (Ollama/cloud)|
  +------------------+    +----------------+   +---------------+
                                            |
                          diff patch        v
                      +-------------------+ +---------------+
                      | document/patcher  |->|   patch(1)   |
                      +-------------------+ +---------------+
```

* **git/diff.py** – extracts staged diff, condenses to bullet summary
* **providers/llm.py** – manages LLM providers with intelligent fallback
* **document/patcher.py** – applies patches with proper validation
* **core/errors.py** – provides centralized error handling throughout

The modular architecture enables:
- Clear separation of concerns
- Easy extension with new LLM providers
- Type-safe interfaces via protocols
- Consistent error handling patterns

---

## 📦 Package structure

```bash
src/bondocs/
├── core/
│   ├── __init__.py    # Core exports
│   ├── config.py      # Configuration management
│   ├── errors.py      # Error system
│   └── interfaces.py  # Protocols and interfaces
├── document/
│   ├── __init__.py    # Document exports
│   ├── document.py    # Document management
│   ├── changelog.py   # Changelog generation
│   ├── patcher.py     # Patch utilities
│   └── runbook.py     # Runbook management
├── git/
│   ├── __init__.py    # Git exports
│   ├── git.py         # Git operations
│   └── diff.py        # Diff utilities
├── providers/
│   ├── __init__.py    # Provider exports
│   ├── llm.py         # LLM backend abstraction
│   └── prompt.py      # Prompt management
├── utils/
│   ├── __init__.py    # Utility exports
│   └── templates.py   # Template rendering
└── cli.py             # Command-line interface
```

The codebase follows a modular structure with clear separation of concerns:
- **core**: Contains foundational components used throughout the application
- **document**: Handles all document operations and patching
- **git**: Manages Git interactions and diff processing
- **providers**: Controls LLM integration with various backends
- **utils**: Houses utility functions and templates

See **`CONTRIBUTING.md`** for dev setup and architectural decisions.

### Import Conventions

Bondocs follows these import conventions:

```python
# Import from a module within the same package
from .errors import ConfigError

# Import from another package
from bondocs.core.errors import handle_errors, GitError
from bondocs.document import doc_manager
from bondocs.providers import llm
```

When contributing, ensure you use the package name (not src.bondocs) in imports for consistent behavior.

---

## 🛡️ Error Handling

Bondocs uses a centralized error handling system to provide consistent error reporting and recovery throughout the application. All errors inherit from a common `BondocsError` base class.

### Error Handling Decorators

```python
from bondocs.core.errors import handle_errors, GitError

@handle_errors(GitError, severity=ErrorSeverity.ERROR)
def get_commit_message():
    # This function will automatically handle GitError exceptions
    # and log them with ERROR severity
    return git.get_last_commit_message()
```

### Safe Execution Pattern

```python
from bondocs.core.errors import safe_execution

@safe_execution("Failed to update changelog", exit_on_error=False)
def update_changelog(commit_message):
    # This function will display a user-friendly error message
    # if the operation fails
    return changelog_generator.generate(commit_message)
```

### Severity Levels

Bondocs errors are categorized by severity:
- `INFO`: Information only, no action required
- `WARNING`: Potential issue, operation continues
- `ERROR`: Operation failed, but program continues
- `CRITICAL`: Fatal error requiring program termination

### Error Types

The following error types are available:
- `BondocsError`: Base exception for all errors
- `ConfigError`: Configuration-related errors
- `GitError`: Git operation errors
- `LLMError`: Language model errors
- `PatchError`: Patch application errors
- `DocumentError`: Document operation errors
- `RunbookError`: Runbook operation errors
- `ChangelogError`: Changelog operation errors

For advanced error handling patterns and implementation details, refer to the `errors.py` module.

---

## 🧪 Testing

Bondocs ships with **pytest** suites that spin up a fake git repo via `pytest-git`.
The LLM call is stubbed when `BONDOCS_MOCK=1`, yielding deterministic patches.
Run tests with:

```bash
poetry run pytest
```

CI pipeline lives in [`.github/workflows/ci.yml`](.github/workflows/ci.yml) and checks formatting (Black, Ruff) plus unit tests.

---

## 🛣️ Roadmap

### Completed
* [x] Project restructuring with modular architecture
* [x] Centralized error handling system
* [x] Standardized import conventions
* [x] Type hints and static analysis support

### In Development
* [ ] Enhanced changelog generation (`CHANGELOG.md`)
* [ ] Improved run‑book support (detect `docs/runbook/*.md`)
* [ ] Doc‑coverage badge & CI gate

### Future Plans
* [ ] VS Code preview extension
* [ ] Multi‑language translation add‑on
* [ ] Compliance‑pack PDF export
* [ ] Error telemetry and reporting system
* [ ] Detailed troubleshooting guides

Track progress in the **Issues** tab.

---

## 🤝 Contributing

1. Fork & clone the repo
2. `poetry install`
3. `make precommit` – sets up local hooks
4. Create your feature branch (`git checkout -b feat/awesome`)
5. Commit patches; Bondocs will auto‑update this README for you 😄
6. Push and open a PR

Please read the [Code of Conduct](CODE_OF_CONDUCT.md) first.

### Code Formatting

This project uses Black and Ruff for code formatting and linting. They're configured to run automatically as pre-commit hooks.

To set up the pre-commit hooks and format all files:

**On Linux/macOS:**

```bash
# Make the script executable if needed
chmod +x format.sh
./format.sh
```

**On Windows:**

```cmd
format.bat
```

**Using Make (if available):**

```bash
make format      # Format code
make lint        # Run linters
make precommit   # Install pre-commit hooks
make test        # Run tests
```

Alternatively, you can run the commands manually:

```bash
# Install pre-commit hooks
pre-commit install

# Run formatters directly
black .
ruff --fix .
```

---

## 📄 License

Bondocs is MIT‑licensed. See [LICENSE](LICENSE) for full text.

---

## 💬 Support & Chat

Questions? Ideas? Join our Discord (#bondocs) or open a GitHub Discussion.

---

> Made with ❤️.
