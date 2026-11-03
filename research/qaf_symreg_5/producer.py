"""An untrusted certificate producer; no authority operations occur here."""
import hashlib
from research.qaf_symreg_4.checker import DOMAIN, canonical, parse


def produce(context_data, authority, epoch, revision, source, target, current=True):
    context = parse(context_data)
    steps, witnesses = [], {}
    for branch, data in sorted(context["branches"].items()):
        claim = data["premises"]["claim"]
        steps.append({"branch": branch, "rule": "PREMISE", "claim": claim,
                      "inputs": [], "premise": "claim"})
        witnesses[branch] = len(steps) - 1
    cert = {"version": 1, "domain": DOMAIN, "scope": context["scope"],
            "context_sha256": hashlib.sha256(context_data).hexdigest(),
            "branches": sorted(context["branches"]), "steps": steps,
            "conclusion": {"rule": "ALL_FEASIBLE_PATHS", "claim": claim,
                           "witnesses": witnesses,
                           "current": {"source": source, "target": target} if current else None}}
    return canonical({"version": 5, "authority": authority, "epoch": epoch,
                      "revision": revision, "certificate": cert})
