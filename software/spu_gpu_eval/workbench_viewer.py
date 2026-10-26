"""Loopback browser viewer for existing T1d workbench artifacts."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from threading import Lock
from urllib.parse import parse_qs, urlsplit

from .device_preview import write_device_preview
from .preview import PreviewError, write_preview
from .scene import HEIGHT, WIDTH
from .workbench import _inspect
from .workbench_catalog import CatalogError, ROOT, find_scene, load_catalog


HTML = Path(__file__).with_name("viewer.html")
PPM_HEADER = f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii")


class ViewerState:
    def __init__(self) -> None:
        base = ROOT / "build/gpu_evaluation"
        base.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(tempfile.mkdtemp(prefix="spu_gpu_w1c_", dir=base))
        self.outputs: dict[str, tuple[Path, Path]] = {}
        self.lock = Lock()

    def close(self) -> None:
        shutil.rmtree(self.temp_dir)

    def frames(self, scene_id: str) -> tuple[bytes, bytes]:
        with self.lock:
            entry = find_scene(scene_id)
            if scene_id not in self.outputs:
                key = hashlib.sha256(scene_id.encode("utf-8")).hexdigest()[:12]
                ideal_dir = self.temp_dir / f"{key}_ideal"
                device_dir = self.temp_dir / f"{key}_device"
                write_preview(entry["absolute_path"], ideal_dir)
                write_device_preview(entry["absolute_path"], device_dir)
                self.outputs[scene_id] = (ideal_dir, device_dir)
            ideal_dir, device_dir = self.outputs[scene_id]
            ideal = (ideal_dir / "preview.ppm").read_bytes()
            device = (device_dir / "device_preview.ppm").read_bytes()
            if not ideal.startswith(PPM_HEADER) or not device.startswith(PPM_HEADER):
                raise ValueError("W1-B renderer returned an unsupported PPM frame")
            size = WIDTH * HEIGHT * 3
            ideal_rgb, device_rgb = ideal[len(PPM_HEADER):], device[len(PPM_HEADER):]
            if len(ideal_rgb) != size or len(device_rgb) != size:
                raise ValueError("W1-B renderer returned an incomplete PPM frame")
            return ideal_rgb, device_rgb


def _json(handler: BaseHTTPRequestHandler, payload: object, status: int = 200) -> None:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


class ViewerHandler(BaseHTTPRequestHandler):
    viewer: ViewerState

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        try:
            query = parse_qs(parsed.query, strict_parsing=True)
            if parsed.path == "/":
                body = HTML.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path == "/api/scenes":
                scenes = [{key: entry[key] for key in ("id", "group", "sha256")}
                          for entry in load_catalog()]
                _json(self, {"profile": "t1d-two-triangle-v1", "scenes": scenes})
                return
            if parsed.path == "/api/frame":
                scene_id = self._one(query, "scene_id")
                mode = self._one(query, "mode")
                if mode not in ("ideal", "device"):
                    raise ValueError("mode must be ideal or device")
                frames = self.viewer.frames(scene_id)
                body = frames[0 if mode == "ideal" else 1]
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("X-Frame-Width", str(WIDTH))
                self.send_header("X-Frame-Height", str(HEIGHT))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path == "/api/inspect":
                scene_id = self._one(query, "scene_id")
                x = int(self._one(query, "x"))
                y = int(self._one(query, "y"))
                _json(self, _inspect(scene_id, x, y))
                return
            _json(self, {"error": "unknown endpoint"}, 404)
        except (CatalogError, PreviewError, OSError, ValueError) as exc:
            _json(self, {"error": str(exc)}, 400)

    @staticmethod
    def _one(query: dict[str, list[str]], key: str) -> str:
        values = query.get(key, [])
        if len(values) != 1 or not values[0]:
            raise ValueError(f"exactly one {key} parameter is required")
        return values[0]


def create_server(port: int = 8765) -> ThreadingHTTPServer:
    viewer = ViewerState()

    class BoundHandler(ViewerHandler):
        pass

    BoundHandler.viewer = viewer
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), BoundHandler)
    except Exception:
        viewer.close()
        raise
    server.viewer_state = viewer  # type: ignore[attr-defined]
    return server


def serve(port: int = 8765) -> None:
    server = create_server(port)
    print(f"W1-C viewer listening at http://127.0.0.1:{server.server_port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nW1-C viewer stopped")
    finally:
        server.server_close()
        server.viewer_state.close()  # type: ignore[attr-defined]
