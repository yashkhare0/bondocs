"""Document management for Bondocs.

This package contains modules for managing documentation files.
"""

from bondocs.document.changelog import update_changelog
from bondocs.document.document import DocumentManager, doc_manager
from bondocs.document.patcher import apply_patch, generate_readme_patch
from bondocs.document.runbook import update_runbooks
