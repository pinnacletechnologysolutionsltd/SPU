"""Independent verifier: trusts an externally provisioned authority view only."""
from research.qaf_symreg_4.checker import Refusal, canonical, fields, parse, require, verify


def assess(envelope_data, trusted_view_data):
    try:
        e, v = parse(envelope_data), parse(trusted_view_data)
        fields(e, ("version", "authority", "epoch", "revision", "certificate"))
        fields(v, ("version", "authority", "active", "epochs", "registry"))
        require(type(e["version"]) is int and e["version"] == 5 and
                type(v["version"]) is int and v["version"] == 5, "VERSION")
        require(type(e["epoch"]) is int and e["epoch"] > 0 and
                type(e["revision"]) is int and e["revision"] > 0, "IDENTITY")
        require(type(v["epochs"]) is dict and type(v["registry"]) is dict, "SCHEMA")
        require(e["authority"] == v["authority"], "AUTHORITY")
        record = v["epochs"].get(str(e["epoch"]))
        require(type(record) is dict, "UNKNOWN_EPOCH")
        fields(record, ("label", "expired", "snapshots"))
        require(type(record["expired"]) is bool and type(record["snapshots"]) is dict, "SCHEMA")
        ctx = record["snapshots"].get(str(e["revision"]))
        require(type(ctx) is dict and ctx.get("scope") == "epoch_" + str(e["epoch"]), "UNKNOWN_REVISION")
        values = ctx.get("values")
        require(type(values) is dict, "SCHEMA")
        identity = all(k in v["registry"] and v["registry"][k] == pair for k, pair in values.items())
        math = verify(canonical(e["certificate"]), canonical(ctx))
        active_revision = max((int(k) for k in record["snapshots"]), default=0)
        current = (not record["expired"] and type(v["active"]) is int and
                   v["active"] == e["epoch"] and active_revision == e["revision"])
        authorized = math["status"] == "VERIFIED" and identity and current
        mode = "CURRENT" if e["certificate"].get("conclusion", {}).get("current") is not None else "HISTORICAL"
        return {"math": math, "identity": "MATCH" if identity else "MISMATCH",
                "authorization": ("AUTHORIZED_" + mode) if authorized else "REJECTED"}
    except (Refusal, ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        return {"math": {"status": "UNKNOWN"}, "identity": "UNKNOWN",
                "authorization": "REJECTED", "reason": getattr(exc, "code", "INVALID")}


if __name__ == "__main__":
    import json
    import sys
    with open(sys.argv[1], "rb") as f:
        envelope = f.read(65537)
    with open(sys.argv[2], "rb") as f:
        view = f.read(65537)
    result = assess(envelope, view)
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if result["authorization"].startswith("AUTHORIZED_") else 1)
