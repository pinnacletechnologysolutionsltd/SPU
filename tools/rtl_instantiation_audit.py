#!/usr/bin/env python3
"""rtl_instantiation_audit.py — which RTL modules are reachable from a board
top, from a testbench, from both, or from neither?

WHY THIS EXISTS. Twice in two days, both by accident, both harbouring real
defects:

  * hal_hdmi.v      — never instantiated by any top on any board (2026-09-04)
  * spu_gpu_top.v   — never instantiated by any top on any board (2026-09-05),
                      and could not even be simulated: an unreset coefficient
                      output turned every pixel X. Three defects in one module.

With board-builds-are-never-rebuilt already on record, that is a pattern, not
a coincidence: RTL gets written, maybe unit-tested, never integrated, and
rots quietly. This makes the question mechanical instead of accidental.

WHAT IT DOES NOT DO. This is a regex parser, not an elaborator. It resolves
instantiation by module NAME, ignores `ifdef, and cannot see a module only
reached through a generate branch it fails to parse. Treat a hit as "go and
look", never as proof. Yosys `hierarchy -check -top <top>` is the authority
for any single top; this is the sweep across all of them.

Roots are collected from the build scripts themselves (`-top X`, `TOP=X`), so
a top that no build script names is correctly reported as unreachable.

Usage:
    python3 tools/rtl_instantiation_audit.py               # summary
    python3 tools/rtl_instantiation_audit.py --class dead  # one class only
    python3 tools/rtl_instantiation_audit.py --json        # machine-readable

Classes:
    dead      no board top and no testbench reaches it
    tb-only   a testbench reaches it, no board top does  (the hal_hdmi class)
    no-tb     a board top reaches it, no testbench does  (goes to silicon
              unsimulated; board tops themselves are expected here)
    dup       modules DEFINED in more than one file. Which definition wins
              depends on elaboration order, so a stub can silently shadow a
              real implementation. Vendor-primitive simulation stubs are
              expected here; a stub/implementation pair is not.
    archive   .v files outside hardware/ that no scan covers

CC0 1.0 Universal.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

RTL_ROOT = "hardware"
SKIP_DIRS = {"build", "archive", ".git", "__pycache__", "node_modules", ".venv"}
# "." picks up build scripts that sit in the repository root -- two do
# (build_25k_blinky_uart*.sh), and missing them made their tops look dead.
BUILD_SEARCH = [".", "hardware/boards", "tools"]

# Words that can appear where a module type would and are not module types.
KEYWORDS = set("""
module endmodule input output inout reg wire logic parameter localparam assign
always initial begin end if else case casez casex endcase for while repeat
forever generate endgenerate genvar integer real time realtime function
endfunction task endtask posedge negedge or and not xor nand nor xnor buf
tri tri0 tri1 wand wor supply0 supply1 signed unsigned defparam specify
endspecify default disable fork join wait force release deassign event
automatic return break continue struct typedef enum union packed const void
always_comb always_ff always_latch unique priority interface endinterface
package endpackage import export bit byte shortint int longint string chandle
virtual class endclass extends this super null assert assume cover expect
""".split())

MODULE_RE = re.compile(r'^\s*module\s+([A-Za-z_][\w$]*)', re.M)
ENDMODULE_RE = re.compile(r'^\s*endmodule', re.M)
# <Type> [#(params)] <inst_name> [array] (
INSTANCE_RE = re.compile(
    r'^[ \t]*([A-Za-z_][\w$]*)\s*'
    r'(?:#\s*\((?:[^()]|\([^()]*\))*\)\s*)?'
    r'([A-Za-z_][\w$]*)\s*'
    r'(?:\[[^\]]*\]\s*)?'
    r'\(', re.M)


def strip_comments(text):
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    return re.sub(r'//[^\n]*', '', text)


def source_files(root):
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(('.v', '.sv')):
                found.append(os.path.join(dirpath, name))
    return sorted(found)


def build_graph(files):
    """-> (defines: module -> [files], instantiates: module -> set(types))"""
    defines = defaultdict(list)
    instantiates = defaultdict(set)
    for path in files:
        try:
            with open(path, errors='replace') as handle:
                src = strip_comments(handle.read())
        except OSError:
            continue
        starts = [(m.start(), m.group(1)) for m in MODULE_RE.finditer(src)]
        ends = [m.start() for m in ENDMODULE_RE.finditer(src)]
        for i, (pos, name) in enumerate(starts):
            limit = starts[i + 1][0] if i + 1 < len(starts) else len(src)
            inner = [e for e in ends if pos < e < limit]
            body = src[pos:inner[0] if inner else limit]
            defines[name].append(path)
            for match in INSTANCE_RE.finditer(body):
                mtype, iname = match.group(1), match.group(2)
                if mtype in KEYWORDS or iname in KEYWORDS or mtype == name:
                    continue
                instantiates[name].add(mtype)
    return defines, instantiates


def build_roots(defines):
    """Top modules named by the build scripts, not guessed from file names."""
    names = set()
    patterns = [
        re.compile(r'-top[= ]+([A-Za-z_][\w]*)'),
        re.compile(r'^\s*TOP=["\']?([A-Za-z_][\w]*)', re.M),
    ]
    for base in BUILD_SEARCH:
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                if not name.endswith(('.sh', '.ys', '.fish', '.py', '.mk')) \
                        and name != 'Makefile':
                    continue
                path = os.path.join(dirpath, name)
                try:
                    with open(path, errors='replace') as handle:
                        text = handle.read()
                except OSError:
                    continue
                for pattern in patterns:
                    names.update(pattern.findall(text))
    # A name that is not a module in this tree was a false match.
    return names & set(defines)


def testbench_roots(defines):
    roots = set()
    for module, paths in defines.items():
        for path in paths:
            base = os.path.basename(path)
            if base.endswith(('_tb.v', '_tb.sv')) or os.sep + 'tests' + os.sep in path:
                roots.add(module)
                break
    return roots


def reachable(seeds, instantiates, defines):
    seen, stack = set(), list(seeds)
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        for child in instantiates.get(node, ()):
            if child in defines and child not in seen:
                stack.append(child)
    return seen


def check_duplicates(defines, build_roots=frozenset()):
    """Modules defined in more than one file.

    Added 2026-09-06, after the operator asked whether recovered RTL needed
    auditing. Name-based resolution means a stub and a real implementation
    sharing a name are indistinguishable to this tool -- and to a simulator,
    which picks by file order. This repository has been bitten by exactly
    that: filesystem-order module dedup broke three testbenches on a fresh
    clone (the test-runner nondeterminism fix).
    """
    out = []
    for module, paths in sorted(defines.items()):
        if len(paths) < 2:
            continue
        stubby = any('optional_stubs' in p for p in paths)
        real = any('/rtl/' in p and 'optional_stubs' not in p for p in paths)
        # Only a name a BUILD SCRIPT selects as TOP is genuinely ambiguous.
        # Vendor primitives (BUFG, MULT18X18 ...) are legitimately redefined
        # per board file and per simulation stub; flagging those is noise.
        ambiguous_top = module in build_roots and len(paths) > 1
        out.append({'module': module, 'count': len(paths), 'paths': paths,
                    'stub_shadows_impl': bool(stubby and real),
                    'ambiguous_build_top': ambiguous_top})
    return out


def check_archive():
    """Verilog outside hardware/ that no reachability check here covers."""
    found = []
    for base in ('archive',):
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in sorted(filenames):
                if name.endswith(('.v', '.sv')):
                    found.append({'file': os.path.join(dirpath, name)})
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--class', dest='klass',
                        choices=['dead', 'tb-only', 'no-tb', 'dup', 'archive', 'all'],
                        default='all')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    if not os.path.isdir(RTL_ROOT):
        sys.exit(f"run from the repository root: no {RTL_ROOT}/ here")

    defines, instantiates = build_graph(source_files(RTL_ROOT))
    tops = build_roots(defines)
    benches = testbench_roots(defines)

    from_top = reachable(tops, instantiates, defines)
    from_tb = reachable(benches, instantiates, defines)
    every = set(defines)

    result = {
        'dup': check_duplicates(defines, tops),
        'archive': check_archive(),
        'dead': sorted(every - from_top - from_tb),
        'tb-only': sorted((from_tb - from_top) - benches),
        'no-tb': sorted(from_top - from_tb),
        'counts': {
            'modules': len(every),
            'build_roots': len(tops),
            'testbench_roots': len(benches),
            'reachable_from_a_top': len(from_top),
            'reachable_from_a_testbench': len(from_tb),
        },
    }

    if args.json:
        result['defined_in'] = {m: defines[m] for m in defines}
        json.dump(result, sys.stdout, indent=1)
        print()
        return 0

    counts = result['counts']
    print(f"{counts['modules']} modules, {counts['build_roots']} board tops named by "
          f"build scripts, {counts['testbench_roots']} testbench roots")
    print(f"reachable from a top: {counts['reachable_from_a_top']}   "
          f"from a testbench: {counts['reachable_from_a_testbench']}")

    dups = result.get('dup', [])
    shadow = [d for d in dups if d['stub_shadows_impl']]
    if args.klass in ('dup', 'all'):
        print(f"\n== DUPLICATE MODULE DEFINITIONS ({len(dups)}) ==")
        amb = [d for d in dups if d.get('ambiguous_build_top')]
        print(f"   stub may shadow an implementation: {len(shadow)}")
        print(f"   name a build script selects as TOP: {len(amb)}")
        for d in dups:
            mark = '  <-- STUB SHADOWS IMPL' if d['stub_shadows_impl'] else ''
            if d.get('ambiguous_build_top'):
                mark = '  <-- A BUILD SCRIPT SELECTS THIS NAME AS TOP'
            print(f"   {d['module']:<34} x{d['count']}{mark}")
            if d['stub_shadows_impl'] or d.get('ambiguous_build_top'):
                for p_ in d['paths']:
                    print(f"        {p_}")
    if args.klass in ('archive', 'all'):
        arc = result.get('archive', [])
        print(f"\n== VERILOG OUTSIDE hardware/ ({len(arc)}) ==")
        print("   Not covered by any reachability check above.")
        for a in arc:
            print(f"   {a['file']}")

    headings = {
        'dead': "DEAD — no board top, no testbench",
        'tb-only': "TB-ONLY — simulated, never integrated into any top",
        'no-tb': "NO-TB — reaches silicon, never simulated (board tops expected here)",
    }
    for key in ('dead', 'tb-only', 'no-tb'):
        if args.klass not in (key, 'all'):
            continue
        print(f"\n== {headings[key]} ({len(result[key])}) ==")
        for module in result[key]:
            print(f"  {module:45s} {defines[module][0]}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
