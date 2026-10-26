# SSM-4-D2 recovery preparation

Date: 2026-10-18. Status: DRAFT FOR REVIEW. Production implementation, new
provenance capture and qualification are NOT AUTHORIZED by this document.
Spec author: Codex. Implementer and auditor: separately authorized future work.
Controlling evidence: build/ssm4/d1_identity_diagnosis_20261018_01/diagnosis.json.

## 1. Execute only the independent identity probe

```bash
sha256sum -c build/ssm4/d2_recovery_preparation_20261018_01/review.sha256
tools/run_detached_job.sh --output build/ssm4/d2_identity_service_20261018_01 --timeout 60 --notify-desktop -- python3 -B build/ssm4/d2_recovery_preparation_20261018_01/service_probe.py
```

Authorize ONE identity-only service job, 60 seconds maximum, no automatic retry.
This is not an SSM-4 qualification allocation. Do not invoke check_repo.sh,
campaign.prepare, capture, test discovery, mathematical tests or provenance
writers. Preserve all original terminal evidence. Stop the agent at LAUNCHED;
review terminal evidence only in a subsequent invocation. A timeout or failure
requires review, not a replacement job. No qualification slots are available.

Record service_entry.json before control-specific exports: identity-relevant
variables, absence versus presence, PID, service invocation ID, CWD and native
interpreter search path. Do not dump unrelated environment values or credentials.
Run two child identity observations in the same actual service: explicit
GIT_PAGER=cat positive; explicitly absent GIT_PAGER negative. Set only the
runner's bytecode/unbuffered variables in both children. Preserve all other
inherited variables. Retain native script search paths separately from explicit
-m-equivalent search-path comparison. Record the complete positive snapshot and
field differences from historical execution.json, including the two known D2
source changes. Positive means snapshot observed, not historical freeze equality.
Negative must reject with 'SSM-4 requires GIT_PAGER=cat'. The negative is a direct
guard control; the D2 runner intentionally normalizes an absent pager.

Review service_entry.json, cat.json, unset.json, probe_summary.json and exactly
one COMPLETE/FAILED/TIMEOUT. Keep actual current observations separate from the
unobserved historical failed-process environment. A matching current service
cannot establish the sole cause of the historical failure. Preserve SHA-256 of
all pinned production/historical/predecessor files before and after the job.

## 2. Inspect exact existing hardcoded paths before future edits

```bash
rg -n --glob '*.py' --glob '*.sh' 'certified_state_20261018_01|research/ssm4/provenance' research/ssm4
```

Existing campaign.py fixes CAMPAIGN to build/ssm4/certified_state_20261018_01
and accepts command.txt.strip() == 'bash research/ssm4/check_repo.sh'.
Existing check_repo.sh uses that root in the verification copy, both captures,
both verifications, both comparison inputs and determinism.json redirection.
It reads artifacts.sha256 at entry and EXIT and copies sources.json,
sources.tar.gz and artifacts.sha256 into verification. Current sources.py fixes
PROVENANCE and embeds research/ssm4/provenance in artifact checksum paths.
Its selection() excludes its own provenance directory to prevent recursion.

## 3. Smallest proposed future amendment — review before applying

Reserve build/ssm4/certified_state_r1_20261018_01 as NEW qualification root and
build/ssm4/recovery_r1_provenance_20261018_01 as NEW immutable freeze root.
Both must be absent, including dangling symlinks, immediately before their
respective creation. Do not create or reserve either directory during preparation.
Keep the old campaign and research/ssm4/provenance immutable in place.

Limit source amendments to research/ssm4/campaign.py, check_repo.sh and sources.py:

1. Change campaign.py CAMPAIGN to the fresh fixed root. Keep the exact accepted
   command identity 'bash research/ssm4/check_repo.sh' (including the launcher's
   trailing-space/newline encoding semantics). Reject added arguments, shell
   prefixes, alternate scripts, changed command text, missing/linked metadata,
   terminal roots and any pre-existing cases/cases_repeat/verification path.
   Reject dangling marker links as existing evidence. Do not add arbitrary path
   or command overrides. Reject existing exit_status/result.json as stale roots.
