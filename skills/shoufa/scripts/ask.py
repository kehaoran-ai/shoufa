#!/usr/bin/env python3
"""Shoufa's local helper: shows a form in the browser and hands the answers back to the agent.

The person never copies or pastes anything. The agent opens a form, waits, and gets
JSON back on stdout. Everything stays on this computer (127.0.0.1 only).

    python3 ask.py open start   --project DIR     # open the start form (starts the helper if needed)
    python3 ask.py wait start   --project DIR     # block until the form is submitted, print the answers
    python3 ask.py open preview --project DIR     # show the built page with "looks good / change" buttons
    python3 ask.py build --project DIR --layout personal --system soft [--accent e4572e] [--title "..."]
                                                  # DIR/body.html -> DIR/site/index.html via Neatly, then check
    python3 ask.py status "Uploading your page" --project DIR [--url URL] [--done] [--phase upload]
    python3 ask.py stop         --project DIR     # shut the helper down

`wait` gives up after --timeout seconds (default 540) with exit code 2 and the line
STILL_WAITING. Run it again; the form and the helper keep running in the meantime.

DIR is the person's project folder. Shoufa writes:
    DIR/body.html     the page content the agent wrote (inside <body>)
    DIR/.shoufa/      helper state, answers-<form>.json, page.json, status.json
    DIR/site/         the website (index.html and assets/)
"""
import argparse
import base64
import json
import os
import re
import socket
import subprocess
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
FORMS = SKILL / "forms"
MAKE = SKILL / "neatly" / "scripts" / "make.py"
SYSTEMS = ("mono", "blueprint", "soft")  # looks on the shadcn/ui base, see systems/
SAMPLE_TITLES = {("personal", "zh"): "林小雨", ("landing", "zh"): "接力", ("personal", "en"): "Mia Chen", ("landing", "en"): "Relay", ("app", "zh"): "专注岛", ("app", "en"): "Focus Island"}
FORM_NAMES = {"start", "preview", "deploy"}
MAX_BODY = 25 * 1024 * 1024
IMAGE_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif", "image/svg+xml": ".svg"}


def system_css(name, sdir):
    """shadcn base + one look, as a single file for make.py. @import must stay on top."""
    look = (SKILL / "systems" / f"{name}.css").read_text(encoding="utf-8")
    imports = "\n".join(l for l in look.splitlines() if l.startswith("@import"))
    rest = "\n".join(l for l in look.splitlines() if not l.startswith("@import"))
    base = (SKILL / "systems" / "shadcn.css").read_text(encoding="utf-8")
    parts = (SKILL / "systems" / "app.css").read_text(encoding="utf-8")
    out = sdir / f"system-{name}.css"
    out.write_text(imports + "\n" + base + "\n" + rest + "\n" + parts + "\n", encoding="utf-8")
    return str(out)


def neatly_layout(layout):
    """A tool (app) has no Neatly layout of its own: its body replaces a landing page's."""
    return "landing" if layout == "app" else layout


