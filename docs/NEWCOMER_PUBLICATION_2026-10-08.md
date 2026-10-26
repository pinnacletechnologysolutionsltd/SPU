# Focused software publication and anonymous checkout

Date: 2026-10-08. The frozen 23-file proposal is published on the public review
branch [`codex/newcomer-software-20261008`](https://github.com/pinnacletechnologysolutionsltd/SPU/tree/codex/newcomer-software-20261008),
at `2a1fcda43070df975d0a6f8dfa1b59cdc99247c5`. `master` remains at the
original base `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`; no merge occurred.

## Implementation review and publication

The [implementation review](../build/newcomer_publication_20261008/implementation_review.json)
checked the exact frozen diff and dependency hashes, robotics tuple arithmetic
and reference assumptions, GPU scene validation/packet layout, independent ideal
and finite-width paths, output refusal/provenance, CLI failures, and focused
test coverage. No implementation blocker was found for draft publication.
This is an agent review, not independent owner implementation sign-off.

The [October 7 result](NEWCOMER_PUBLICATION_REVIEW_2026-10-07.md) retains the
local clean-clone PASS: 26 commands, expected outputs, source/artifact hashes,
and clean initial/final Git status. Icarus S2 checks ran successfully. It does
not establish full regression, installed packaging, native simulation or FPGA
qualification. Those dimensions remain separate.

GitHub accepted the exact commit on the review branch. The active GitHub CLI
account `johncurley` could not create a draft PR: GitHub returned
`GraphQL: must be a collaborator (createPullRequest)`. No PR was created.
An authorized collaborator can use the
[prepared comparison](https://github.com/pinnacletechnologysolutionsltd/SPU/compare/master...codex/newcomer-software-20261008?expand=1)
and [prepared PR description](../build/newcomer_publication_20261008/pr_body.md).
[Publication status](../build/newcomer_publication_20261008/publication_status.json)
records the successful branch push and the distinct PR permission failure.

The proposal's [quickstart is publicly readable](https://github.com/pinnacletechnologysolutionsltd/SPU/blob/2a1fcda43070df975d0a6f8dfa1b59cdc99247c5/docs/NEWCOMER_SOFTWARE_QUICKSTART.md).
Users must select this review branch to obtain the proposed software; the
default branch has not acquired it. Do not report a default-branch newcomer
publication or merged milestone from this branch push.

## Anonymous remote qualification: PASS

Reviewed in the later October 8 session: exactly one `COMPLETE` marker, exit 0,
and all 26 individual command results PASS. Expected VM, Fibonacci, robotics
and preview outputs were checked; S2's Icarus checks ran successfully. The
[review record](../build/newcomer_publication_20261008/remote_walkthrough_01/review_01.json)
rechecks the frozen runner/manifest identity, 46 source hashes, 28 artifact hashes,
the exact proposed HEAD and empty initial/final/current Git status. Raw logs are
hashed in that record. Outcome: `PASS_ANONYMOUS_REMOTE_CHECKOUT` for the review
branch. This establishes neither default-branch publication nor full regression
or hardware qualification. No PR or merge was performed during result review.

The owner requested anonymous remote checkout after focused publication.
Freeze one new attempt with a 1,200-second timeout and a 1,200-second cumulative
budget. This is a distinct remote-checkout campaign, not a retry of the completed
local qualification. The [plan](../build/newcomer_publication_20261008/freeze_remote_01/plan.json)
binds the runner and manifest bytes to the same proposed commit and public branch.

```bash
tools/run_detached_job.sh --output build/newcomer_publication_20261008/remote_walkthrough_01 --timeout 1200 --notify-desktop -- python3 build/newcomer_publication_20261008/freeze_remote_01/run_remote_quickstart.py build/newcomer_publication_20261008/remote_walkthrough_01
```

The [runner](../build/newcomer_publication_20261008/freeze_remote_01/run_remote_quickstart.py)
clones GitHub over HTTPS with no overlay. Git user/system configuration,
credential helpers, extra authentication headers and prompts are disabled;
the URL contains no credentials. It verifies the frozen HEAD and all declared
file hashes, creates isolated Python, and exercises the same demo/edit/inspect
path and focused tests. Command exits and output expectations determine the
result. Original and edited packet/image/model manifests and final Git state
are independently checked by the runner.

If Icarus is unavailable, record S2 as `UNTESTED_MISSING_ICARUS`, while reporting
the separately successful preview path as `PASS_PREVIEW_S2_UNTESTED`. A missing
optional RTL test prerequisite is not evidence of preview failure or RTL parity.
With Icarus available and all checks successful, the result is
`PASS_ANONYMOUS_REMOTE_CHECKOUT` for this exact review branch/commit.

The launch procedure requires ending the agent turn and inspecting only in a later invocation,
after exactly one terminal marker (`COMPLETE`, `FAILED`, or `TIMEOUT`) exists.
Read individual `quickstart_results.json` rows and raw outputs; the terminal
marker alone does not establish usability or test coverage. No automatic retry
or timeout extension is authorized.

Archive qualification and production pruning remain held independently.
Neither branch publication nor a successful remote software walkthrough
authorizes archive pruning, a merge, or stronger hardware claims.
