"""Step G1-E1/E2: read every timing group of a Vivado report_timing_summary and cross-check tables against Timing Details blocks.

Usage: python3 -I timing_groups.py synth_timing_summary.rpt
Prints one line per item; the evaluator consumes them:
  ROW   <group> <from> <to> <wns> <tns> <tns_fail> <tns_total> <whs> <ths> <ths_fail> <ths_total>
  BLOCK <group> <from> <to> <setup_fail> <setup_ws> <setup_tv> <hold_fail> <hold_ws> <hold_tv>
  ERR   <reason>
<group> is "-" for the per-clock-pair tables (Intra, Inter) and the path-group name for "Other Path Groups" (e.g. **async_default**).
Fail-closed: a missing section, a malformed row, a duplicate key, a block without a row, a row without a block, or a block whose numbers
contradict its row is an ERR. A legitimate extra group (async_default) is a separate key, never a duplicate.
"""
import re
import sys

SECTIONS = ("| Intra Clock Table", "| Inter Clock Table", "| Other Path Groups Table", "| Timing Details")


def main(path):
    lines = open(path).read().split("\n")
    out, errs = [], []
    idx = {}
    for s in SECTIONS:
        hits = [i for i, l in enumerate(lines) if l.startswith(s)]
        if len(hits) != 1:
            errs.append(f"section '{s}' found {len(hits)} times, expected 1")
        else:
            idx[s] = hits[0]
    if errs:
        return [f"ERR {e}" for e in errs]

    def table(start, end, width, header, keyf, first):
        rows = []
        for l in lines[idx[start] + 1:idx[end]]:
            t = l.split()
            if not t or t[0] == header or set(t[0]) == {"-"} or l.startswith("|") or set(l.strip()) == {"-"}:
                continue
            if len(t) != width:
                errs.append(f"malformed row in {start.strip('| ')}: {l.strip()}")
                continue
            rows.append((keyf(t), t[first:first + 8]))
        return rows

    rows = table("| Intra Clock Table", "| Inter Clock Table", 13, "Clock", lambda t: ("-", t[0], t[0]), 1)
    rows += table("| Inter Clock Table", "| Other Path Groups Table", 10, "From", lambda t: ("-", t[0], t[1]), 2)
    rows += table("| Other Path Groups Table", "| Timing Details", 11, "Path", lambda t: (t[0], t[1], t[2]), 3)
    rowmap = {}
    for k, v in rows:
        if k in rowmap:
            errs.append(f"duplicate table row {k}")
        rowmap[k] = v

    blocks, group, key, cur = {}, None, None, None
    num = r"(-?[0-9.]+|inf|NA)"
    for l in lines[idx["| Timing Details"] + 1:]:
        m = re.match(r"^Path Group:\s+(\S+)\s*$", l)
        if m:
            group = m.group(1)
            continue
        m = re.match(r"^From Clock:\s+(\S+)\s*$", l)
        if m:
            frm = m.group(1)
            continue
        m = re.match(r"^  To Clock:\s+(\S+)\s*$", l)
        if m:
            key = (group or "-", frm, m.group(1))
            group = None
            if key in blocks:
                errs.append(f"duplicate details block {key}")
            cur = blocks.setdefault(key, {})
            continue
        m = re.match(r"^(Setup|Hold)\s*:\s+(\d+)\s+Failing Endpoints,\s+Worst Slack\s+" + num + r"(?:ns)?,\s+Total Violation\s+" + num + r"(?:ns)?", l)
        if m and cur is not None and m.group(1) not in cur:
            cur[m.group(1)] = (m.group(2), m.group(3), m.group(4))

    for k, b in blocks.items():
        if "Setup" not in b or "Hold" not in b:
            errs.append(f"details block {k} lacks Setup/Hold summary")
            continue
        if k not in rowmap:
            errs.append(f"details block {k} has no table row")
            continue
        wns, tns, tf, tt, whs, ths, hf, ht = rowmap[k]
        want = (tf, wns, tns, hf, whs, ths)
        got = b["Setup"] + b["Hold"]
        if tuple(got) != (want[0], want[1], want[2], want[3], want[4], want[5]):
            errs.append(f"details block {k} {got} contradicts table row {want}")
    for k in rowmap:
        if k not in blocks:
            errs.append(f"table row {k} has no details block")

    for k, v in rows:
        out.append("ROW " + " ".join(k) + " " + " ".join(v))
    for k, b in blocks.items():
        if "Setup" in b and "Hold" in b:
            out.append("BLOCK " + " ".join(k) + " " + " ".join(b["Setup"] + b["Hold"]))
    out += [f"ERR {e}" for e in errs]
    return out


if __name__ == "__main__":
    print("\n".join(main(sys.argv[1])))
