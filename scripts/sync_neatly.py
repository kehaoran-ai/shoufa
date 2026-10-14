#!/usr/bin/env python3
"""Copy the Neatly engine into Shoufa so beginners install one thing.

    python3 scripts/sync_neatly.py [path/to/neatly/skills/neatly]

Neatly (github.com/kehaoran-ai/neatly) is the source of truth for layouts,
design systems, make.py and check.py. Never edit skills/shoufa/neatly by hand;
change Neatly and run this again.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT.parent / "neatly" / "skills" / "neatly").resolve()
DST = ROOT / "skills" / "shoufa" / "neatly"

if not (SRC / "layouts").is_dir():
    sys.exit(f"Neatly not found at {SRC}")
if DST.exists():
    shutil.rmtree(DST)
(DST / "scripts").mkdir(parents=True)
(DST / "reference").mkdir()
for d in ("layouts", "systems"):
    shutil.copytree(SRC / d, DST / d)
for f in ("scripts/make.py", "scripts/check.py", "reference/components.md", "neatly.css", "neatly.js"):
    shutil.copy2(SRC / f, DST / f)
print(f"synced Neatly from {SRC}")
