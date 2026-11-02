"""REGRESS-CLEAN-1: release-test manifest, preflight and research-mode classification.

Pure helpers for run_all_tests.py. Release mode runs exactly the benches listed in
tools/release_tests.txt (tracked benches under hardware/tests/); research mode runs
every other discovered bench and classifies its outcome against
tools/known_failures.txt. A known failure is never reported as a pass.
"""
import fnmatch
import hashlib
import re
import subprocess
from pathlib import Path

PATTERNS = ("*_tb.v", "*tb*.v", "testbench*.v")
BENCH_ROOT = "hardware/tests/"
SOURCE_SUFFIXES = (".v", ".vh", ".sv")
MANIFEST = "tools/release_tests.txt"
KNOWN = "tools/known_failures.txt"


def _git(root, *args):
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout.splitlines() if r.returncode == 0 else None


def is_bench(path):
    return any(fnmatch.fnmatch(Path(path).name, p) for p in PATTERNS)


def eligible(root, skip_dirs):
    """Tracked benches under hardware/tests/ (filesystem scan if not a git checkout)."""
    files = _git(root, "ls-files", BENCH_ROOT)
    if files is None:
        files = [p.relative_to(root).as_posix() for p in (Path(root) / BENCH_ROOT).rglob("*.v")]
    return sorted(f for f in files if is_bench(f) and "/reference/" not in "/" + f
                  and not any(part in skip_dirs for part in Path(f).parts))


def discover(root, skip_dirs):
    """Legacy repo-wide discovery (what the runner did before REGRESS-CLEAN-1)."""
    found = set()
    for pat in PATTERNS:
        for f in Path(root).rglob(pat):
            rel = f.relative_to(root)
            if not any(part in skip_dirs for part in rel.parts) and "/reference/" not in str(f):
                found.add(f)
    return found


def select(root, mode, skip_dirs):
    """release -> exactly the manifest; research -> every other discovered bench."""
    manifest = {Path(root) / e for e in load_manifest(root)[0]}
    return sorted(manifest if mode == "release" else discover(root, skip_dirs) - manifest)


def load_manifest(root, rel=MANIFEST):
    """Return (entries, problems). Entries must be sorted, unique and under hardware/tests/."""
    path = Path(root) / rel
    if not path.is_file():
        return [], [f"MANIFEST-MISSING {rel}"]
    entries = [l.strip() for l in path.read_text().splitlines() if l.strip() and not l.lstrip().startswith("#")]
    problems = []
    if len(set(entries)) != len(entries):
        problems.append("MANIFEST-DUPLICATE " + ", ".join(sorted(e for e in set(entries) if entries.count(e) > 1)))
    if entries != sorted(entries):
        problems.append("MANIFEST-UNSORTED entries must be in sorted order")
    problems += [f"MANIFEST-OUTSIDE-SCOPE {e}" for e in entries if not e.startswith(BENCH_ROOT)]
    return entries, problems


def check_manifest(root, skip_dirs):
    """Consistency between the manifest and the tracked benches; returns problem strings."""
    entries, problems = load_manifest(root)
    tracked = _git(root, "ls-files")
    tracked = set(tracked) if tracked is not None else None
    for e in entries:
        if not (Path(root) / e).is_file():
            problems.append(f"LISTED-BENCH-ABSENT {e}")
        elif tracked is not None and e not in tracked:
            problems.append(f"LISTED-BENCH-UNTRACKED {e}")
    problems += [f"ELIGIBLE-BENCH-OMITTED {e}" for e in sorted(set(eligible(root, skip_dirs)) - set(entries))]
    return problems


def untracked_rtl(root):
    """Untracked or ignored RTL sources under hardware/ (they could change module resolution)."""
    files = _git(root, "ls-files", "--others", "--", "hardware")
    return [f"UNTRACKED-RTL {f}" for f in (files or []) if f.endswith(SOURCE_SUFFIXES)]


def normalize(text, root):
    return re.sub(r"\s+", " ", text.replace(str(root), "<ROOT>")).strip()


def signature(text, root):
    return hashlib.sha256(normalize(text, root).encode()).hexdigest()


def verdict(block):
    """Runner verdict class of one test instance's captured output."""
    if re.search(r"\] PASSED\s*$", block, re.M):
        return "PASS"
    if re.search(r"\] TIMEOUT", block):
        return "TIMEOUT"
    if re.search(r"\] NO VERDICT", block):
        return "NO-VERDICT"
    if re.search(r"COMPILE ERROR|PREPROCESS ERROR|make error", block):
        return "COMPILE"
    return "FAIL" if re.search(r"\] FAILED", block) else "UNKNOWN"


def load_known(root, rel=KNOWN):
    """Return {bench path: (kind, signature)}."""
    path = Path(root) / rel
    out = {}
    if path.is_file():
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                p, kind, sig = (x.strip() for x in line.split("|")[:3])
                out[p] = (kind, sig)
    return out


def classify(rel, kind, sig, known):
    """One research instance -> PASS-RESEARCH | KNOWN-FAIL | NEW-FAIL | RESOLVED."""
    if kind == "PASS":
        return "RESOLVED" if rel in known else "PASS-RESEARCH"
    if rel in known and known[rel] == (kind, sig):
        return "KNOWN-FAIL"
    return "NEW-FAIL"


def research_report(results, known, discovered):
    """results: [(rel, kind, sig)]. Returns (lines, exit_status); only NEW-FAIL/MISSING are nonzero."""
    lines, counts = [], {}
    for rel, kind, sig in results:
        c = classify(rel, kind, sig, known)
        counts[c] = counts.get(c, 0) + 1
        why = "" if c in ("PASS-RESEARCH", "KNOWN-FAIL") else f" ({kind}, signature {sig[:12]})"
        lines.append(f"  {c:13} {rel}{why}")
    for rel in sorted(set(known) - set(discovered)):
        counts["MISSING"] = counts.get("MISSING", 0) + 1
        lines.append(f"  {'MISSING':13} {rel} (known failure whose bench was not found)")
    lines.append("  " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return lines, 1 if counts.get("NEW-FAIL") or counts.get("MISSING") else 0