2. Replace EVERY old qualification-root occurrence in check_repo.sh with the
   new root: verification copy, cases, cases_repeat, verify commands, comparison
   inputs and determinism.json. Replace entry/EXIT artifact paths and all copied
   provenance paths with the new freeze root. Copy research.json and execution.json
   as well, so the retained verification record includes both manifest roles.
   Keep D2's pager policy and strict source checks before dispatch and at exit;
   retain fail-fast ordering and all regressions.
3. Change sources.py PROVENANCE to the new build freeze root. Retain explicit
   exclusion of historical research/ssm4/provenance in selection(), alongside
   the new output exclusion, otherwise its historical metadata becomes newly
   discovered source and violates membership. Build artifact digest lines from
   PROVENANCE.relative_to(ROOT), replacing the embedded historical prefix.
   Existing archive metadata member names already use ROOT-relative paths.
   Require new freeze destination absent (including dangling symlinks), and
   preserve mkdir(exist_ok=False). No historical manifest changes or exemptions.
   Preserve exact membership/hash/mode/discovery/environment comparisons.

Stay within 150 lines per Python module. Current sources.py is 148 lines; make
in-place expression substitutions where appropriate rather than adding helpers.
Stop if this cannot maintain 148 research / 2194 execution membership, unchanged
mathematics, predecessor identities, line limits or the three-file edit scope.
A newly tracked contract or concurrent source addition requires an explicit
reviewed membership delta; never change a fixed membership digest silently.

Normalize only absent GIT_PAGER to cat and reject explicit conflicts. Require
cat at freeze. Set PYTHONDONTWRITEBYTECODE=1 and PYTHONUNBUFFERED=1 as before.
Use actual service observations to review all remaining variables/tool/interpreter
identities. Unexpected drift must halt; do not filter GIT_* or normalize arbitrary
variables to pass. The launcher remains unchanged and forwards PATH explicitly.

## 4. Required focused regression controls after implementation authorization

Run focused private fixtures only, each bounded to 55 seconds. Preserve the 36
original guard controls and 14 D2 launch controls. Add campaign-path controls:

- Fresh metadata-owned private root accepts the exact command and produces only
  its private verification/preflight.json; input roots remain outside real runs.
- COMPLETE, FAILED and TIMEOUT roots each reject; marker dangling links reject.
- Pre-existing cases, cases_repeat and verification each reject as directory,
  file and dangling symlink. Existing exit_status/result.json each reject.
- Linked/missing command.txt or unit_name, empty unit and altered commands reject.
- Static runner audit verifies every output path and every checksum/copy path;
  a stubbed command harness records argv/redirections without invoking renderers,
  regressions or campaign qualification. No old campaign destination is written.
- New private provenance capture/check and archive metadata paths agree; repeated
  capture refuses existing output. Original provenance remains excluded while
  historical archives retain their digests. Preserve recursive-output controls.
- Matching pager and normalized absence pass; empty/less/injected pager reject;
  unrelated GIT_*, tool, source, mode, discovery and bypass drift still reject.

```bash
bash -n research/ssm4/check_repo.sh
git diff --check -- research/ssm4/campaign.py research/ssm4/check_repo.sh research/ssm4/sources.py
PYTHONDONTWRITEBYTECODE=1 python3 -m research.sg0.sources check
sha256sum -c research/ssm3/provenance/sources.sha256
```

Freeze exact focused test commands and evidence-directory paths in the
implementation authorization before running them. Do not substitute a full
regression, synthesis or main qualification run for these controls.

## 5. Separate future freeze and qualification gates

After focused review, separately authorize creation of the NEW immutable freeze
with explicit GIT_PAGER=cat, bytecode/unbuffered exports and a documented stable
source boundary. Record exact diffs, hashes, modes, member counts, tools, Git and
service-environment identities. Verify original evidence unchanged. Require a
reviewed actual service-context comparison to the NEW freeze before qualification;
this preparation probe compares historical inputs only and does not meet that gate.

Only a later owner authorization may allocate a NEW one-attempt / 1800-second
qualification campaign. Proposed command (DO NOT EXECUTE now):

```bash
tools/run_detached_job.sh --output build/ssm4/certified_state_r1_20261018_01 --timeout 1800 --notify-desktop -- bash research/ssm4/check_repo.sh
```

No automatic retries or timeout extensions. Old allocation remains 1/1 consumed.
No mathematical qualification claim follows from identity-only observations.
