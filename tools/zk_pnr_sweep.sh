#!/usr/bin/env bash
# Karatsuba sidecar P&R A/B sweep.
#
# Rebuilds the full 2-spin x 2-arm x N-seed matrix at a SINGLE commit, so the
# reference and candidate arms are comparable. The 07-22/23 sweep on disk is
# not: its PROBE candidate arm spans three commits (5449055, 8aaaeaa, 15b3118)
# and LUTX moved 22797 -> 22726 between them.
#
# Synthesis is seed-independent -- A7_SEED reaches only the nextpnr --seed
# argument and the artifact name (build_a7.sh:341, :176); INVERTER_VARIANT is
# empty for tensegrity spins. So this synthesises once per (spin, arm) and
# feeds all seeds from it. That assumption is CHECKED, not assumed: see the
# determinism gate below, which fails the run if a second synth at a different
# seed produces a different JSON hash.
#
# Usage:  bash zk_pnr_sweep.sh [n_seeds] [n_parallel]
set -uo pipefail

REPO="${REPO:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -n "$REPO" ] || { echo "run from inside the repo, or set REPO="; exit 1; }
cd "$REPO" || exit 1

N_SEEDS="${1:-10}"
N_PAR="${2:-2}"
BASE_SEED=1
SPINS=(tensegrityprobe tensegritylink)
ARMS=(0 1)

# Fixed seed list: distinct, reproducible, and not a suspiciously round run of
# consecutive integers. Extend by appending, never by renumbering.
ALL_SEEDS=(1 2 3 5 7 11 13 17 19 23 29 31)
SEEDS=("${ALL_SEEDS[@]:0:$N_SEEDS}")

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="build/zk_pnr_campaign/$STAMP"
mkdir -p "$OUT"

COMMIT="$(git rev-parse HEAD)"
DIRTY="$(git status --porcelain | grep -v '^?? ' || true)"

{
    echo "commit=$COMMIT"
    echo "dirty_tracked_files<<EOF"
    echo "$DIRTY"
    echo "EOF"
    echo "seeds=${SEEDS[*]}"
    echo "spins=${SPINS[*]}"
    echo "arms=${ARMS[*]}"
    echo "parallel=$N_PAR"
    echo "started_utc=$(date -u +%FT%TZ)"
} > "$OUT/provenance.txt"

echo "=== ZK P&R sweep ==="
echo "commit  : $COMMIT"
echo "seeds   : ${SEEDS[*]} (${#SEEDS[@]})"
echo "matrix  : ${#SPINS[@]} spins x ${#ARMS[@]} arms x ${#SEEDS[@]} seeds = $(( ${#SPINS[@]} * ${#ARMS[@]} * ${#SEEDS[@]} )) P&R runs"
echo "out     : $OUT"
[ -n "$DIRTY" ] && echo "NOTE: tracked files modified -- recorded in provenance.txt"

jsonpath() {  # spin_upper arm seed
    echo "build/spu_a7_100t_${1}_ZK${2}_S${3}.json"
}

# ---- Phase 1: one synth per (spin, arm) -------------------------------------
echo
echo "--- Phase 1: synthesis (${#SPINS[@]}x${#ARMS[@]}) ---"
for spin in "${SPINS[@]}"; do
    SU="$(echo "$spin" | tr '[:lower:]' '[:upper:]')"
    for arm in "${ARMS[@]}"; do
        t0=$(date +%s)
        ZPHI_KARATSUBA=$arm A7_SEED=$BASE_SEED \
            bash hardware/boards/artix7/build_a7.sh 100t "$spin" synth \
            > "$OUT/synth_${SU}_ZK${arm}.log" 2>&1
        rc=$?
        j="$(jsonpath "$SU" "$arm" "$BASE_SEED")"
        if [ $rc -ne 0 ] || [ ! -f "$j" ]; then
            echo "FATAL: synth failed for $SU ZK$arm (rc=$rc); see $OUT/synth_${SU}_ZK${arm}.log"
            exit 1
        fi
        h="$(sha256sum "$j" | cut -d' ' -f1)"
        echo "  $SU ZK$arm  $(( $(date +%s) - t0 ))s  ${h:0:16}"
        echo "$SU ZK$arm $h" >> "$OUT/synth_hashes.txt"

        # Confirm the selector actually reached the RTL rather than defaulting.
        if grep -q "USE_ZPHI_KARATSUBA=32'0*${arm}\b" "$OUT/synth_${SU}_ZK${arm}.log" \
           || grep -q "USE_ZPHI_KARATSUBA=32'[01]*${arm}$" "$OUT/synth_${SU}_ZK${arm}.log"; then
            :
        else
            echo "  WARN: could not confirm USE_ZPHI_KARATSUBA=$arm in $SU synth log"
        fi
    done
