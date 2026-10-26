#!/usr/bin/env bash
# SPU-METRIC-VAL-1 runner. Modes:
#   metric_val_1_run.sh run      <OUT>   one attempt, consumes the ledger slot
#   metric_val_1_run.sh identity <OUT>   source-identity checks only, consumes nothing
#   metric_val_1_run.sh selftest <OUT>   limit/confinement demonstration, consumes nothing
# OUT must be a NEW child of build/metric_val_1/. Never modifies the pinned clone or the worktree.
set -euo pipefail
umask 077
MODE="${1:?mode: run|selftest}"; OUT="${2:?output dir}"
REPO=/home/user/Projects/hardware/SPU
CLONE=/home/user/Projects/hardware/spu-release-candidates/release-3d-final
PIN=4e0d5b908e5bb1e0e86ba979b87affb83bd2a372
HERE="$REPO/spu_strategy/metric_val_1"
BUDGET_S=840          # inner deadline; outer detached runner timeout is 900
AS_BYTES=$((2*1024**3))
case "$OUT" in "$REPO"/build/metric_val_1/*) ;; *) echo "REFUSED: OUT outside build/metric_val_1"; exit 2;; esac
[ ! -e "$OUT" ] || { echo "REFUSED: OUT exists"; exit 2; }
ulimit -v $((AS_BYTES/1024))
START=$(date +%s.%N); DEADLINE=$(python3 -I -c "print($START+$BUDGET_S)")
mkdir -p "$OUT"/{stages,work,home,logs}; echo "$START" > "$OUT/start_epoch"

stage() { # name timeout cmd...
  local n="$1" t="$2"; shift 2
  python3 -I "$HERE/stage_run.py" --name "$n" --stages "$OUT/stages" --cwd "$OUT/work" \
    --timeout "$t" --deadline-epoch "$DEADLINE" --as-bytes "$AS_BYTES" --home "$OUT/home" -- "$@" || true
}
finish() { # terminal marker, separate from audit dispositions
  python3 -I "$HERE/assemble_results.py" --out "$OUT" --mode "$MODE" --start "$START" || true
}

if [ "$MODE" = selftest ]; then
  stage st_timeout 2 sleep 30
  stage st_memcap 20 python3 -I -c 'x=bytearray(3*1024**3)'
  stage st_confine 20 python3 -I -c 'open("confine_probe.txt","w").write("x"); import os; print(os.getcwd())'
  stage st_ok 20 python3 -I -c 'print("ok")'
  finish; cat "$OUT/TERMINAL"; exit 0
fi
[ "$MODE" = run ] || [ "$MODE" = identity ] || { echo "bad mode"; exit 2; }

# --- one-attempt accounting: ledger slot is consumed before anything else ---
LEDGER="$REPO/build/metric_val_1/ATTEMPT_LEDGER"
[ "$MODE" = identity ] || ( set -o noclobber; echo "run_dir=$OUT started=$(date -u +%FT%TZ)" > "$LEDGER" ) 2>/dev/null \
  || { echo "REFUSED: attempt ledger exists ($LEDGER)"; rmdir "$OUT"/* "$OUT" 2>/dev/null; exit 2; }

# --- source identity (read-only): pinned clone, then immutable archive copy ---
[ "$(git -C "$CLONE" rev-parse HEAD)" = "$PIN" ] || { echo "IDENTITY FAIL: HEAD"; echo IDENTITY_FAIL > "$OUT/TERMINAL"; exit 3; }
[ -z "$(git -C "$CLONE" status --porcelain)" ]   || { echo "IDENTITY FAIL: dirty clone"; echo IDENTITY_FAIL > "$OUT/TERMINAL"; exit 3; }
git -C "$CLONE" status --porcelain > "$OUT/logs/clone_status_pre.txt"
mkdir "$OUT/src" "$OUT/wt"
git -C "$CLONE" archive "$PIN" software hardware knowledge docs/hardware_evidence.md | tar -x -C "$OUT/src"
tree_hash() { (cd "$1" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1); }
SRC_PRE=$(tree_hash "$OUT/src"); chmod -R a-w "$OUT/src"
# worktree files are COPIED read-only for the dev-vs-pinned comparison; originals are hashed pre/post
WT_FILES="software/spu_vm.py hardware/rtl/core/shared/davis_gate_dsp.v software/lib/rotc_thirds_native.py"
: > "$OUT/logs/wt_hash_pre.txt"
for f in $WT_FILES; do mkdir -p "$OUT/wt/$(dirname "$f")"; cp "$REPO/$f" "$OUT/wt/$f"; sha256sum "$REPO/$f" >> "$OUT/logs/wt_hash_pre.txt"; done
chmod -R a-w "$OUT/wt"
git -C "$REPO" status --porcelain | sha256sum > "$OUT/logs/repo_status_pre.sha"
{ echo "python=$(python3 -V)"; { iverilog -V 2>&1 | head -1; } || true; echo "git=$(git --version)"; uname -a
  echo "ulimit_v_kib=$(ulimit -v)"; echo "pin=$PIN"; echo "src_tree_sha256=$SRC_PRE"; } > "$OUT/logs/tools_identity.txt"
IMG="$REPO/build/metric_val_1/prep_01/img0a_received"
sha256sum "$IMG"/* > "$OUT/logs/img0a_hashes.txt"

if [ "$MODE" = identity ]; then cat "$OUT/logs/tools_identity.txt"; echo "IDENTITY_OK"; chmod -R u+w "$OUT/src" "$OUT/wt"; exit 0; fi
S="$OUT/src"; R="$HERE/REPRODUCERS"
# development-tree view: pinned software/ with only the worktree spu_vm.py overlaid (original untouched)
mkdir "$OUT/wt_tree"; cp -r --no-preserve=mode "$S/software" "$OUT/wt_tree/software"
cp --no-preserve=mode "$OUT/wt/software/spu_vm.py" "$OUT/wt_tree/software/spu_vm.py"
stage val_g 30  python3 -I "$R/val_g_img0a_record.py" --dir "$IMG" --zip-sha 0f4b0f19ea6bf6239f5802684da46685947facfce40886421d2c2c5a5958ddf0
stage val_a 60  python3 -I "$R/val_a_vm_metric.py" --src "$S" --label pinned
stage val_a_wt 60 python3 -I "$R/val_a_vm_metric.py" --src "$OUT/wt_tree" --label worktree
stage val_b_ref 60 python3 -I "$R/val_b_davis_ref.py" gen --out "$OUT/work"
for dev in SIM GW5A; do
  stage "val_b_compile_$dev" 60 iverilog -g2012 -DDEV="\"$dev\"" -o "$OUT/work/davis_$dev.vvp" "$R/val_b_davis_harness.v" \
    "$S/hardware/rtl/core/shared/davis_gate_dsp.v" "$S/hardware/tests/common/sim_spu_gowin_multiplier.v"
  stage "val_b_run_$dev" 60 vvp -n "$OUT/work/davis_$dev.vvp" +VEC="$OUT/work/vectors.hex" +OBS="$OUT/work/obs_$dev.txt"
done
stage val_b_check 60 python3 -I "$R/val_b_davis_ref.py" check --work "$OUT/work"
stage val_c 60  python3 -I "$R/val_c_quadray.py" --src "$S"
stage val_d 60  python3 -I "$R/val_d_transforms.py" --src "$S"
stage val_e 60  bash "$R/val_e_static.sh" "$S" "$REPO"
stage val_f 60  python3 -I "$R/val_f_vm_diff.py" --pinned "$S" --worktree "$OUT/wt" --repo-wt "$REPO"

# --- post-run integrity ---
SRC_POST=$(tree_hash "$OUT/src")
git -C "$CLONE" status --porcelain > "$OUT/logs/clone_status_post.txt"
: > "$OUT/logs/wt_hash_post.txt"; for f in $WT_FILES; do sha256sum "$REPO/$f" >> "$OUT/logs/wt_hash_post.txt"; done
git -C "$REPO" status --porcelain | sha256sum > "$OUT/logs/repo_status_post.sha"
{ echo "src_tree_pre=$SRC_PRE"; echo "src_tree_post=$SRC_POST"; echo "clone_head_post=$(git -C "$CLONE" rev-parse HEAD)"; } > "$OUT/logs/integrity.txt"
finish; cat "$OUT/TERMINAL"
