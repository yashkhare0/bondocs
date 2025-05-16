import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init", "-q"])
    Path("README.md").write_text("# Project\n")
    subprocess.check_call(["git", "add", "README.md"])
    subprocess.check_call(["git", "commit", "-m", "init", "-q"])
    # monkey‑patch LLM to deterministic output
    monkeypatch.setenv("BONDOCS_MOCK", "1")
    yield tmp_path


def test_readme_patched(repo, monkeypatch):
    src = Path("src/app.py")
    src.parent.mkdir()
    src.write_text("print('hi')\n")
    subprocess.check_call(["git", "add", "src/app.py"])
    from bondocs.cli import run as bondocs_run

    monkeypatch.setenv("BONDOCS_MODEL", "mock")  # use stub
    bondocs_run()
    new_readme = Path("README.md").read_text()
    assert "src/app.py" in new_readme
