# Publication redactions, exclusions and retained provenance

This release is a publication export of a larger private research repository. This note records what differs
from the private originals, so that a hash or reference that does not match is not mistaken for a technical failure.

## Redacted

* `docs/hardware_evidence.md`: the RP2350 unique chip identifier on the line beginning `Device: Pico2 RP2350 A2` is
  replaced by `<redacted>`. The unredacted original is kept privately.
  The SHA-256 of the unredacted ledger is `7341df25d3d586bc1d98f056c59905097185a3f63341a50f02c69015b74b2718`; that is the value recorded for this file in
  `docs/ret2_candidates_20261018.json`, so that record does not match the redacted copy published here.
  This is a provenance difference, not a failed verification. The sealed archive below still contains its original copy of the ledger.
* Three bench photographs had location and device metadata removed; see `docs/bench_captures/t1n_h1_2026-09-28/SANITIZED.txt`.
* Disk and device serial numbers in a few documents are replaced by `<serial-redacted>` or `<disk-serial-redacted>`.

## Retained unchanged on purpose

* USB adapter serials (owner decision, 2026-11-09). The USB serial numbers of three bench adapters, audited on
  2026-11-09, are intentionally retained wherever they appear: the Pico used as the DirtyJTAG programmer, the Sipeed
  Tang debugger, and a Pico 2 running the flash-PMOD utility. All three already appear in public repository history or
  in published evidence, and their publication is accepted for this project; existing occurrences, including
  historical ledger entries and hash-anchored files, are not altered. Unique FPGA and MCU chip identifiers (such as the
  RP2350 chip ID above) remain subject to redaction. Credentials, secrets and account identifiers must never be
  published. This decision does not authorize publication of private strategy documents.

* `docs/assets/publication/2026-10-14/selected-evidence.zip` keeps its published SHA-256 and original contents.
  Some files in it contain a local username in file-system paths and one contains a kernel string.
* Hash-anchored evidence files (review manifests, frozen run records, Vivado fixtures and their provenance) keep
  their original bytes, including local file-system paths and, in the Vivado report headers, the build host name.
  Rewriting them would invalidate the SHA-256 values that other files record.

## Not included

Outreach and session-handover documents, a private memory-search helper and a private working-tree status dump are
not part of this release, and neither are `photonics/` and `results/`. Research contracts under `spu_strategy/` that
were published with an earlier public snapshot remain; other internal planning documents are not part of this
release. Research added during development after that public snapshot, including the Soul project, is not part of
the curated v0.2 release (see [the v0.2 readiness index](V02_RELEASE_READINESS.md) §11). Documents that still mention
those files refer to material that is not here; such links are intentionally unresolved.
