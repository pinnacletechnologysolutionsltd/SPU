#!/usr/bin/env python3
"""doc_audit.py — mechanical documentation audit for the SPU repository.

WHY THIS EXISTS. `tools/verify_repo.sh`'s evidence-citation gate is
DIFF-SCOPED by design (governance rewrite, 2026-08-19): it checks only lines
changed since HEAD, so pre-existing documentation has never been audited by
it. This tool sweeps the whole corpus instead. It complements the gate; it
does not replace it.

WHAT IT CHECKS
  links      internal markdown links whose target does not exist
  claims     assertive "silicon-verified/proven" statements with no
             hardware_evidence reference anywhere in their enclosing
             markdown section
  stale      numeric claims (test totals) that disagree with the suite
  orphans    tracked .md files linked from no other tracked .md
  contra     documents asserting a status a later decision superseded

WHAT IT IS NOT. Regex over prose. Every hit needs a human or a reviewer to
judge; several classes have legitimate exceptions (a spec may cite evidence
in a distant section; an orphan may be intentionally standalone). A finding
means "go and look", never "this is wrong". Same discipline as
tools/rtl_instantiation_audit.py.

Usage:
    python3 tools/doc_audit.py                # all checks
    python3 tools/doc_audit.py --check links
    python3 tools/doc_audit.py --json

CC0 1.0 Universal.
"""
import argparse, json, os, re, subprocess, sys
from collections import Counter

SKIP_PARTS = ('docs/archive/', 'SESSION_HANDOVER', 'hardware_evidence')
LINK = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
CLAIM = re.compile(r'(silicon[- ](verified|proven)|verified in silicon|proven (on|in) silicon)', re.I)
NEG = re.compile(r'\b(not|never|no|without|nor|cannot|un)\b[^.]{0,60}$', re.I)
CITE = re.compile(r'hardware_evidence|§ ?3\.\d|section 3\.\d', re.I)
TOTAL = re.compile(r'Total PASS:? *`?(\d+)')

# Superseded-status table. This encodes JUDGEMENT explicitly rather than
# pretending to derive it: each entry names the decision that superseded the
# topic, so a reviewer can dispute the entry itself rather than the output.
# Add to it when a direction is shelved; that is the maintenance cost.
SUPERSEDED = [
    {'topic': 'SOM / anomaly-detection wedge',
     'since': '2026-09-03',
     'decision': 'spu_strategy/contract_som_vs_processor_priority_2026-09-03.md',
     'asserts_current': re.compile(
         r'current (proven )?product path|current SPU-13 platform wedge|'
         r'the current wedge|next sensor bench step|current product-shaped artifact', re.I)},
    {'topic': 'SPU-4 as the commercial direction',
     'since': '2026-09-03',
     'decision': 'superseded by the graphics-first decision',
     'asserts_current': re.compile(r'separate commercial direction is now', re.I)},
    {'topic': 'southbridge SPI stack as the hardware direction',
     'since': '2026-09-05',
     'decision': 'docs/SESSION_HANDOVER_2026-09-05.md section 8 (parked)',
     'asserts_current': re.compile(r'## Current Hardware Direction', re.I)},
    {'topic': 'funding-gated scaling',
     'since': '2026-09-03',
     'decision': 'bootstrap posture; see strategy-pivot record',
     'asserts_current': re.compile(r'funding target', re.I)},
]


def tracked_md():
    out = subprocess.run(['git', 'ls-files', '*.md'], capture_output=True, text=True).stdout
    return sorted(out.split())


def read(path):
    try:
        return open(path, errors='replace').read()
    except OSError:
        return ''


def check_links(files):
    bad = []
    for f in files:
        d = os.path.dirname(f)
        txt = read(f)
        for m in LINK.finditer(txt):
            tgt = m.group(2).split('#')[0].strip()
            if not tgt or tgt.startswith(('http://', 'https://', 'mailto:', 'file://')):
                continue
            p = tgt.lstrip('/') if tgt.startswith('/') else os.path.normpath(os.path.join(d, tgt))
            if not os.path.exists(p):
                bad.append({'file': f, 'line': txt[:m.start()].count('\n') + 1,
                            'text': m.group(1)[:50], 'target': tgt})
    return bad


HEADING = re.compile(r'^#{1,6} ')


def _section_bounds(lines, i):
    """Enclosing markdown section: nearest heading at/above i, to the next one.

    Rev 2 (external review, 2026-09-06): a +/-10 line window multi-counted
    table rows and missed citations that sit legitimately elsewhere in the
    same section. A 7-row instruction table whose section cites its evidence
    once was counted as 6 separate violations.
    """
    start = 0
    for j in range(i, -1, -1):
        if HEADING.match(lines[j]):
            start = j
            break
    end = len(lines)
    for j in range(i + 1, len(lines)):
        if HEADING.match(lines[j]):
            end = j
            break
    return start, end


def _block_bounds(lines, i):
    """Enclosing blank-line-delimited block: one paragraph, or one table."""
    a = i
    while a > 0 and lines[a - 1].strip() and not HEADING.match(lines[a - 1]):
        a -= 1
    b = i
    while b + 1 < len(lines) and lines[b + 1].strip() and not HEADING.match(lines[b + 1]):
        b += 1
    return a, b + 1


def _section_declares_source(lines, sec_a, sec_b):
    """True if the section's OPENING paragraph cites evidence.

    That is what "the section explicitly declares a shared evidence source"
    means operationally: a citation in the lead paragraph covers the section.
    A citation buried in an unrelated paragraph further down does NOT.
    """
    j = sec_a + 1
    while j < sec_b and not lines[j].strip():
        j += 1
    if j >= sec_b:
        return False
    k = j
    while k < sec_b and lines[k].strip():
        k += 1
    return bool(CITE.search('\n'.join(lines[j:k])))


