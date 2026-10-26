#!/usr/bin/env python3
"""HTTP contract tests for the loopback W1-C viewer."""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from software.spu_gpu_eval.workbench_viewer import PPM_HEADER, create_server


class WorkbenchViewerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = create_server(0)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        viewer = self.server.viewer_state
        temp_dir = viewer.temp_dir
        viewer.close()
        self.assertFalse(temp_dir.exists())

    def get(self, path: str) -> tuple[int, dict[str, str], bytes]:
        try:
            response = urlopen(self.base + path, timeout=30)
        except HTTPError as error:
            try:
                return error.code, dict(error.headers), error.read()
            finally:
                error.close()
        with response:
            return response.status, dict(response.headers), response.read()

    def test_page_and_scene_catalogue_are_explicit(self) -> None:
        status, headers, page = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn(b"Ideal rational reference", page)
        self.assertIn(b"Finite-width T1d device model", page)
        self.assertIn(b"addEventListener(\"click\"", page)

        status, _, body = self.get("/api/scenes")
        self.assertEqual(status, 200)
        catalogue = json.loads(body)
        self.assertEqual(catalogue["profile"], "t1d-two-triangle-v1")
        self.assertEqual(len(catalogue["scenes"]), 13)
        original = json.loads((ROOT / 'fixtures/sg0_v1/catalogue_before.json').read_bytes())
        frozen = json.loads((ROOT / 'fixtures/sg0_v1/inputs.json').read_bytes())
        fields = ('id', 'group', 'sha256')
        self.assertEqual(catalogue['scenes'][:11],
                         [{k: entry[k] for k in fields} for entry in original['scenes']])
        self.assertEqual(catalogue['scenes'][11:],
                         [{k: entry[k] for k in fields} for entry in frozen['publication_entries']])

    def test_frames_are_existing_w1b_rgb_payloads(self) -> None:
        for mode, artifact in (("ideal", "preview.ppm"),
                               ("device", "device_preview.ppm")):
            query = urlencode({"scene_id": "baseline", "mode": mode})
            status, headers, body = self.get(f"/api/frame?{query}")
            self.assertEqual(status, 200)
            self.assertEqual(headers["X-Frame-Width"], "640")
            self.assertEqual(headers["X-Frame-Height"], "480")
            self.assertEqual(len(body), 640 * 480 * 3)
            ideal_dir, device_dir = self.server.viewer_state.outputs["baseline"]
            source = ideal_dir if mode == "ideal" else device_dir
            ppm = (source / artifact).read_bytes()
            self.assertTrue(ppm.startswith(PPM_HEADER))
            self.assertEqual(body, ppm[len(PPM_HEADER):])

    def test_parallel_frame_requests_create_one_render_pair(self) -> None:
        paths = ["/api/frame?" + urlencode({"scene_id": "baseline", "mode": mode})
                 for mode in ("ideal", "device")]
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(self.get, paths))
        self.assertEqual([item[0] for item in responses], [200, 200])
        self.assertEqual(set(self.server.viewer_state.outputs), {"baseline"})
        self.assertEqual(len(list(self.server.viewer_state.temp_dir.iterdir())), 2)

    def test_pixel_endpoint_preserves_depth_discrepancy(self) -> None:
        query = urlencode({"scene_id": "baseline", "x": 320, "y": 0})
        status, _, body = self.get(f"/api/inspect?{query}")
        self.assertEqual(status, 200)
        report = json.loads(body)
        self.assertFalse(report["comparison"]["depths_equal"])
        for field in ("coverage_equal", "covered_triangles_equal", "winner_equal", "rgb_equal"):
            self.assertTrue(report["comparison"][field])
        self.assertEqual(report["ideal_reference"]["depths"][0]["numerator"], 2000)
        self.assertEqual(report["device_model"]["depths"][0]["value"], 1999)
        self.assertFalse(report["evidence"]["physical_observation"])

    def test_invalid_scene_mode_pixel_and_query_fail_cleanly(self) -> None:
        invalid = (
            "/api/frame?scene_id=missing&mode=ideal",
            "/api/frame?scene_id=baseline&mode=shader",
            "/api/inspect?scene_id=baseline&x=640&y=0",
            "/api/inspect?scene_id=baseline&x=1&y=0&x=2",
            "/api/inspect?scene_id=baseline&x=1",
            "/api/frame?malformed",
        )
        for path in invalid:
            with self.subTest(path=path):
                status, _, body = self.get(path)
                self.assertIn(status, (400, 404))
                self.assertIn("error", json.loads(body))

    def test_sg0_frame_and_pixel_endpoints(self) -> None:
        frozen = json.loads((ROOT / 'fixtures/sg0_v1/inputs.json').read_bytes())
        for variant in frozen['variants']:
            scene_id = 'sg0_' + variant['id']
            for mode, artifact in (('ideal', 'preview.ppm'), ('device', 'device_preview.ppm')):
                query = urlencode({'scene_id': scene_id, 'mode': mode})
                status, headers, body = self.get('/api/frame?' + query)
                self.assertEqual(status, 200)
                self.assertEqual(len(body), 640*480*3)
                self.assertEqual(headers['X-Frame-Width'], '640')
                directories = self.server.viewer_state.outputs[scene_id]
                directory = directories[0 if mode == 'ideal' else 1]
                self.assertEqual(body, (directory / artifact).read_bytes()[len(PPM_HEADER):])
            for expected in variant['diagnostic_pixels']:
                query = urlencode({'scene_id': scene_id, 'x': expected['x'], 'y': expected['y']})
                status, _, body = self.get('/api/inspect?' + query)
                self.assertEqual(status, 200)
                report = json.loads(body)
                self.assertEqual(report['ideal_reference'], expected)
                self.assertFalse(report['evidence']['physical_observation'])


if __name__ == "__main__":
    unittest.main()
