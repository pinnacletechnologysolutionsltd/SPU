# AOR-S1 final specification ratification

```bash
cat spu_strategy/AOR_S1_FINAL_RATIFICATION_2026-10-14.md
cat spu_strategy/contract_aor_s1_schedule_reconciliation_2026-10-14.md
python3 -m json.tool spu_strategy/aor_s1_qualification_supplement_2026-10-14.json
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/AOR_S1_FINAL_RATIFICATION_2026-10-14.md spu_strategy/contract_aor_s1_schedule_reconciliation_2026-10-14.md
```

Date: 2026-10-14. Authority: explicit owner final ratification of the amendment
dated 14 October 2026, after the requested independent review.

| Subject | Final disposition |
|---|---|
| Schedule reconciliation, checked 1a, 14-unit adjustment | RATIFIED |
| Status precedence and input rules | RATIFIED |
| Original 83 operation fixtures | Separate-agent independent review PASS |
| Five kernels, 11 comparators, 13 alias cases | Separate-agent independent review PASS |
| Isolated implementation/qualification contract preparation | AUTHORIZED |
| Candidate implementation | HOLD |
| Qualification execution | NOT AUTHORIZED |
| ISA changes, FPGA or hardware work | NOT AUTHORIZED |

The [independent review](AOR_S1_INDEPENDENT_REVIEW_DISPOSITION_2026-10-14.md)
satisfies the owner's ratification condition for submitted counts, mathematics
and expected outcomes. Its original evidence and reviewed input identities
remain intact. This is separate-agent review, not independent human verification.

Prepare a separate contract incorporating the eight recommended operation
witnesses, executable fault controls, independent oracle/checker separation,
exact commands, acceptance criteria and proposed frozen attempt/time budgets.
Keep the original 83 rows and identities byte-identical. Store additions in
the [supplement](aor_s1_qualification_supplement_2026-10-14.json); their inclusion
in a proposed contract is not qualification or authorization to execute them.

The checked 1a multiplication is a logical accounting convention, not a
mathematical necessity or measured hardware work. Future comparative reports
must disclose it. Implementation and qualification remain HOLD pending review
and separate execution authorization of their contract.

This final decision supersedes the provisional ratification disposition in
[the earlier owner record](AOR_S1_OWNER_DECISION_2026-10-14.md). Preserve that
record as decision history rather than replacing its original conditions.
