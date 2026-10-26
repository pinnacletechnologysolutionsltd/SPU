#!/usr/bin/env bash
# Validation E + reachability: read-only greps over the pinned archive ($1) emitting RESULT lines. Judgment is the reviewer's.
S="$1"; cd "$S"
r() { # id, description, pattern, paths...
  local id="$1" d="$2" pat="$3"; shift 3
  local hits; hits=$(grep -rn -E "$pat" "$@" 2>/dev/null | head -25 | python3 -I -c 'import sys,json;print(json.dumps(sys.stdin.read().splitlines()))')
  echo "RESULT {\"id\":\"E.$id\",\"ok\":null,\"detail\":{\"what\":\"$d\",\"hits\":$hits}}"
}
r spread_callers      "callers of QuadrayVector.spread / spread_from_quadrances"            '\.spread\(|spread_from_quadrances' software --include='*.py' --include='*.cpp' --include='*.h'
r hex_project_callers "callers of hex_project"                                               'hex_project\(' software --include='*.py'
r rotate_cycle_callers "callers of QuadrayVector rotate()/cycle()"                           '\.rotate\(\)|\.cycle\(\)' software --include='*.py'
r davis_instances     "RTL instantiations of davis_gate_dsp and DEVICE bound"                'davis_gate_dsp' hardware/rtl hardware/boards --include='*.v'
r davis_ys            "synthesis scripts naming davis_gate_dsp"                              'davis_gate_dsp' hardware/boards --include='*.ys'
r quadrance_consumers "how spu13_core consumes quadrance / gasket_sum (signedness, widths)"  'quadrance|gasket_sum' hardware/rtl/core/spu13/spu13_core.v
r input_domain_docs   "documented zero-sum / input-domain statements"                        'zero.sum|sum.*=.*0|Davis invariant|input domain|11585' knowledge docs/hardware_evidence.md hardware/rtl/core/shared/davis_gate_dsp.v
r div3_semantics      "div3 / thirds rounding in RTL"                                        'div3|apply_div3|/ *3|thirds' hardware/rtl/core/spu13 --include='*.v'
r doc_metric_norm     "quadrance normalization / Quadray vs Cartesian statements"            'quadrance|IVM quadrance|Q *=|Σ.*[<]' knowledge --include='*.md'
r doc_angles          "tetrahedral basis angle statements (60 vs 109.47)"                    '60.{0,3}(deg|°)|109\.47|tetrahedral angle' knowledge docs/hardware_evidence.md --include='*.md'
r doc_groups          "Weyl vs full point group statements"                                  'Weyl|point group|O_h|octahedral group|S_?4|A_?3' knowledge --include='*.md'
r doc_lattice         "A3 / A3* / FCC / BCC statements"                                      'A_?3|A₃|FCC|BCC|root lattice|weight lattice' knowledge docs/hardware_evidence.md --include='*.md'
r doc_norm_preserve   "norm preserved vs scaled statements for rotations"                    'preserv|scales?|dilat' knowledge/isa_reference.md knowledge/SPU_LEXICON.md
