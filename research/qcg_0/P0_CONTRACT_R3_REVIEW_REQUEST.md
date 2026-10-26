# QCG-0 P0 contract Revision 3.1: request for independent read-only review

Date: 2026-10-23. From: QCG-0 author. To: the independent reviewer. **Read-only inspection; no calculation is requested or
authorized** (the R2 allowance is exhausted). Subject: `QCG0_P0_EXECUTION_CONTRACT.md` Revision 3.1, SHA-256
`2829a167eabb3bcc16a5beed35249ce91f5097de0f7934647e0f7676b474ee44`; Revision 3 (the text revised in response to the R2 review)
was `d6f27aae3328814b67b8c10da2e916b2f3943dbffa9416f97aa4e629243e7989`; Revision 3.1 differs only in status wording
(`QCG0_P0_EXECUTION_CONTRACT_REVISION_3_1.diff`, `48bccfad…bc75a`, and the owner dispositions of D-1…D-6 in §11).
Owner dispositions: `QCG0_P0_DECISION_RECORD.md`. The R2 certificate is used for its reference results only; its REVISE verdict
is not an assessment of this revision.

Verify against the frozen §10 checklist, with particular attention to the four R2 objections:
1. **Sequential S1 operation selection:** S1 runs only the position steps (no `ok`, no other step); the required-step table of §5 for
   S1/S2/S3 per arm family; per-arm evolution rules; preparation is request-independent; each tape restarts from the post-P snapshot.
2. **Nested composite event identities:** one operation counter per primitive call including nested primitives; generic
   `<PRIMITIVE>.<polynomial>` names; P1–P31 and k1–k8; BERN weight imports; the `PADD`/`PSUB` and zero-polynomial rules.
3. **Deadline attestation:** TIMEOUT only from `timeout`'s own exit 124; the runner never exits 124 and installs no SIGTERM handler;
   no `--kill-after`; any other nonzero status, including 137, is FAILED.
4. **Pin/version manifests and output cap:** checksum-only `PINS.sha256`, separate string-compared `TOOLS.manifest`, no
   self-hashes (out-of-band recording); per-file `RLIMIT_FSIZE`, runner total, and the pre-marker `du` check; exactly one marker;
   the post-run pin check always attempted.

Also confirm that: the administrative-versus-semantic K rule is stated once and consistently (preparation K = 0); the P-1
references and field mapping are adopted as produced; the Cell A W31 events match the certified list; no certified value is altered.
Report PASS / REVISE / BLOCKED with evidence; a PASS does not authorize freeze, implementation or P0.
