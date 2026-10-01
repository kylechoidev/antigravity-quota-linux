"""Embedded backend server serving the web UI and REST API."""
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from config import WEB_SERVER_PORT
from auth_manager import (
    load_accounts,
    start_interactive_oauth,
    add_active_local_account,
    rename_account,
    remove_account,
)
from quota_fetcher import (
    fetch_all_accounts_quota,
    kickstart_account,
    kickstart_all_idle_accounts,
)

WEB_DIR = Path(__file__).parent.parent / "src" / "web"


class AppServerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            accounts = load_accounts()
            if not accounts:
                add_active_local_account("Primary Session")
            data = fetch_all_accounts_quota()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return
        elif self.path == "/api/ping":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return
        # Default static file serving from WEB_DIR
        super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if self.path == "/api/add-account":
            name = payload.get("name", "New Account")
            threading.Thread(target=start_interactive_oauth, args=(name,), daemon=True).start()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"started"}')
            return

        elif self.path == "/api/import-active":
            name = payload.get("name", "Primary Session")
            acc = add_active_local_account(name)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "account": acc}).encode("utf-8"))
            return

        elif self.path == "/api/rename-account":
            identifier = payload.get("identifier", "")
            new_name = payload.get("newName", "")
            success = rename_account(identifier, new_name)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok" if success else "error"}).encode("utf-8"))
            return

        elif self.path == "/api/remove-account":
            identifier = payload.get("identifier", "")
            success = remove_account(identifier)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok" if success else "not_found"}).encode("utf-8"))
            return

        elif self.path == "/api/kickstart-account":
            identifier = payload.get("identifier", "").lower()
            pools = payload.get("pools", ["gemini", "claude_gpt"])
            accounts = load_accounts()
            target_acc = next((a for a in accounts if a.get("name", "").lower() == identifier or a.get("email", "").lower() == identifier), None)
            if not target_acc:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "error": "Account not found"}).encode("utf-8"))
                return

            res = kickstart_account(target_acc, pools=pools)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        elif self.path == "/api/kickstart-all":
            pools = payload.get("pools", ["gemini", "claude_gpt"])
            only_unanchored = payload.get("onlyUnanchored", True)
            summary = kickstart_all_idle_accounts(pools=pools, only_unanchored=only_unanchored)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "results": summary}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(("127.0.0.1", WEB_SERVER_PORT), AppServerHandler)
    print(f"Antigravity Quota WebApp Backend running at: http://127.0.0.1:{WEB_SERVER_PORT}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