def check_claims(files):
    """Assertive silicon claims with no evidence pointer covering them.

    Scope model (external review + operator, 2026-09-06). A claim is covered
    when a citation appears in EITHER its own paragraph/table block, OR the
    opening paragraph of its section -- the latter being the only thing that
    counts as declaring a shared source. Whole-section scope was rejected as
    too generous: it would bless unrelated claims in a long section.
    Consecutive rows of one table are reported as ONE grouped finding.
    """
    hits = []
    for f in files:
        if any(k in f for k in SKIP_PARTS) or '/blog/' in f:
            continue
        lines = read(f).split('\n')
        seen_blocks = set()
        for i, line in enumerate(lines):
            m = CLAIM.search(line)
            if not m:
                continue
            # Negation may sit on the PREVIOUS line -- 80-column prose wraps
            # "...no\nregression risk to anything currently silicon-proven."
            prev = lines[i - 1] if i > 0 else ''
            if NEG.search((prev + ' ' + line[:m.start()])[-90:]):
                continue
            sec_a, sec_b = _section_bounds(lines, i)
            blk_a, blk_b = _block_bounds(lines, i)
            if CITE.search('\n'.join(lines[blk_a:blk_b])):
                continue
            if _section_declares_source(lines, sec_a, sec_b):
                continue
            key = (f, blk_a)
            if key in seen_blocks:
                for h in hits:
                    if h.get('_key') == key:
                        h['rows'] += 1
                continue
            seen_blocks.add(key)
            hits.append({'file': f, 'line': i + 1, 'text': line.strip()[:100],
                         'rows': 1, '_key': key})
    for h in hits:
        h.pop('_key', None)
    return hits


def check_stale(files, actual):
    """Numeric suite totals that disagree with the measured value."""
    hits = []
    for f in files:
        # DOC_AUDIT_* quotes stale values by design when reporting them.
        if any(k in f for k in SKIP_PARTS) or 'DOC_AUDIT_' in f:
            continue
        txt = read(f)
        for m in TOTAL.finditer(txt):
            n = int(m.group(1))
            if actual is not None and n != actual:
                hits.append({'file': f, 'line': txt[:m.start()].count('\n') + 1,
                             'claims': n, 'actual': actual})
    return hits


def check_orphans(files):
    linked = set()
    for f in files:
        d = os.path.dirname(f)
        for m in LINK.finditer(read(f)):
            t = m.group(2).split('#')[0].strip()
            if not t or t.startswith(('http', 'mailto')):
                continue
            linked.add(t.lstrip('/') if t.startswith('/') else os.path.normpath(os.path.join(d, t)))
    roots = ('README.md', 'AGENTS.md', 'CLAUDE.md', 'GEMINI.md', 'CONTRIBUTING.md', 'LICENSING.md')
    return [{'file': f} for f in files
            if f not in linked
            and not f.startswith(('docs/archive/', 'docs/SESSION_HANDOVER'))
            and os.path.basename(f) not in roots]


def check_contradictions(files):
    """Assertions of a status that a later recorded decision superseded."""
    hits = []
    for f in files:
        # DOC_AUDIT_* quotes the offending text by design; excluding it stops
        # the audit flagging itself for reporting what it found.
        if any(k in f for k in ('docs/archive/', 'SESSION_HANDOVER',
                                'spu_strategy/', 'DOC_AUDIT_')):
            continue
        txt = read(f)
        for entry in SUPERSEDED:
            for m in entry['asserts_current'].finditer(txt):
                hits.append({'file': f, 'line': txt[:m.start()].count('\n') + 1,
                             'topic': entry['topic'], 'since': entry['since'],
                             'decision': entry['decision'],
                             'text': m.group(0)[:60]})
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check',
                    choices=['links', 'claims', 'stale', 'orphans', 'contra', 'all'],
                    default='all')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--actual-pass', type=int, default=None,
                    help='measured "Total PASS" to compare stale claims against')
    args = ap.parse_args()

    if not os.path.isdir('docs'):
        sys.exit('run from the repository root')

    files = tracked_md()
    res = {}
    if args.check in ('links', 'all'):
        res['links'] = check_links(files)
    if args.check in ('claims', 'all'):
        res['claims'] = check_claims(files)
    if args.check in ('stale', 'all'):
        res['stale'] = check_stale(files, args.actual_pass)
    if args.check in ('orphans', 'all'):
        res['orphans'] = check_orphans(files)
    if args.check in ('contra', 'all'):
        res['contra'] = check_contradictions(files)

    if args.json:
        json.dump(res, sys.stdout, indent=1)
        print()
        return 0

    print(f"scanned {len(files)} tracked markdown files\n")
    for key, label in [('links', 'BROKEN INTERNAL LINKS'),
                       ('claims', 'UNCITED SILICON CLAIMS (assertive, paragraph-scoped, tables grouped)'),
                       ('stale', 'STALE SUITE TOTALS'),
                       ('orphans', 'ORPHANED DOCS (linked from no other tracked .md)'),
                       ('contra', 'SUPERSEDED STATUS ASSERTED AS CURRENT')]:
        if key not in res:
            continue
        rows = res[key]
        print(f"== {label}: {len(rows)} ==")
        for f, n in Counter(r['file'] for r in rows).most_common(10):
            print(f"   {n:>4}  {f}")
        print()
    print("Every hit needs judgement. This is a regex sweep, not an elaborator.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
