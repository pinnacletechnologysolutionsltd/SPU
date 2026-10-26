"""Human-readable S0 packet renderer from frozen JSON evidence."""
import json
from pathlib import Path


def policy_totals(results):
    totals={}
    cohort=results['cohorts']['retained_vector_rational_joint']['chains']
    for chain in cohort.values():
        for key,stats in chain['policy_accounting'].items():
            row=totals.setdefault(key,{'operations':0,'fallbacks':0,'reentries':0,'nonresident_results':0})
            for field in row: row[field]+=stats[field]
    return totals


def render(directory, plan_path=None):
    root=Path(directory); r=json.loads((root/'results.json').read_text())
    p=json.loads(Path(plan_path or root/'plan.json').read_text())
    fixed=r['scale_candidates']['fixed_scale']; shared=r['scale_candidates']['shared_scale']
    rows=['# SPU Surd Register S0 results','',f"Retained correctness: **{r['retained_correctness_status']}**.",
          'This report records retained-corpus correctness and accounting. The bounded corpus command terminal marker is stored beside this report as `terminal.txt`. Focused synthetic verification is recorded separately under the sibling `focused/test_01/terminal.txt` evidence.','',
          '## Retained robotics cohort','',
          '32 retained vector inputs use rational-only joints. The independent Fraction component-pair oracle, maintained kernel, fused wide kernel, and each bounded policy are compared for chain lengths 1, 3, 6 and 12. This is not retained Surd-by-Surd joint coverage.','',
          '| Joints | W/policy | Operations | Fallbacks | Re-entries | Nonresident results | Max named intermediate bits |',
          '|---:|---|---:|---:|---:|---:|---:|']
    for chain,entry in r['cohorts']['retained_vector_rational_joint']['chains'].items():
        for key,s in entry['policy_accounting'].items():
            maximum=max(s['max_named_intermediate_bits'].values(),default=0)
            rows.append(f"| {chain} | {key} | {s['operations']} | {s['fallbacks']} | {s['reentries']} | {s['nonresident_results']} | {maximum} |")
    rows+=['','## Totals across chain lengths','','',
           '| W/policy | Operations | Fallbacks | Re-entries | Nonresident results |',
           '|---|---:|---:|---:|---:|']
    for key,stats in policy_totals(r).items():
        rows.append(f"| {key} | {stats['operations']} | {stats['fallbacks']} | {stats['reentries']} | {stats['nonresident_results']} |")
    rows+=['','## Candidate accounting','','',
       f"Fixed scale discovered from retained coefficients: `{r['scale_candidates']['fixed_scale']['scale']}`. It uses 2W bits per scalar plus the frozen shared scale. Exactness rejections are retained in `results.json`.",
       'Explicit denominator uses 3W logical bits per scalar. Shared-scale blocks count their denominator lane, alignment multiplications, block updates and fallback events. These are logical storage and software-model counts, not physical register pressure or cycles.','',
       '## Interpretation','',
       'The retained comparison supports exact bounded register semantics for the tested cohort wherever the model reports resident/re-entry status; wide-fallback outputs are kept distinct from resident values. A 64-bit observed width fit is not a proof for all input sequences. Fixed scale has an exactness boundary, and shared scale trades denominator duplication for alignment and capacity costs.',
       'The recommended next software candidate is explicit-denominator W=64 with the FIT_RESCUE policy for separately reviewed robustness, while retaining BOUNDARY as the cost baseline. This does not authorize or establish an RTL design. The synthetic focused test terminal status prevents acceptance until a renewed test budget yields a passing terminal record.','',
       '### Frozen scale candidate measurements','','',
       f"The retained coefficient LCM is `{fixed['scale']}`. Fixed-scale loads accepted {fixed['loads_ok']} coefficients and rejected {fixed['loads_rejected']}; its modeled multiplications accepted {fixed['mul_ok']} and rejected {fixed['mul_rejected']}. Rejections preserve exactness and do not imply arithmetic failure for explicit-denominator storage.",
       f"Shared-scale accounting aligned {shared['load_blocks']} vector/joint blocks and ran {shared['mul_blocks']} representative multiplications. It recorded {shared['alignment_multiplications']} coefficient alignment multiplications, {shared['block_scale_updates']} block-scale updates and {shared['fallbacks']} storage fallbacks.",
       'The representative scale-candidate multiplication uses the same two retained vector coefficients for fixed and shared models. It is a storage/arithmetic probe, not a complete competing chain kernel.','',
       '### Width limits and observations','','',
       'The `parameterized_full_range_intermediate_limits` object lists formula-derived per-operation bounds for each W. These are mathematical sufficient widths for one valid operation. `max_named_intermediate_bits` and fallback counts are observations over the frozen chains and are not universal bounds.',
       'At W=64 the proposed explicit register is 192 logical bits. The prior chain study observed a 35-bit peak on its 12-joint workload and no 64-bit fallback; S0 replays its own bounded operation policies and keeps wide-fused behavior separately identified. No Python memory or physical register-pressure estimate is made.','',
       '## Provenance','',f"HEAD: `{p['head']}`",f"Dirty tree at preflight: `{p['dirty']}`; status SHA-256 `{p['dirty_status_sha256']}`.",
       f"Frozen input SHA-256: `{p['inputs_sha256']}`",f"Plan SHA-256: `{p['plan_sha256']}`",f"Command: `{ ' '.join(p['command']) }`",'',
       f"Focused-failure source hashes: `{p['failure_source_hashes']}`. Current sources are frozen in `plan.json`; earlier untracked snapshots were not preserved, so their exact contents are unavailable.",
       'Attempt history: `focused/test_01` import failure; `focused/test_02` narrow-accumulator control exposed missing accounting; `focused/test_03` exposed an incorrect FIT_RESCUE expectation. All logs are preserved.','',
       'Hardware operations: 0. Device equivalence: not tested. Python timings: not run by S0. Python object memory: not measured.','',
       '## Explicit limitations','',
       'The exact oracle uses Python `Fraction` coefficient pairs and is independent of the bounded candidate. The maintained robotics reference remains unchanged, including its determinant-one adjugate inverse behavior for singular joints.',
       'The focused test defines six-step paired-rotation closure and the full-range rotation denominator witness as synthetic controls. They do not expand the retained workload cohort.',
       'Logical bits and scheduled transfer bytes describe the stated register organizations only. They are not physical CPU register allocation, FPGA resource use, cycle counts, throughput, energy, or area.',
       'The report is suitable for review of software semantics and cost models. Promotion into the maintained ISA, robotics default path, or any hardware experiment requires a separate decision.']
    return '\n'.join(rows)+'\n'
