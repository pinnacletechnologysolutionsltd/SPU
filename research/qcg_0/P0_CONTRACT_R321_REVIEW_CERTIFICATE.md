# QCG-0 P0 Revision 3.2.1 narrow independent review

Date: 2026-10-23. Reviewer: `/root/qcg0_fixture_reviewer`, independent of the author and HEX-SOM acceptance context. **Disposition: PASS for the five requested finalization checks.** This closes the single B4 defect left by the Revision 3.2 review; prior accepted B1–B3 and D-1…D-6 are not reopened.

Verified the supplied SHA-256 identities before review:

- Contract: `1f8aca9f088ffbaafb002ba5cffde7bdee7b33fdfcf18dcf20dec16202b8cf2f`.
- Revision 3.2.1 diff: `d331ed67bd18e3a2f83c06a40e47b80c21726630383fef88ec81851ca03f30c9`.
- Review request: `76d02321445b9332740e4a54dd18545a31203aa3d53b66fadc853013ab578af4`.

Read the request, full supplied diff and amended finalization block. The preceding R32 certificate/manifest identities also match. Author scratch seen: no. No input or previous artifact was edited.

| Requested check | Result | Evidence |
|---|---|---|
| 1. Required metadata precedes marker choice | PASS | exit.code, pins_after.txt and any required cause file are attempted before MARK is selected. W records their write failures. |
| 2. Metadata failure forces FAILED | PASS | The first marker-selection branch tests W, sets MARK=FAILED and attempts FINALIZE_FAILED. COMPLETE/TIMEOUT branches cannot run when W is nonzero. This removes the prior false-COMPLETE path. |
| 3. Durable failure versus unavailable | PASS | No terminal marker gives RESULT_UNAVAILABLE and exit 4. A persisted FAILED marker with a metadata failure reaches exit 3. Failure evidence is attempted where possible; no impossible persistence guarantee is inferred. |
| 4. Marker count and exit consistency | PASS | Marker count is checked after the single marker attempt. Any write/count inconsistency gives finalization failure rather than success; normal completion requires one marker and maps COMPLETE to 0, TIMEOUT to 11 and FAILED to 10. The raw child status remains separately recorded. |
| 5. No unrelated change | PASS | The supplied diff changes the finalization ordering/branches and their descriptive checklist/header text only. The prior algorithms, reference results, policy scopes and B1–B3 fixes are preserved. |

The displayed shell block passed `bash -n` (exit 0), supplied as text through awk. The launcher was **not executed**. No mathematical calculation, stage/fixture generation, experiment or implementation occurred; no allowance was granted or consumed.

This narrow PASS is a text/syntax review, not implementation or runtime conformance evidence. The remaining sequential/Cell B W31 derivation still needs its separately granted owner allowance; complete manifests, freeze, implementation and P0 execution remain separate authorization gates. This PASS grants none of them.
