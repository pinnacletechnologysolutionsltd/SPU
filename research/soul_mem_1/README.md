# SOUL-MEM-1

Deterministic research comparing current-summary (M0), full-history scan (M1)
and selective indexed retrieval (M2). The registered scenario data and
instrumented per-query results are in `scenarios.py` and `evidence/results.json`.
No predecessor or QAF code is reused. See [findings](FINDINGS.md).

Reproduce from the repository root with Python 3.10+ and standard library only:

```bash
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_mem_1/test_experiment.py'
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_mem_1/evaluate.py /tmp/soul-mem-1-repro1'
bash -c 'ulimit -v 1048576; timeout 30s python3 -B research/soul_mem_1/evaluate.py /tmp/soul-mem-1-repro2'
diff -r /tmp/soul-mem-1-repro1 /tmp/soul-mem-1-repro2
sha256sum -c research/soul_mem_1/evidence/registration.sha256
```

Output files in the specified scratch directory are overwritten: choose fresh
paths to preserve earlier runs. Registered input and policy hashes were recorded
before the two runs. Limit per process: 30 seconds and 1 GiB address space.

Each condition gets every record in the same order. No agent receives expected
answers or the evaluator's relevance list. Each record supplies its source,
epoch and asserted reliability; sources are assumed calibrated, not learned.
A fixed procedure retains at most one current candidate per key and revocation
IDs. M0 discards prior candidates and does not store an archive. M1 and M2
retain the same records and identical summaries. The fixture uses at most six
summary keys and six records; this implementation does not enforce a general
maximum. M2 additionally stores a key-to-offset index. Thus the unequal total
storage is intentional and disclosed, not an equal-budget comparison.

A candidate with the highest epoch and then highest reliability wins; equally
ranked contradictory records yield unknown. A revocation of the current candidate
makes the summary unresolved. M1 scans its archive on every lookup; M2 consults
its index only for a history query or unresolved revoked candidate. M0 has no
fallback. No future information determines these triggers. This is one deliberately
simple policy, not an optimized summary or full-history system.

Resource accounting starts at evaluation queries, not ingestion: every archive
record visited, including irrelevant ones and repeated visits, counts once per
visit and contributes its canonical JSON byte length. Each M2 index lookup also
counts the canonical JSON bytes of its key and posting list. Counts model logical
reads, not disk I/O or Python allocation. Reported operations count lookups,
index lookups and archive-record visits; ingestion counts are separate and do not
claim equal real CPU cost. Stored bytes are the canonical JSON size of the full
policy state including archive and M2 index, not measured resident memory. The
relevance oracle lists records relevant to each question and is used solely after
answers. Retrieval precision counts relevant accesses including repeated visits;
no-retrieval precision is undefined. Attribution correctness in the JSON checks
whether the returned reference is in that relevance list, which is weaker than
independent verification that it actually supports the reported answer.

The archive validator tests a trusted SHA-256 anchor and reference structure.
It does not authenticate an adversary able to replace both record and anchor;
normal answering is not automatically gated on archive validation. C5 tests
this validator directly. Other limitations are detailed in the findings.
