"""Versioned JSON artifact: canonical serialization, hash, and an independent reader that recomputes both."""
import hashlib
import json

VERSION = "qcg0-p0-artifact-v1"


def dumps(obj):
    return json.dumps(dict(obj, version=VERSION), sort_keys=True, indent=1, ensure_ascii=True) + "\n"


def readback(path, want_sha, obj):
    """Independent check: re-read the bytes, recompute the hash, parse, and compare with the in-memory object."""
    with open(path, "rb") as f:
        raw = f.read()
    ok_hash = hashlib.sha256(raw).hexdigest() == want_sha
    parsed = json.loads(raw.decode("utf-8"))
    return ok_hash and parsed == json.loads(json.dumps(dict(obj, version=VERSION))) and parsed["version"] == VERSION
