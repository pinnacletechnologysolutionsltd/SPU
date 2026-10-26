import sys, shutil, os
src, dst, m = sys.argv[1:4]
os.makedirs(dst, exist_ok=True)
for f in ("evaluate_g1_v2.sh", "timing_groups.py"): shutil.copy(os.path.join(src, f), dst)
R = {
 "M1_no_duplicate_block_check": ("timing_groups.py", 'errs.append(f"duplicate details block {key}")', "pass"),
 "M2_no_block_row_crosscheck":  ("timing_groups.py", 'errs.append(f"details block {k} {got} contradicts table row {want}")', "pass"),
 "M3_no_row_without_block":     ("timing_groups.py", 'errs.append(f"table row {k} has no details block")', "pass"),
 "M4_E2_other_groups_ignored":  ("evaluate_g1_v2.sh", "viol=$(printf '%s\\n' \"$TG\" | awk '$1==\"ROW\" {", "viol=$(printf '%s\\n' \"$TG\" | awk '$1==\"ROW\" && $2==\"-\" {"),
 "M5_unreadable_not_timing_fail": ("evaluate_g1_v2.sh", 'if [ -n "$terr" ]; then ft=1; echo', 'if [ -n "$terr" ]; then echo'),
}[m]
p = os.path.join(dst, R[0]); s = open(p).read(); assert s.count(R[1]) == 1, (m, R[1]); open(p, "w").write(s.replace(R[1], R[2]))
