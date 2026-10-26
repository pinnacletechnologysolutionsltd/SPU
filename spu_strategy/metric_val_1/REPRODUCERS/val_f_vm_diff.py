"""Read-only comparison of geometry-relevant VM functions: pinned 4e0d5b9 vs current development worktree (CPU-PROFILE-2 dirty)."""
import argparse, ast, hashlib, json, subprocess
ap = argparse.ArgumentParser(); ap.add_argument("--pinned", required=True); ap.add_argument("--worktree", required=True); ap.add_argument("--repo-wt", required=True)
a = ap.parse_args()
def emit(i, ok, d): print("RESULT " + json.dumps({"id": "F." + i, "ok": ok, "detail": d}, default=str))
def funcs(path):
    src = open(path).read(); tree = ast.parse(src); out = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef):
            for f in n.body:
                if isinstance(f, ast.FunctionDef): out[f"{n.name}.{f.name}"] = hashlib.sha256(ast.get_source_segment(src, f).encode()).hexdigest()[:16]
        elif isinstance(n, ast.FunctionDef) and n.col_offset == 0: out[n.name] = hashlib.sha256(ast.get_source_segment(src, n).encode()).hexdigest()[:16]
    return out
P = funcs(a.pinned + "/software/spu_vm.py"); W = funcs(a.worktree + "/software/spu_vm.py")
names = ["RationalSurd.__mul__", "RationalSurd.quadrance", "RationalSurd.rotate_phi", "QuadrayVector.normalize", "QuadrayVector.rotate", "QuadrayVector.cycle",
         "QuadrayVector.quadrance", "QuadrayVector.dot", "QuadrayVector.spread", "QuadrayVector.hex_project", "QuadrayVector.circulant_rotate", "rs_min", "rs_lt", "spread_from_quadrances"]
rows = {n: {"pinned": P.get(n), "worktree": W.get(n), "identical": P.get(n) == W.get(n) and P.get(n) is not None} for n in names}
emit("geometry_function_bodies_identical_pinned_vs_worktree", all(r["identical"] for r in rows.values()), rows)
emit("other_function_differences_recorded", True, {"changed_or_added": sorted(k for k in set(P) | set(W) if P.get(k) != W.get(k))[:60]})
d = subprocess.run(["git", "-C", a.repo_wt, "diff", "--stat", "--", "software/spu_vm.py"], capture_output=True, text=True)
emit("worktree_vs_HEAD_stat_recorded", True, d.stdout.strip()[-200:])
