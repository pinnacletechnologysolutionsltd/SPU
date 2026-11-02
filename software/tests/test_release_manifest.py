"""REGRESS-CLEAN-1: release manifest, preflight, selection and known-failure classification."""
import os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import release_manifest as rm

SKIP = {".git", "build", "archive", "__pycache__"}
SIG = "a" * 64


def make_repo(benches, manifest, untracked=()):
    d = Path(tempfile.mkdtemp(prefix="relmf_"))
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    for k, v in (("user.name", "t"), ("user.email", "t@t")):
        subprocess.run(["git", "-C", str(d), "config", k, v], check=True)
    for rel in benches:
        (d / rel).parent.mkdir(parents=True, exist_ok=True); (d / rel).write_text("module m; endmodule\n")
    (d / "tools").mkdir(exist_ok=True)
    (d / rm.MANIFEST).write_text("".join(f"{m}\n" for m in manifest))
    shutil.copy(ROOT / "run_all_tests.py", d); shutil.copy(ROOT / "tools/release_manifest.py", d / "tools")
    subprocess.run(["git", "-C", str(d), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(d), "commit", "-qm", "x"], check=True)
    for rel in untracked:
        (d / rel).parent.mkdir(parents=True, exist_ok=True); (d / rel).write_text("module u; endmodule\n")
    return d


def run_runner(d, **env):
    e = {k: v for k, v in os.environ.items() if k not in ("TB_FILTER", "SPU_TEST_SET")}
    e.update(env)
    return subprocess.run([sys.executable, "run_all_tests.py"], cwd=d, env=e, capture_output=True, text=True, timeout=60)


A, B = "hardware/tests/spu13/a_tb.v", "hardware/tests/spu13/b_tb.v"


class ManifestTests(unittest.TestCase):
    def test_real_manifest_is_consistent(self):
        self.assertEqual(rm.check_manifest(ROOT, SKIP), [])

    def test_omitted_entry_fails_preflight_and_runner(self):
        d = make_repo([A, B], [A])
        self.assertEqual(rm.check_manifest(d, SKIP), [f"ELIGIBLE-BENCH-OMITTED {B}"])
        r = run_runner(d)
        self.assertEqual(r.returncode, 2); self.assertIn("ELIGIBLE-BENCH-OMITTED", r.stdout)

    def test_absent_and_untracked_listed_bench(self):
        d = make_repo([A], [A, "hardware/tests/spu13/zz_tb.v"])
        self.assertIn("LISTED-BENCH-ABSENT hardware/tests/spu13/zz_tb.v", rm.check_manifest(d, SKIP))
        d2 = make_repo([A], [A, B], untracked=[B])
        self.assertIn(f"LISTED-BENCH-UNTRACKED {B}", rm.check_manifest(d2, SKIP))

    def test_malformed_manifest(self):
        d = make_repo([A, B], [B, A, A])
        self.assertTrue(any(p.startswith("MANIFEST-DUPLICATE") for p in rm.check_manifest(d, SKIP)))
        self.assertTrue(any(p.startswith("MANIFEST-UNSORTED") for p in rm.check_manifest(d, SKIP)))

    def test_untracked_rtl_refused_in_release_not_hidden_by_ignore(self):
        d = make_repo([A], [A], untracked=["hardware/rtl/x.v"])
        (d / ".gitignore").write_text("hardware/rtl/ign.v\n"); (d / "hardware/rtl/ign.v").write_text("module i; endmodule\n")
        self.assertEqual(sorted(rm.untracked_rtl(d)), ["UNTRACKED-RTL hardware/rtl/ign.v", "UNTRACKED-RTL hardware/rtl/x.v"])
        r = run_runner(d)
        self.assertEqual(r.returncode, 2); self.assertIn("UNTRACKED-RTL hardware/rtl/x.v", r.stdout)

    def test_clean_and_research_filled_select_same_release_tests(self):
        clean = make_repo([A, B], [A, B])
        filled = make_repo([A, B, "research/e/r_tb.v"], [A, B],
                           untracked=["spu_strategy/q/q_tb.v", "hardware/tests/spu13/wip_tb.v"])
        rel = lambda d, m: [p.relative_to(d).as_posix() for p in rm.select(d, m, SKIP)]
        self.assertEqual(rel(clean, "release"), rel(filled, "release"))
        self.assertEqual(rel(clean, "release"), [A, B])
        self.assertEqual(rel(clean, "research"), [])
        self.assertEqual(rel(filled, "research"),
                         ["hardware/tests/spu13/wip_tb.v", "research/e/r_tb.v", "spu_strategy/q/q_tb.v"])

    def test_invalid_test_set(self):
        self.assertEqual(run_runner(make_repo([A], [A]), SPU_TEST_SET="bogus").returncode, 2)


class ClassificationTests(unittest.TestCase):
    known = {"k": ("COMPILE", SIG)}

    def test_known_failure_is_known_not_pass(self):
        self.assertEqual(rm.classify("k", "COMPILE", SIG, self.known), "KNOWN-FAIL")
        lines, status = rm.research_report([("k", "COMPILE", SIG)], self.known, ["k"])
        self.assertEqual(status, 0); self.assertNotIn("PASS", "".join(lines))

    def test_changed_signature_or_kind_is_new_fail(self):
        self.assertEqual(rm.classify("k", "COMPILE", "b" * 64, self.known), "NEW-FAIL")
        self.assertEqual(rm.classify("k", "FAIL", SIG, self.known), "NEW-FAIL")
        self.assertEqual(rm.research_report([("k", "COMPILE", "b" * 64)], self.known, ["k"])[1], 1)

    def test_unknown_failure_is_nonzero(self):
        self.assertEqual(rm.research_report([("n", "FAIL", SIG)], self.known, ["n", "k"])[1], 1)

    def test_resolved_is_informational(self):
        lines, status = rm.research_report([("k", "PASS", SIG)], self.known, ["k"])
        self.assertEqual(rm.classify("k", "PASS", SIG, self.known), "RESOLVED"); self.assertEqual(status, 0)

    def test_missing_known_bench_is_nonzero(self):
        self.assertEqual(rm.research_report([], self.known, [])[1], 1)

    def test_verdict_and_signature(self):
        self.assertEqual(rm.verdict("[a.v] PASSED\n"), "PASS")
        self.assertEqual(rm.verdict("[a.v] FAILED (vvp exit 1)\nx"), "FAIL")
        self.assertEqual(rm.verdict("[a.v] COMPILE ERROR:\nx"), "COMPILE")
        self.assertEqual(rm.verdict("[a.v] TIMEOUT (hung)"), "TIMEOUT")
        self.assertEqual(rm.signature("err /r/x.v:1  a", "/r"), rm.signature("err  <ROOT>/x.v:1 a", "/zz"))
        self.assertNotEqual(rm.signature("err 1", "/r"), rm.signature("err 2", "/r"))

    def test_known_file_loads_nine_entries(self):
        self.assertEqual(len(rm.load_known(ROOT)), 9)


if __name__ == "__main__":
    unittest.main()
