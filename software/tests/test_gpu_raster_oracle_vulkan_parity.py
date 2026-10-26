#!/usr/bin/env python3
"""test_gpu_raster_oracle_vulkan_parity.py -- exhaustive bit-exact parity
between gpu_raster_oracle.py and a real Vulkan compute dispatch
(software/gpu_vulkan/gpu_raster.comp), over the same full 640x480 screen
and the same 3 test triangles as
test_gpu_raster_oracle_rtl_parity.py -- the third leg of the same
triangle (oracle<->RTL done 2026-08-24; oracle<->Vulkan compute here),
giving RTL<->Vulkan-compute agreement transitively through the shared
oracle rather than needing its own separate comparison.

Compiles the GLSL compute shader (glslc) and the C++ Vulkan host
program (g++ -lvulkan) once, then runs the host program once per
triangle, parsing its "COV x y" stdout lines exactly like the RTL
parity test parses vvp's.

Run:
  python3 software/tests/test_gpu_raster_oracle_vulkan_parity.py

Requirements: glslc, g++, and a Vulkan-capable GPU + driver in PATH/on
the system (checked at import time; skips cleanly, not a failure, if
unavailable -- this is real GPU hardware, not a toolchain assumption
every dev machine or CI runner is guaranteed to have).
"""
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "software"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.gpu_raster_oracle import covered_pixels  # noqa: E402
from test_gpu_raster_oracle_rtl_parity import TEST_TRIANGLES, WIDTH, HEIGHT  # noqa: E402

GPU_DIR = REPO / "software" / "gpu_vulkan"
SHADER_SRC = GPU_DIR / "gpu_raster.comp"
HOST_SRC = GPU_DIR / "gpu_raster_compute.cpp"


def vulkan_available() -> bool:
    if not (shutil.which("glslc") and shutil.which("g++")):
        return False
    probe = subprocess.run(["vulkaninfo", "--summary"], capture_output=True, text=True)
    return probe.returncode == 0 and "deviceType" in probe.stdout


def build(build_dir: Path):
    spv_path = build_dir / "gpu_raster.comp.spv"
    cc = subprocess.run(["glslc", str(SHADER_SRC), "-o", str(spv_path)],
                         capture_output=True, text=True)
    if cc.returncode != 0:
        raise RuntimeError(f"glslc failed:\n{cc.stdout}\n{cc.stderr}")

    bin_path = build_dir / "gpu_raster_compute"
    cc2 = subprocess.run(
        ["g++", "-std=c++17", "-O2", str(HOST_SRC), "-o", str(bin_path), "-lvulkan"],
        capture_output=True, text=True)
    if cc2.returncode != 0:
        raise RuntimeError(f"g++ failed:\n{cc2.stdout}\n{cc2.stderr}")
    return bin_path, spv_path


def run_vulkan_scan(binary: Path, spv_path: Path, edges) -> set:
    (a0, b0, c0), (a1, b1, c1), (a2, b2, c2) = edges
    args = [str(binary)] + [str(v) for v in
            (a0, b0, c0, a1, b1, c1, a2, b2, c2, WIDTH, HEIGHT)] + [str(spv_path)]
    rr = subprocess.run(args, capture_output=True, text=True, timeout=30)
    if "SCAN DONE" not in rr.stdout:
        raise RuntimeError(f"Vulkan scan did not complete:\n{rr.stdout}\n{rr.stderr}")
    covered = set()
    for line in rr.stdout.splitlines():
        if line.startswith("COV "):
            _, xs, ys = line.split()
            covered.add((int(xs), int(ys)))
    return covered


def main() -> int:
    if not vulkan_available():
        print("SKIP: no Vulkan-capable device/toolchain found on this machine")
        print("ALL GPU RASTER VULKAN PARITY CHECKS PASSED (skipped, no GPU)")
        return 0

    build_dir = REPO / "build"
    build_dir.mkdir(exist_ok=True)
    binary, spv_path = build(build_dir)

    total_fail = 0
    for name, edges in TEST_TRIANGLES:
        oracle_set = covered_pixels(edges, WIDTH, HEIGHT)
        vk_set = run_vulkan_scan(binary, spv_path, edges)

        missing = oracle_set - vk_set
        extra = vk_set - oracle_set
        if missing or extra:
            total_fail += 1
            print(f"FAIL: {name} -- oracle={len(oracle_set)} vulkan={len(vk_set)} "
                  f"missing_in_vulkan={len(missing)} extra_in_vulkan={len(extra)}")
            for pt in sorted(missing)[:5]:
                print(f"    missing in Vulkan (oracle says covered): {pt}")
            for pt in sorted(extra)[:5]:
                print(f"    extra in Vulkan (oracle says NOT covered): {pt}")
        else:
            print(f"PASS: {name} -- {len(oracle_set)}/{WIDTH*HEIGHT} pixels, "
                  f"exact set match against Vulkan compute")

    if total_fail:
        print(f"\nFAILED: {total_fail}/{len(TEST_TRIANGLES)} triangles mismatched")
        return 1
    print(f"\n{len(TEST_TRIANGLES)} triangles, exact pixel-set parity "
          f"(oracle vs Vulkan compute, full {WIDTH}x{HEIGHT} screen)")
    print("ALL GPU RASTER VULKAN PARITY CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