def state_dir(project):
    d = Path(project).expanduser().resolve() / ".shoufa"
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(path, data):
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def alive(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------- server
def make_handler(project):
    root = Path(project).expanduser().resolve()
    sdir = state_dir(root)
    site = root / "site"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, body, ctype="text/plain; charset=utf-8"):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def file(self, path):
            ext = path.suffix.lower()
            ctype = {".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript",
                     ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png",
                     ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
                     ".ico": "image/x-icon"}.get(ext, "application/octet-stream")
            self.send(200, path.read_bytes(), ctype)

        def do_GET(self):
            u = urlparse(self.path)
            p = u.path
            if p in ("/", ""):
                return self.redirect("/form/start")
            m = re.fullmatch(r"/form/([a-z]+)", p)
            if m and m.group(1) in FORM_NAMES:
                return self.file(FORMS / f"{m.group(1)}.html")
            if p.startswith("/forms/"):
                target = (FORMS / p[len("/forms/"):]).resolve()
                if FORMS in target.parents and target.is_file():
                    return self.file(target)
            if p == "/api/status":
                return self.send(200, json.dumps(read_json(sdir / "status.json", {})), "application/json")
            if p == "/api/meta":
                meta = read_json(sdir / "meta.json", {})
                meta.update(read_json(sdir / "page.json", {}))
                return self.send(200, json.dumps(meta), "application/json")
            m = re.fullmatch(r"/sample/(personal|landing|app)/([a-z]+)", p)
            if m and m.group(2) in SYSTEMS:
                # A finished sample page in the chosen system, for the style picker on the start form.
                q = parse_qs(u.query)
                lang = "en" if (q.get("lang") or ["zh"])[0] == "en" else "zh"
                accent = (q.get("accent") or [""])[0].lstrip("#")
                out = sdir / f"sample-{m.group(1)}-{lang}-{m.group(2)}.html"
                args = [sys.executable, str(MAKE), neatly_layout(m.group(1)), str(SKILL / "samples" / f"{m.group(1)}-{lang}.html"), str(out),
                        "--system", system_css(m.group(2), sdir), "--no-check", "--lang", "zh-CN" if lang == "zh" else "en",
                        "--title", SAMPLE_TITLES[(m.group(1), lang)]]
                if accent and re.fullmatch(r"[0-9a-fA-F]{3,8}", accent):
                    args += ["--accent", accent]
                r = subprocess.run(args, capture_output=True, text=True)
                if r.returncode != 0 or not out.is_file():
                    return self.send(500, r.stderr or "build failed")
                return self.file(out)
            m = re.fullmatch(r"/preview/([a-z]+)", p)
            if m and m.group(1) in SYSTEMS:
                # Rebuild the same body in another design system or colour, for the live switcher.
                page = read_json(sdir / "page.json", {})
                if not page.get("layout") or not (root / "body.html").is_file():
                    return self.send(404, "no page built yet")
                accent = (parse_qs(u.query).get("accent") or [page.get("accent", "")])[0].lstrip("#")
                out = sdir / f"preview-{m.group(1)}.html"
                args = [sys.executable, str(MAKE), neatly_layout(page["layout"]), str(root / "body.html"), str(out),
                        "--system", system_css(m.group(1), sdir), "--no-check"]
                if accent:
                    args += ["--accent", accent]
                if page.get("title"):
                    args += ["--title", page["title"]]
                if page.get("lang"):
                    args += ["--lang", page["lang"]]
                r = subprocess.run(args, capture_output=True, text=True)
                if r.returncode != 0 or not out.is_file():
                    return self.send(500, r.stderr or "build failed")
                # The preview lives outside site/, so point asset links back at it.
                html = out.read_text(encoding="utf-8").replace('src="assets/', 'src="/site/assets/')
                return self.send(200, html, "text/html; charset=utf-8")
            if p.startswith("/site/"):
                rel = p[len("/site/"):] or "index.html"
                target = (site / rel).resolve()
                if (site.resolve() in target.parents or target == site.resolve()) and target.is_file():
                    return self.file(target)
                if p.endswith("/") and (target / "index.html").is_file():
                    return self.file(target / "index.html")
            self.send(404, "not found")

        def redirect(self, to):
            self.send_response(302)
            self.send_header("Location", to)
            self.end_headers()

        def do_POST(self):
            m = re.fullmatch(r"/api/answer/([a-z]+)", urlparse(self.path).path)
            if not m or m.group(1) not in FORM_NAMES:
                return self.send(404, "not found")
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > MAX_BODY:
                return self.send(413, "too large")
            try:
                data = json.loads(self.rfile.read(n).decode("utf-8"))
            except ValueError:
                return self.send(400, "bad json")
            data = save_uploads(data, site / "assets")
            data["_submitted_at"] = time.time()
            write_json(sdir / f"answers-{m.group(1)}.json", data)
            self.send(200, json.dumps({"ok": True}), "application/json")

    return Handler


def save_uploads(data, assets):
    """Turn data: URLs from file inputs into files in site/assets, keep the relative path."""
    def walk(v, key=""):
        if isinstance(v, dict):
            return {k: walk(x, k) for k, x in v.items()}
        if isinstance(v, list):
            return [walk(x, key) for x in v]
        if isinstance(v, str) and v.startswith("data:"):
            m = re.match(r"data:([\w/+.-]+);base64,(.*)", v, re.S)
            if m and m.group(1) in IMAGE_TYPES:
                assets.mkdir(parents=True, exist_ok=True)
                name = re.sub(r"[^a-z0-9-]", "", key.lower()) or "image"
                path = assets / f"{name}-{int(time.time() * 1000) % 100000}{IMAGE_TYPES[m.group(1)]}"
                path.write_bytes(base64.b64decode(m.group(2)))
                return f"assets/{path.name}"
            return ""
        return v
    return walk(data)


def serve(project, port):
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(project))
    server.serve_forever()


# ---------------------------------------------------------------- commands
def ensure_server(project):
    sdir = state_dir(project)
    info = read_json(sdir / "server.json", {})
    port = info.get("port")
    if port and alive(port):
        return port
    port = free_port()
    log = open(sdir / "server.log", "a")
    subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "serve", "--project", str(project), "--port", str(port)],
                     stdout=log, stderr=log, stdin=subprocess.DEVNULL, start_new_session=True)
    for _ in range(50):
        if alive(port):
            break
        time.sleep(0.1)
    else:
        sys.exit("The local helper did not start. See .shoufa/server.log")
    write_json(sdir / "server.json", {"port": port, "pid_hint": "started by ask.py"})
    return port


