import tempfile
from pathlib import Path

import pytest
from git import Repo


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = Repo.init(temp_dir)

        # Create initial README.md
        readme_path = Path(temp_dir) / "README.md"
        readme_path.write_text("# Test Project\n\nInitial README content.")

        # Create initial commit
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")

        # Create a test branch
        repo.create_head("test-branch")

        yield repo

        # Cleanup happens automatically when temp_dir is removed


@pytest.fixture
def mock_llm_response(monkeypatch):
    """Mock LLM responses for testing."""

    def mock_chat(prompt: str) -> str:
        if "README.md" in prompt:
            return """--- a/README.md
+++ b/README.md
@@ -1,3 +1,4 @@
 # Test Project

 Initial README content.
+Added new feature.
"""
        elif "CHANGELOG.md" in prompt:
            return """--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -0,0 +1,4 @@
+# Changelog
+
+## [Unreleased]
+- Added new feature
"""
        return ""

    monkeypatch.setenv("BONDOCS_MOCK", "1")
    monkeypatch.setattr("bondocs.llm.LLMBackend.chat", mock_chat)


@pytest.fixture
def sample_runbook():
    """Create a sample runbook for testing."""
    return """# Sample Runbook

## Overview
This is a test runbook.

## Steps
1. First step
2. Second step
"""
