"""QCG-0 P0 runner: one invocation, contract §9. Exit 0 only after all gates pass and RUNNER_DONE is written last; 90 on a cap breach."""
import argparse
import hashlib
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import artifact
import stages
from events import OpBudget
from writer import CapBreach, Out


def main(argv, build=None, verdict=None):
    """`build`/`verdict` default to the registered stages; tests inject small stand-ins (no P0 computation)."""
    build, verdict = build or stages.build, verdict or stages.verdict
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Out(ap.parse_args(argv).out)
    try:
        R = build()
        ok = verdict(R)
        text = artifact.dumps(R)
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        out.write("results.json", text)
        out.write("results.sha256", "%s  results.json\n" % sha)
        rb = artifact.readback(str(Path(out.dir) / "results.json"), sha, R)
        out.write("readback.txt", "readback=%s\n" % ("OK" if rb else "MISMATCH"))
        out.say("QCG0_P0 verdict=%s readback=%s mutants_killed=%d ops=%d" % (
            "PASS" if ok and rb else "FAIL", rb, sum(m["killed"] for m in R.get("stage6_mutants", {}).values()), R.get("counted_operations", -1)))
        if not (ok and rb):
            return 1                                   # artifacts persisted, but no RUNNER_DONE: the launcher classifies FAILED
        out.write("RUNNER_DONE", "")                    # always the last file written
        return 0
    except (CapBreach, OSError):
        return out.breach()
    except OpBudget as e:                              # the operation that would exceed the budget was not executed
        try:
            out.say("OP_BUDGET_EXHAUSTED before %s" % e.event)
        except (CapBreach, OSError):
            return out.breach()
        return 92
    except Exception as e:  # noqa: BLE001  (bounded report; never exit 124)
        try:
            out.say("RUNNER_ERROR %s" % repr(e)[:200])
        except (CapBreach, OSError):
            return out.breach()
        return 2


if __name__ == "__main__":
    rc = main(sys.argv[1:])
    sys.exit(rc if rc != 124 else 1)
