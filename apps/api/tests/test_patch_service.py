from pathlib import Path

import pytest

from app.services.patch_service import PatchValidationError, validate_unified_diff


def test_rejects_path_traversal(tmp_path: Path) -> None:
    patch = "diff --git a/../secret b/../secret\n--- a/../secret\n+++ b/../secret\n@@ -0,0 +1 @@\n+x"
    with pytest.raises(PatchValidationError, match="Unsafe patch path"):
        validate_unified_diff(patch, tmp_path)


def test_accepts_focused_text_patch(tmp_path: Path) -> None:
    patch = "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new"
    assert validate_unified_diff(patch, tmp_path) == ["app.py"]
