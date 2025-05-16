from pathlib import Path

from bondocs.diff import staged_diff, summarize


def test_staged_diff(temp_git_repo):
    """Test staged diff extraction."""
    # Create a new file
    new_file = Path(temp_git_repo.working_dir) / "test.py"
    new_file.write_text("print('test')")

    # Stage the file
    temp_git_repo.index.add(["test.py"])

    # Get the diff
    diff = staged_diff()
    assert "test.py" in diff
    assert "print('test')" in diff


def test_summarize(temp_git_repo):
    """Test diff summarization."""
    # Create and stage a file
    new_file = Path(temp_git_repo.working_dir) / "test.py"
    new_file.write_text("print('test')")
    temp_git_repo.index.add(["test.py"])

    # Get and summarize the diff
    diff = staged_diff()
    summary = summarize(diff)

    assert "ADD" in summary
    assert "test.py" in summary
    assert "print('test')" in summary
