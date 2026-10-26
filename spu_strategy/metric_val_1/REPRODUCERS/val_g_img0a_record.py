"""Record IMG-0A provenance as received. Parses only; executes nothing from the archive."""
import argparse, glob, hashlib, json, os, re
ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); ap.add_argument("--zip-sha", required=True)
a = ap.parse_args()
def emit(i, ok, d): print("RESULT " + json.dumps({"id": "G." + i, "ok": ok, "detail": d}, default=str))
hs = {os.path.basename(f): hashlib.sha256(open(f, "rb").read()).hexdigest() for f in sorted(glob.glob(a.dir + "/*"))}
emit("files_present_hashed", len(hs) == 4, hs)
log = open(a.dir + "/img0a_run.log", errors="replace").read()
m = re.search(r"checks=(\d+)\s+PASS=(\d+)\s+FAIL=(\d+)", log)
r = json.load(open(a.dir + "/img0a_results.json"))
res = r["results"]; npass = sum(1 for x in res if x.get("result") == "PASS")
emit("historical_ledger_32_9_as_received", bool(m) and m.groups() == ("41", "32", "9") and npass == 32,
     {"log_summary": m.groups() if m else None, "json_pass": npass, "json_fail": sum(1 for x in res if x.get("result") == "FAIL"), "json_entries": len(res), "zip_sha256_supplied": a.zip_sha,
      "provenance": "zip supplied by owner; original execution environment (/home/claude/img0a) unverifiable; UNVERIFIED historical summary, not a reproducible acceptance"})
