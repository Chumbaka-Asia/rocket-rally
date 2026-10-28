"""
Rocket Rally -- local network exhibition hub

Usage:
  python scripts/server.py          # default port 8082
  python scripts/server.py 9001     # custom port

API:
  GET     /api/rockets
  GET     /api/host-info    (LAN IP + active port for join QR codes)
  POST    /api/rockets
  POST    /api/rockets/import  (quiet archive restore)
  DELETE  /api/rockets/<id>
  DELETE  /api/rockets
  GET     /api/events       (SSE: new-rocket, sync-rockets, remove-rocket, clear)
"""

import json
import os
import queue
import socket
import sys
import tempfile
import threading
import time
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

# This file lives in scripts/; the served piece root is its parent folder.
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "rockets-data.json"
TEMPLATES_DIR = ROOT / "templates"
DEFAULT_PORT = 8082
MAX_BODY_BYTES = 2_000_000
MAX_IMPORT_BODY_BYTES = 35_000_000
MAX_NAME_LENGTH = 20
MAX_ROCKET_NAME_LENGTH = 24


def load_template_ids():
    """Every printable template is one <id>.svg in templates/. That folder is
    the single source of truth for which rocket shapes exist, so the upload
    allowlist is derived from it rather than hand-kept in sync."""
    if not TEMPLATES_DIR.exists():
        return frozenset()
    return frozenset(path.stem for path in TEMPLATES_DIR.glob("*.svg"))


VALID_TEMPLATE_IDS = load_template_ids()

rockets_lock = threading.Lock()
rockets = []
clients_lock = threading.Lock()
clients = []


def load_rockets():
    global rockets
    if not DATA_FILE.exists():
        return
    try:
        with DATA_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            rockets = [item for item in data if isinstance(item, dict)]
            print("  Loaded {} rocket(s) from {}".format(len(rockets), DATA_FILE.name))
    except Exception as error:
        print("  Warning: could not load {}: {}".format(DATA_FILE.name, error))


def save_rockets():
    """Atomically save while rockets_lock is held."""
    fd, temp_name = tempfile.mkstemp(prefix="rocket-rally-", suffix=".json", dir=str(ROOT))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(rockets, handle, ensure_ascii=False, separators=(",", ":"))
        os.replace(temp_name, DATA_FILE)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def event_message(event, data):
    return ("event: {}\ndata: {}\n\n".format(event, json.dumps(data, ensure_ascii=False))).encode("utf-8")


def broadcast(event, data):
    message = event_message(event, data)
    with clients_lock:
        stale = []
        for client in clients:
            try:
                client.put_nowait(message)
            except queue.Full:
                stale.append(client)
        for client in stale:
            clients.remove(client)


def valid_optional_string(value, maximum):
    return isinstance(value, str) and len(value.strip()) <= maximum


def validate_submission(payload):
    if not isinstance(payload, dict):
        return None, "Expected a JSON object."
    image = payload.get("imageDataURL")
    child_name = payload.get("childName", "")
    rocket_name = payload.get("rocketName", "")
    template_id = payload.get("templateId")
    if not isinstance(image, str) or not image.startswith(("data:image/webp;base64,", "data:image/png;base64,")):
        return None, "Rocket image must be a WebP or PNG data URL."
    if len(image) > 1_800_000:
        return None, "Rocket image is too large. Please use the preview image."
    if not valid_optional_string(child_name, MAX_NAME_LENGTH):
        return None, "Child name must contain no more than {} characters.".format(MAX_NAME_LENGTH)
    if not valid_optional_string(rocket_name, MAX_ROCKET_NAME_LENGTH):
        return None, "Rocket name must contain no more than {} characters.".format(MAX_ROCKET_NAME_LENGTH)
    if template_id not in VALID_TEMPLATE_IDS:
        return None, "Unknown rocket template."
    return {
        "version": 1,
        "id": uuid.uuid4().hex,
        "imageDataURL": image,
        "templateId": template_id,
        "childName": child_name.strip(),
        "rocketName": rocket_name.strip(),
        "createdAt": int(time.time() * 1000),
    }, None


class RocketHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        pass

    def translate_path(self, path):
        # Static files always resolve from the installation directory, not the caller's cwd.
        requested = urlparse(path).path.lstrip("/").replace("/", os.sep)
        candidate = (ROOT / requested).resolve()
        try:
            candidate.relative_to(ROOT)
        except ValueError:
            return str(ROOT / "display.html")
        return str(candidate)

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self, maximum=MAX_BODY_BYTES):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None, "Invalid Content-Length."
        if length <= 0 or length > maximum:
            return None, "Request body is missing or too large."
        try:
            return json.loads(self.rfile.read(length).decode("utf-8")), None
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None, "Invalid JSON."

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/rockets":
            with rockets_lock:
                snapshot = list(rockets)
            self.send_json(HTTPStatus.OK, snapshot)
        elif path == "/api/host-info":
            self.send_json(HTTPStatus.OK, {
                "ip": local_ip(),
                "port": self.server.server_address[1],
            })
        elif path == "/api/events":
            self.handle_events()
        else:
            super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ("/api/rockets", "/api/rockets/import"):
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Unknown API path."})
            return
        payload, error = self.read_json(MAX_IMPORT_BODY_BYTES if path == "/api/rockets/import" else MAX_BODY_BYTES)
        if error:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": error})
            return
        if path == "/api/rockets/import":
            candidates = payload.get("rockets") if isinstance(payload, dict) else None
            if not isinstance(candidates, list) or not candidates or len(candidates) > 500:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Import must contain 1-500 rockets."})
                return
            imported = []
            for candidate in candidates:
                rocket, error = validate_submission(candidate)
                if error:
                    self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid import: {}".format(error)})
                    return
                imported.append(rocket)
            try:
                with rockets_lock:
                    rockets.extend(imported)
                    save_rockets()
            except OSError as error:
                self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Could not save import: {}".format(error)})
                return
            broadcast("sync-rockets", imported)
            self.send_json(HTTPStatus.CREATED, imported)
            return
        rocket, error = validate_submission(payload)
        if error:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": error})
            return
        try:
            with rockets_lock:
                rockets.append(rocket)
                save_rockets()
        except OSError as error:
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Could not save rocket: {}".format(error)})
            return
        broadcast("new-rocket", rocket)
        self.send_json(HTTPStatus.CREATED, rocket)

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path == "/api/rockets":
            with rockets_lock:
                rockets.clear()
                save_rockets()
            broadcast("clear", {})
            self.send_json(HTTPStatus.OK, {"ok": True})
            return
        prefix = "/api/rockets/"
        if path.startswith(prefix) and len(path) > len(prefix):
            rocket_id = path[len(prefix):]
            with rockets_lock:
                index = next((i for i, item in enumerate(rockets) if item.get("id") == rocket_id), None)
                if index is None:
                    self.send_json(HTTPStatus.NOT_FOUND, {"error": "Rocket not found."})
                    return
                rockets.pop(index)
                save_rockets()
            broadcast("remove-rocket", {"id": rocket_id})
            self.send_json(HTTPStatus.OK, {"ok": True})
            return
        self.send_json(HTTPStatus.NOT_FOUND, {"error": "Unknown API path."})

    def handle_events(self):
        client = queue.Queue(maxsize=100)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        with clients_lock:
            clients.append(client)
        try:
            while True:
                try:
                    message = client.get(timeout=25)
                except queue.Empty:
                    message = b": keep-alive\n\n"
                self.wfile.write(message)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        finally:
            with clients_lock:
                if client in clients:
                    clients.remove(client)


class RocketServer(ThreadingHTTPServer):
    daemon_threads = True


def local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "YOUR_LOCAL_IP"


def main():
    try:
        port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    except ValueError:
        print("Port must be a number.")
        return 2
    load_rockets()
    try:
        server = RocketServer(("", port), RocketHandler)
    except OSError as error:
        print("Could not start Rocket Rally on port {}: {}".format(port, error))
        print("Try: python scripts/server.py 9001")
        return 1
    ip = local_ip()
    print("\nRocket Rally is ready")
    print("  Display screen -> http://localhost:{}/display.html".format(port))
    print("  Phone kiosks   -> http://{}:{}/upload.html".format(ip, port))
    print("  Templates      -> {}".format(", ".join(sorted(VALID_TEMPLATE_IDS)) or "none found in templates/"))
    print("  Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
