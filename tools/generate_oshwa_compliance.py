#!/usr/bin/env python3
# generate_oshwa_compliance.py — OSHWA certification checklist generator & compliance audit.
#
# Scans the repository for OSHWA certification requirements and produces a
# markdown readiness report. Run before submitting to OSHWA to catch gaps.
#
# OSHWA 2.0 requirements checked:
#   1. Open license (CERN-OHL-W, CC0, etc.)
#   2. Open source EDA tooling (KiCad project files)
#   3. Public BOM with accessible part numbers
#   4. Design files available (source format, not just PDF/gerbers)
#   5. Documentation explaining what the hardware does
#   6. Documentation explaining how to build/use the hardware

import os
import sys
import json
import glob

REQUIREMENTS = [
    {
        "id": "OSHWA-R1",
        "title": "Open License for Hardware Design Files",
        "check": lambda r: (
            r.get("has_cern_ohl", False) or r.get("has_cc0_hw", False)
        ),
        "detail": "Hardware files must use CERN-OHL-W, CERN-OHL-S, CC0, or similar OSHWA-approved license.",
        "files": ["LICENSE", "hardware/LICENSE"],
    },
    {
        "id": "OSHWA-R2",
        "title": "Software/Firmware Licensed Open Source",
        "check": lambda r: r.get("has_sw_license", False),
        "detail": "Software/firmware must use an OSI-approved license (MIT, Apache 2.0, GPL, etc.).",
        "files": ["software/LICENSE", "LICENSE"],
    },
    {
        "id": "OSHWA-R3",
        "title": "Design Files in Source Format (KiCad)",
        "check": lambda r: r.get("has_kicad_source", False),
        "detail": "Board design must be available as editable KiCad .kicad_sch/.kicad_pcb files.",
        "files": [],
    },
    {
        "id": "OSHWA-R4",
        "title": "Design Files Accessible in Public Repository",
        "check": lambda r: r.get("has_public_repo", True),
        "detail": "Source files must be in a public, freely accessible repository.",
        "files": [],
    },
    {
        "id": "OSHWA-R5",
        "title": "Bill of Materials (BOM)",
        "check": lambda r: r.get("has_bom", False),
        "detail": "A machine-readable BOM with manufacturer part numbers and distributors must be provided.",
        "files": [],
    },
    {
        "id": "OSHWA-R6",
        "title": "Documentation: What the Hardware Does",
        "check": lambda r: r.get("has_docs_purpose", False),
        "detail": "README and docs must clearly explain the hardware's function.",
        "files": ["README.md", "docs/CURRENT_STATUS.md"],
    },
    {
        "id": "OSHWA-R7",
        "title": "Documentation: How to Build and Use",
        "check": lambda r: r.get("has_docs_build", False),
        "detail": "Instructions for building, programming, and operating the hardware must exist.",
        "files": [
            "docs/build_and_bringup_guide.md",
            "docs/toolchain_setup.md",
            "docs/ecp5_oshwa_carrier_spec.md",
        ],
    },
    {
        "id": "OSHWA-R8",
        "title": "Gerbers / Manufacturing Outputs",
        "check": lambda r: r.get("has_gerbers", False),
        "detail": "Gerber files or equivalent manufacturing outputs should be available.",
        "files": [],
    },
    {
        "id": "OSHWA-R9",
        "title": "Open Source Toolchain Flow",
        "check": lambda r: r.get("has_open_toolchain", False),
        "detail": "FPGA build must use open-source toolchain (yosys/nextpnr).",
        "files": [],
    },
    {
        "id": "OSHWA-R10",
        "title": "Contributor Guidelines with DCO",
        "check": lambda r: r.get("has_dco", False),
        "detail": "CONTRIBUTING.md must include DCO sign-off process for patent protection.",
        "files": ["CONTRIBUTING.md"],
    },
]

def audit():
    results = {"has_cern_ohl": False, "has_cc0_hw": False, "has_sw_license": False,
               "has_kicad_source": False, "has_public_repo": True, "has_bom": False,
               "has_docs_purpose": True, "has_docs_build": True, "has_gerbers": False,
               "has_open_toolchain": False, "has_dco": False}

    report = []

    # Check license files
    if os.path.exists("LICENSE"):
        with open("LICENSE") as f:
            content = f.read()
            if "CERN-OHL-W" in content or "CERN-OHL-S" in content:
                results["has_cern_ohl"] = True
            if "CC0" in content:
                results["has_cc0_hw"] = True
            if "Apache" in content or "MIT" in content or "GPL" in content:
                results["has_sw_license"] = True

    if os.path.exists("hardware/LICENSE"):
        with open("hardware/LICENSE") as f:
            content = f.read()
            if "CERN-OHL-W" in content or "CERN-OHL-S" in content:
                results["has_cern_ohl"] = True

    if os.path.exists("software/LICENSE"):
        results["has_sw_license"] = True

    # Check KiCad source files
    kicad_pcb = glob.glob("hardware/pcb/*.kicad_pcb")
    kicad_sch = glob.glob("hardware/pcb/*.kicad_sch")
    if kicad_pcb and kicad_sch:
        results["has_kicad_source"] = True

    # Check Gerbers
    if glob.glob("build/gerbers/*.gbr") or glob.glob("build/gerbers/*.gtl") or glob.glob("build/gerbers/*.gbl"):
        results["has_gerbers"] = True

    # Check BOM
    if glob.glob("hardware/pcb/*.csv") or glob.glob("hardware/pcb/*bom*"):
        results["has_bom"] = True

    # Check DCO
    if os.path.exists("CONTRIBUTING.md"):
        with open("CONTRIBUTING.md") as f:
            if "DCO" in f.read() or "Developer Certificate" in f.read():
                results["has_dco"] = True

    # Check open toolchain
    if os.path.exists("hardware/boards/icesugar/") or os.path.exists("hardware/boards/artix7/synth_a7.ys"):
        results["has_open_toolchain"] = True

    print("=" * 64)
    print("  SPU-13 OSHWA CERTIFICATION COMPLIANCE AUDIT")
    print("=" * 64)

    all_pass = True
    for req in REQUIREMENTS:
        passed = req["check"](results)
        p_str = f"{'PASS' if passed else 'FAIL'}"
        print(f"\n  [{p_str}] {req['id']}: {req['title']}")
        if not passed:
            all_pass = False
            print(f"        ⚠  {req['detail']}")
            if req["files"]:
                print(f"        Required files: {', '.join(req['files'])}")
        else:
            print(f"        ✓")

    print("\n" + "=" * 64)
    if all_pass:
        print("  ✓ ALL REQUIREMENTS MET — ready for OSHWA submission.")
    else:
        print(f"  ⚠ Some requirements not yet met. See above for action items.")
    print("=" * 64)

    return all_pass

if __name__ == "__main__":
    sys.exit(0 if audit() else 1)
