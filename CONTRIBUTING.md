# Contributing to SPU-13

Thank you for your interest in contributing to SPU-13! This project is dedicated to remaining free, open-source, and unencumbered by patents.

To protect the community and ensure the SPU-13 architecture remains free for anyone to use, we require all contributions to adhere to the licensing and contribution guidelines outlined below.

## Ways to help

The most useful contributions right now are independent checks, not new features:

- **Run the software quickstart** ([docs/NEWCOMER_SOFTWARE_QUICKSTART.md](docs/NEWCOMER_SOFTWARE_QUICKSTART.md)) on your machine and report the exact command,
  exit code and output of anything that fails. Missing files or modules are publication gaps; wrong results are functional failures.
- **Re-derive or break a result.** Each experiment under `research/` has a `FINDINGS.md` with its claim, its test command and its stated limits.
  An independent oracle, a counterexample or a flaw in a proof is more valuable than agreement.
- **Review the arithmetic.** Bounds, error precedence and refusal semantics are written down (for example the full-domain bounds in
  [research/som_rp0/FINDINGS.md](research/som_rp0/FINDINGS.md)); look for overflow, ordering or tie-break mistakes.
- **Reproduce on hardware you own.** Hardware claims live only in [docs/hardware_evidence.md](docs/hardware_evidence.md), with a fixed entry format.
  A new entry needs the artifact hash, the command and what was *not* checked.
- **Improve documentation and exercises** that run without a board, and report broken links.

See the [capability matrix](docs/CAPABILITY_MATRIX.md) for what is and is not established, and its known limitations before proposing work on them.
Open an issue before large changes. Do not add silicon-verified claims without a ledger entry.

## Developer Certificate of Origin (DCO)

All commits submitted to this repository must be signed off to certify that you wrote the code or have the right to submit it under the open-source license that applies to each file you contribute. The repository uses different licenses for different directories; see [Licensing](#licensing) below and [LICENSING.md](LICENSING.md).

We use the standard Developer Certificate of Origin (DCO) version 1.1. By signing off your commits, you assert the following:

```
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004 Lawrence Rosen <lrosen@aqsp.com>

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, I have the right to submit under the same open
    source license (unless I am permitted to submit under a different
    license), as indicated in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

### How to Sign Off

To sign off a commit, add a `Signed-off-by` line to the commit message. You can do this automatically by using the `-s` or `--signoff` flag when committing:

```bash
git commit -s -m "your commit message"
```

This will append a line like this to your commit message:

```
Signed-off-by: Jane Doe <jane.doe@example.com>
```

---

## Licensing

For contributions submitted after adoption of this policy, contribute original
material under the applicable license described in [LICENSING.md](LICENSING.md).
The defaults are:

| Scope | Default license |
|---|---|
| `software/` | MIT, from [software/LICENSE](software/LICENSE) |
| `hardware/` | CERN-OHL-W-2.0, from [hardware/LICENSE](hardware/LICENSE) |
| `docs/` and `knowledge/` | CC0 1.0 Universal, from [docs/LICENSE](docs/LICENSE) |
| `examples/` and `fixtures/` | MIT, from [software/LICENSE](software/LICENSE), for original content by the repository owner |
| `spu_strategy/` and `research/` | Apache-2.0, from the root [LICENSE](LICENSE), for original content by the repository owner, unless a file specifies otherwise |
| Root-level files and `tools/` without a more-specific notice | Apache-2.0, from [LICENSE](LICENSE) |

A more-specific file or directory notice takes precedence. Preserve existing
license, copyright and attribution notices when modifying or moving material;
a directory default does not replace an existing grant. Third-party material
retains its own terms and must be identified with its source and applicable
notices. Submit only material you have the right to contribute under those
terms, as certified by the Developer Certificate of Origin above.

[LICENSING.md](LICENSING.md) is authoritative where this summary and it differ,
including its exceptions (for example, hardware source copies stored under
`research/` keep the hardware license). For scopes the licensing map does not
cover, ask maintainers to resolve the applicable terms before contribution
acceptance. This amendment makes no new licensing decision for those scopes.

This policy is prospective. It does not relicense existing material, withdraw
existing grants, or establish that historic contributors agreed to different
terms. Any unresolved ownership or licensing conflict requires a separate
rights review before the affected material is accepted or redistributed.
