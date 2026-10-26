"""Test helper (offline only): mutate a COPY of a real report_timing_summary to build E1/E2 negative controls.
Usage: python3 -I edit_ts.py FILE OP [ARGS...]
  drop_block G F T | dup_block G F T          remove / duplicate a Timing Details block (G '-' = clock-pair block)
  set_block_hold G F T FAIL WS TV             rewrite a block's Hold summary line
  drop_row G F T | dup_row G F T | break_row G F T   remove / duplicate / drop the last token of a table row
  set_row_hold G F T WHS THS FAIL             rewrite a row's WHS, THS and THS failing columns
  drop_section HEADER                         remove a section header line, e.g. '| Other Path Groups Table'
"""
import re
import sys

path, op, args = sys.argv[1], sys.argv[2], sys.argv[3:]
L = open(path).read().split("\n")


def block_span(g, f, t):
    """Return [start, end) of the block whose header is (g, f, t); start includes a preceding 'Path Group:' line."""
    for i, l in enumerate(L):
        if l == f"From Clock:  {f}" and i + 1 < len(L) and L[i + 1] == f"  To Clock:  {t}":
            named = i > 0 and L[i - 1].startswith("Path Group:")
            if (g == "-" and not named) or (named and L[i - 1].split()[-1] == g):
                s = i - 1 if named else i
                e = next(j for j in range(i + 2, len(L)) if re.match(r"^-{20,}$", L[j]))
                return s, e
    sys.exit(f"block {g} {f} {t} not found")


def row_index(g, f, t):
    for i, l in enumerate(L):
        x = l.split()
        if g == "-" and f == t and len(x) == 13 and x[0] == f:
            return i
        if g == "-" and f != t and len(x) == 10 and x[0] == f and x[1] == t:
            return i
        if g != "-" and len(x) == 11 and x[:3] == [g, f, t]:
            return i
    sys.exit(f"row {g} {f} {t} not found")


if op == "drop_block":
    s, e = block_span(*args); del L[s:e]
elif op == "dup_block":
    s, e = block_span(*args); L[e:e] = L[s - 1:e] if L[s - 1].startswith("---") else L[s:e]
elif op == "set_block_hold":
    s, e = block_span(*args[:3]); fail, ws, tv = args[3:]
    for j in range(s, e):
        if L[j].startswith("Hold  :"):
            L[j] = f"Hold  :  {fail:>11}  Failing Endpoints,  Worst Slack  {ws:>10}ns,  Total Violation  {tv:>10}ns"
elif op == "drop_row":
    del L[row_index(*args)]
elif op == "dup_row":
    i = row_index(*args); L.insert(i + 1, L[i])
elif op == "break_row":
    i = row_index(*args); L[i] = " ".join(L[i].split()[:-1])
elif op == "set_row_hold":
    i = row_index(*args[:3]); whs, ths, fail = args[3:]; x = L[i].split()
    k = {13: 5, 10: 6, 11: 7}[len(x)]          # index of WHS in the token list
    x[k], x[k + 1], x[k + 2] = whs, ths, fail
    L[i] = "  ".join(x)
elif op == "drop_section":
    L = [l for l in L if not l.startswith(args[0])]
else:
    sys.exit(f"unknown op {op}")
open(path, "w").write("\n".join(L))
