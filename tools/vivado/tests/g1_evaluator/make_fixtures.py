"""Build the compact G1-evaluator fixtures from preserved Vivado 2026.1 run evidence (run once; output is committed).

Usage (repository root): python3 -I tools/vivado/tests/g1_evaluator/make_fixtures.py
Sources (gitignored build evidence):  build/vivado/g1_pos_01 + detached_g1_pos_01   (G1 positive run, generated clock)
                                      build/vivado/step7v_nc3_01 + detached_step7v_nc3_01   (Step 7V NC3, original XDC)
Every fixture file is either a byte copy or a whole-line selection of its source in original order (no line is edited). PROVENANCE.txt records
the source sha256 and the rule per file, so the selection can be re-derived and checked.
"""
import hashlib
import os
import re

ROOT = "tools/vivado/tests/g1_evaluator/fixtures"
SRC = {"g1_pos": ("build/vivado/g1_pos_01", "build/vivado/detached_g1_pos_01"),
       "nc3": ("build/vivado/step7v_nc3_01", "build/vivado/detached_step7v_nc3_01")}
LOG_KEEP = re.compile(r"^(SPU_GATE_SCOPE_BEGIN$|INFO: |WARNING: |CRITICAL WARNING: |ERROR: |Parsing XDC File|Finished Parsing XDC File|# )")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def log_lines(lines):
    return [l for l in lines if LOG_KEEP.match(l)], "lines matching " + LOG_KEEP.pattern


def check_timing_lines(lines):
    return [l for l in lines if re.match(r"^\s*[0-9]+\. checking [a-z_]+ \([0-9]+\)", l) or l == "Table of Contents"], \
        "'Table of Contents' and every 'N. checking <name> (<count>)' line"


def report_head(lines):
    # The table of contents also lists "2. REPORT DETAILS"; the section heading is the occurrence followed by its dash underline.
    end = next((i for i, l in enumerate(lines[:-1]) if l.startswith("2. REPORT DETAILS") and re.match(r"^-{5,}$", lines[i + 1])), len(lines))
    return lines[:end], "lines before the '2. REPORT DETAILS' section heading (table of contents + summary table)"


def timing_summary(lines):
    td = next(i for i, l in enumerate(lines) if l.startswith("| Timing Details"))
    keep, i = lines[:td + 1], td + 1
    while i < len(lines):
        if re.match(r"^-{20,}$", lines[i]) and i + 1 < len(lines) and re.match(r"^(From Clock:|Path Group:)", lines[i + 1]):
            j = i + 1
            while j < len(lines) and not re.match(r"^-{20,}$", lines[j]):
                j += 1
            keep += lines[i:j + 1]
            i = j + 1
        else:
            i += 1
    return keep, "all lines up to '| Timing Details', then each details block from its opening to its closing dash line (path listings dropped)"


RULES = {"vivado.log": log_lines, "synth_check_timing.rpt": check_timing_lines, "synth_methodology.rpt": report_head,
         "synth_drc.rpt": report_head, "synth_timing_summary.rpt": timing_summary}
OUT_FILES = ["vivado.log", "run_manifest.txt", "synth_check_timing.rpt", "synth_clocks.rpt", "synth_clock_networks.rpt",
             "synth_timing_summary.rpt", "synth_methodology.rpt", "synth_drc.rpt", "synth_utilization.rpt", "synth_cdc.rpt",
             "COMPLETE", "FAILED"]
DET_FILES = ["exit_status", "result.json", "COMPLETE", "FAILED"]
SMALL = 16384   # files at or below this size are copied whole

prov = ["Compact fixtures for tools/vivado/tests/g1_evaluator. Real Vivado v2026.1 (SW Build 6511674) output; no line edited.", ""]
for name, (out, det) in SRC.items():
    for sub, src, files in (("out", out, OUT_FILES), ("det", det, DET_FILES)):
        os.makedirs(os.path.join(ROOT, name, sub), exist_ok=True)
        for f in files:
            p = os.path.join(src, f)
            if not os.path.exists(p):
                continue
            raw = open(p).read()
            if os.path.getsize(p) <= SMALL or f not in RULES:
                text, rule = raw, "byte copy"
            else:
                sel, rule = RULES[f](raw.split("\n"))
                text = "\n".join(sel) + "\n"
            open(os.path.join(ROOT, name, sub, f), "w").write(text)
            prov.append(f"{name}/{sub}/{f}  <- {p}  sha256 {sha(p)}  [{rule}]")
open(os.path.join(ROOT, "PROVENANCE.txt"), "w").write("\n".join(prov) + "\n")
print("\n".join(prov))
