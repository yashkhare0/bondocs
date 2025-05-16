# Bondocs

> **Git‑native, LLM‑powered documentation guardrails.**
> Keep your `README.md` (and soon run‑books & changelogs) automatically in sync with every commit.

![PyPI](https://img.shields.io/pypi/v/bondocs) ![License](https://img.shields.io/github/license/your‑org/bondocs) ![CI](https://github.com/your‑org/bondocs/actions/workflows/ci.yml/badge.svg)

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
  - repo: https://github.com/your‑org/bondocs
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
bondocs run           # patch README from staged diff
bondocs diff          # show proposed README patch, don't apply
bondocs config        # print effective configuration
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

---

## 🛠️ Architecture

```bash
            +----------------+
  git diff  |   diff.py      |  summarize
------------>   bullets      +----+
            +----------------+    |
                                      | prompt
                                      v
            +----------------+   +---------------+
            |  llm.py        |-->|  LLM backend   |
            |  backend pick  |   |  (Ollama/provider)
            +----------------+   +---------------+
                                      |
                    diff patch        v
            +----------------+   +---------------+
            | patcher.py     |-->|   patch(1)    |
            +----------------+   +---------------+
```

* **diff.py** – extracts staged diff, condenses to bullet summary.
* **llm.py** – picks Ollama if `localhost:11434` responds; else falls back to the configured fallback provider.
* **patcher.py** – renders Jinja prompt, calls LLM, applies unified diff via `patch -p0`.

---

## 📦 Package structure

```bash
src/bondocs/
├── cli.py         # Click commands
├── diff.py        # Staged diff helpers
├── llm.py         # Backend abstraction
├── patcher.py     # Prompt + patch
├── prompt.md      # Jinja template
└── config.py      # Env & TOML loader
```

See **`CONTRIBUTING.md`** for dev setup and architectural decisions.

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

* [ ] Changelog autogeneration (`CHANGELOG.md`)
* [ ] Run‑book support (detect `docs/runbook/*.md`)
* [ ] Doc‑coverage badge & CI gate
* [ ] VS Code preview extension
* [ ] Multi‑language translation add‑on
* [ ] Compliance‑pack PDF export

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

# Run all pre-commit hooks on all files
pre-commit run --all-files
```

---

## 📄 License

Bondocs is MIT‑licensed. See [LICENSE](LICENSE) for full text.

---

## 💬 Support & Chat

Questions? Ideas? Join our Discord (#bondocs) or open a GitHub Discussion.

---

> Made with ❤️.
