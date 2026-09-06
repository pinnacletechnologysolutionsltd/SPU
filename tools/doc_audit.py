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
             hardware_evidence reference within +/-10 lines
  stale      numeric claims (test totals) that disagree with the suite
  orphans    tracked .md files linked from no other tracked .md

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


def check_claims(files):
    """Assertive silicon claims with no nearby evidence reference."""
    hits = []
    for f in files:
        if any(k in f for k in SKIP_PARTS) or '/blog/' in f:
            continue
        lines = read(f).split('\n')
        for i, line in enumerate(lines):
            m = CLAIM.search(line)
            if not m or NEG.search(line[:m.start()]):
                continue
            if CITE.search('\n'.join(lines[max(0, i - 10):i + 11])):
                continue
            hits.append({'file': f, 'line': i + 1, 'text': line.strip()[:100]})
    return hits


def check_stale(files, actual):
    """Numeric suite totals that disagree with the measured value."""
    hits = []
    for f in files:
        if any(k in f for k in SKIP_PARTS):
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
            t = m.group(1) and m.group(2).split('#')[0].strip()
            if not t or t.startswith(('http', 'mailto')):
                continue
            linked.add(t.lstrip('/') if t.startswith('/') else os.path.normpath(os.path.join(d, t)))
    roots = ('README.md', 'AGENTS.md', 'CLAUDE.md', 'GEMINI.md', 'CONTRIBUTING.md', 'LICENSING.md')
    return [{'file': f} for f in files
            if f not in linked
            and not f.startswith(('docs/archive/', 'docs/SESSION_HANDOVER'))
            and os.path.basename(f) not in roots]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', choices=['links', 'claims', 'stale', 'orphans', 'all'], default='all')
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

    if args.json:
        json.dump(res, sys.stdout, indent=1)
        print()
        return 0

    print(f"scanned {len(files)} tracked markdown files\n")
    for key, label in [('links', 'BROKEN INTERNAL LINKS'),
                       ('claims', 'UNCITED SILICON CLAIMS (assertive, +/-10 line window)'),
                       ('stale', 'STALE SUITE TOTALS'),
                       ('orphans', 'ORPHANED DOCS (linked from no other tracked .md)')]:
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
