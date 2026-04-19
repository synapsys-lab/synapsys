"""
Utility: copy new EN docs to the PT i18n directory (without overwriting existing translations).
Run from the repo root: python website/sync_i18n.py
"""

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "website" / "docs"
DST = (
    REPO_ROOT / "website" / "i18n" / "pt" / "docusaurus-plugin-content-docs" / "current"
)

for src_file in SRC.rglob("*.md"):
    rel = src_file.relative_to(SRC)
    dst_file = DST / rel
    if not dst_file.exists():
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)
        print(f"Copied: {rel}")