def cmd_open(a):
    if a.form not in FORM_NAMES:
        sys.exit(f"Unknown form {a.form!r}. Forms: {', '.join(sorted(FORM_NAMES))}")
    sdir = state_dir(a.project)
    port = ensure_server(a.project)
    old = sdir / f"answers-{a.form}.json"
    if old.exists():
        old.rename(sdir / f"answers-{a.form}.{int(time.time())}.json")
    meta = read_json(sdir / "meta.json", {})
    meta[f"opened_{a.form}"] = time.time()
    write_json(sdir / "meta.json", meta)
    url = f"http://127.0.0.1:{port}/form/{a.form}"
    if not a.no_browser:
        webbrowser.open(url)
    print(f"OPENED {url}")
    print("The form is open in the browser. Now run: ask.py wait " + a.form + " --project " + str(a.project))


def cmd_wait(a):
    sdir = state_dir(a.project)
    path = sdir / f"answers-{a.form}.json"
    end = time.time() + a.timeout
    while time.time() < end:
        data = read_json(path)
        if data:
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        time.sleep(1)
    print("STILL_WAITING")
    print("The person has not submitted yet. Run the same wait command again.")
    return 2


def cmd_status(a):
    sdir = state_dir(a.project)
    st = read_json(sdir / "status.json", {"steps": []})
    st.setdefault("steps", []).append({"text": a.text, "at": time.time()})
    st["current"] = a.text
    if a.url:
        st["url"] = a.url
    if a.done:
        st["done"] = True
    if a.error:
        st["error"] = a.text
    if a.phase:
        st["phase"] = a.phase
    write_json(sdir / "status.json", st)
    print("STATUS", a.text)


def cmd_build(a):
    root = Path(a.project).expanduser().resolve()
    body = root / "body.html"
    if not body.is_file():
        sys.exit(f"Write the page content to {body} first.")
    accent = (a.accent or "").lstrip("#")
    args = [sys.executable, str(MAKE), neatly_layout(a.layout), str(body), str(root / "site" / "index.html"),
            "--system", system_css(a.system, state_dir(root))]
    if accent:
        args += ["--accent", accent]
    if a.title:
        args += ["--title", a.title]
    if a.lang:
        args += ["--lang", a.lang]
    code = subprocess.call(args)
    sdir = state_dir(root)
    write_json(sdir / "page.json", {"layout": a.layout, "system": a.system, "accent": ("#" + accent) if accent else "",
                                    "title": a.title or "", "lang": a.lang or "", "suggested_name": a.name or ""})
    return code


def cmd_stop(a):
    sdir = state_dir(a.project)
    info = read_json(sdir / "server.json", {})
    port = info.get("port")
    if port and alive(port):
        r = subprocess.run(["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"], capture_output=True, text=True)
        for pid in r.stdout.split():
            try:
                os.kill(int(pid), 15)
            except (OSError, ValueError):
                pass
    print("STOPPED")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("open", "wait"):
        p = sub.add_parser(name)
        p.add_argument("form")
        p.add_argument("--project", default=".")
        if name == "open":
            p.add_argument("--no-browser", action="store_true")
        else:
            p.add_argument("--timeout", type=int, default=540)
    p = sub.add_parser("status")
    p.add_argument("text")
    p.add_argument("--project", default=".")
    p.add_argument("--url")
    p.add_argument("--done", action="store_true")
    p.add_argument("--error", action="store_true")
    p.add_argument("--phase", help="login | upload, so the deploy page can move its steps along")
    p = sub.add_parser("build")
    p.add_argument("--project", default=".")
    p.add_argument("--layout", required=True, help="personal, landing, app (a working tool), report, docs, dashboard or deck")
    p.add_argument("--system", default="mono", choices=SYSTEMS)
    p.add_argument("--accent")
    p.add_argument("--title")
    p.add_argument("--name", help="suggested web address, e.g. mia-chen")
    p.add_argument("--lang", help="page language tag, e.g. zh-CN or en")
    p = sub.add_parser("stop")
    p.add_argument("--project", default=".")
    p = sub.add_parser("serve")
    p.add_argument("--project", default=".")
    p.add_argument("--port", type=int, required=True)
    a = ap.parse_args()
    if a.cmd == "open":
        return cmd_open(a)
    if a.cmd == "wait":
        return cmd_wait(a)
    if a.cmd == "status":
        return cmd_status(a)
    if a.cmd == "stop":
        return cmd_stop(a)
    if a.cmd == "build":
        return cmd_build(a)
    if a.cmd == "serve":
        return serve(a.project, a.port)


if __name__ == "__main__":
    sys.exit(main() or 0)
