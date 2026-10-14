#!/usr/bin/env python3
"""Assemble the demo site into dist/ (deployed to shoufa.kehaoran.ai).

    python3 scripts/site.py
    npx wrangler pages deploy dist --project-name shoufa --branch main

dist/ holds the front page, the finished examples (pages and working tools),
and the start form in demo mode: every sample it shows is pre-built, so the
look and colour switches work without an agent behind them.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "shoufa"
DIST = ROOT / "dist"
sys.path.insert(0, str(SKILL / "scripts"))
import ask  # noqa: E402

MAKE = [sys.executable, str(SKILL / "neatly" / "scripts" / "make.py")]

shutil.rmtree(DIST, ignore_errors=True)
tmp = DIST / ".build"
tmp.mkdir(parents=True)

# Front page, built with the skill's own mono look.
subprocess.run(MAKE + ["landing", str(ROOT / "site" / "body.html"), str(DIST / "index.html"),
                       "--system", ask.system_css("mono", tmp), "--lang", "en",
                       "--title", "Shoufa: your first product, live, without code"], check=True)
shutil.copytree(ROOT / "site" / "img", DIST / "img")
shutil.copytree(ROOT / "examples", DIST / "examples")

# The start form in demo mode, with its styles and thumbnails.
(DIST / "forms").mkdir()
shutil.copy(SKILL / "forms" / "forms.css", DIST / "forms" / "forms.css")
shutil.copytree(SKILL / "forms" / "thumbs", DIST / "forms" / "thumbs")
(DIST / "try").mkdir()
form = (SKILL / "forms" / "start.html").read_text(encoding="utf-8")
form = form.replace("</head>", "<script>window.SHOUFA_STATIC = true;</script>\n</head>", 1)
(DIST / "try" / "index.html").write_text(form, encoding="utf-8")

# Every sample the form can show: kind x look x language.
(DIST / "samples").mkdir()
for kind in ("landing", "personal", "app"):
    for lang in ("zh", "en"):
        for look in ask.SYSTEMS:
            subprocess.run(MAKE + [ask.neatly_layout(kind), str(SKILL / "samples" / f"{kind}-{lang}.html"),
                                   str(DIST / "samples" / f"{kind}-{lang}-{look}.html"),
                                   "--system", ask.system_css(look, tmp), "--no-check",
                                   "--lang", "zh-CN" if lang == "zh" else "en",
                                   "--title", ask.SAMPLE_TITLES[(kind, lang)]],
                           check=True, capture_output=True)

shutil.rmtree(tmp)
for f in sorted(DIST.rglob("*")):
    if f.is_file() and f.suffix == ".html":
        print(f.relative_to(DIST))