done

# ---- Determinism gate: synth must not depend on the seed --------------------
echo
echo "--- Determinism gate: re-synth PROBE ZK1 at a different seed ---"
GATE_SEED=7
ZPHI_KARATSUBA=1 A7_SEED=$GATE_SEED \
    bash hardware/boards/artix7/build_a7.sh 100t tensegrityprobe synth \
    > "$OUT/synth_gate.log" 2>&1
GJ="$(jsonpath TENSEGRITYPROBE 1 $GATE_SEED)"
BJ="$(jsonpath TENSEGRITYPROBE 1 $BASE_SEED)"
GH="$(sha256sum "$GJ" | cut -d' ' -f1)"
BH="$(sha256sum "$BJ" | cut -d' ' -f1)"
if [ "$GH" != "$BH" ]; then
    echo "FATAL: synthesis is seed-dependent ($BH vs $GH)."
    echo "The one-synth-per-arm shortcut is invalid; synthesise per seed instead."
    echo "seed_independent=NO" >> "$OUT/provenance.txt"
    exit 1
fi
echo "  PASS: identical JSON at seeds $BASE_SEED and $GATE_SEED (${BH:0:16})"
echo "seed_independent=YES" >> "$OUT/provenance.txt"

# ---- Phase 2: P&R every cell ------------------------------------------------
echo
echo "--- Phase 2: place & route (${N_PAR} parallel) ---"
run_pnr() {
    local spin="$1" arm="$2" seed="$3"
    local SU; SU="$(echo "$spin" | tr '[:lower:]' '[:upper:]')"
    local base tgt t0 rc
    base="$(jsonpath "$SU" "$arm" "$BASE_SEED")"
    tgt="$(jsonpath "$SU" "$arm" "$seed")"
    [ "$tgt" = "$base" ] || cp "$base" "$tgt"
    t0=$(date +%s)
    ZPHI_KARATSUBA="$arm" A7_SEED="$seed" \
        bash hardware/boards/artix7/build_a7.sh 100t "$spin" pnr \
        > "$OUT/pnr_${SU}_ZK${arm}_S${seed}.log" 2>&1
    rc=$?
    echo "$SU ZK$arm S$seed rc=$rc $(( $(date +%s) - t0 ))s" >> "$OUT/pnr_status.txt"
    echo "  $SU ZK$arm S$seed  rc=$rc  $(( $(date +%s) - t0 ))s"
}

for spin in "${SPINS[@]}"; do
    for arm in "${ARMS[@]}"; do
        for seed in "${SEEDS[@]}"; do
            while [ "$(jobs -rp | wc -l)" -ge "$N_PAR" ]; do wait -n; done
            run_pnr "$spin" "$arm" "$seed" &
        done
    done
done
wait

cp build/metrics/artix7_100t_TENSEGRITY*_ZK*_S*.json "$OUT/" 2>/dev/null
echo "finished_utc=$(date -u +%FT%TZ)" >> "$OUT/provenance.txt"
echo
echo "=== done: $OUT ==="
grep -c 'rc=0' "$OUT/pnr_status.txt" 2>/dev/null | xargs echo "P&R succeeded:"
grep -v 'rc=0' "$OUT/pnr_status.txt" 2>/dev/null | sed 's/^/  FAILED: /'
