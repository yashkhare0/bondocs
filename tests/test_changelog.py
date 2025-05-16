from pathlib import Path

from bondocs.changelog import get_changelog_path, update_changelog


def test_changelog_creation(temp_git_repo, mock_llm_response):
    """Test changelog creation and updates."""
    # Create a new file
    new_file = Path(temp_git_repo.working_dir) / "test.py"
    new_file.write_text("print('test')")
    temp_git_repo.index.add(["test.py"])

    # Update changelog
    changelog_path = get_changelog_path(temp_git_repo.working_dir)
    update_changelog("feat: add test file")

    # Check if changelog was created and updated
    assert changelog_path.exists()
    content = changelog_path.read_text()
    assert "Changelog" in content
    assert "Unreleased" in content
    assert "Added new feature" in content


def test_changelog_format(temp_git_repo, mock_llm_response):
    """Test changelog format and structure."""
    # Create and stage multiple changes
    new_file = Path(temp_git_repo.working_dir) / "test.py"
    new_file.write_text("print('test')")
    temp_git_repo.index.add(["test.py"])

    # Update changelog
    update_changelog("feat: add test file")

    # Check format
    content = get_changelog_path(temp_git_repo.working_dir).read_text()
    assert "# Changelog" in content
    assert "## [Unreleased]" in content
    assert "- " in content  # Bullet points
