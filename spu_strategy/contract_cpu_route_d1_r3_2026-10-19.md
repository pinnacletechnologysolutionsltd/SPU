# CPU ROUTE-D1-R3 — narrow feasibility amendment

Status: proposed preparation; implementation, build, fixtures and physical operations are not authorized. This amendment supersedes only the source/output/staging clauses identified below in the retained I3-R1 contract. All other observation, native binary, durability and equivalence requirements remain mandatory.

Controlling evidence: `build/cpu_route_d1/i3_r2_20261019/REVIEW.md`. Retained parent normative identity: `4fd9c0815a764bd9586beb0c99cf20d6a27e6a19bce201b8576ab805ef2edf8c`. The unfinished ledger is evidence of a draft, not an accepted accounting implementation.

Static preparation command only:

```sh
python3 -B spu_strategy/cpu_route_d1_r3_20261019/check_packet.py
```

The machine packet's `commands.json` contains the exact proposed future argv. None may be executed by this amendment. Missing implemented artifacts/hashes are refusals at their later gate, not preparation PASS substitutions.

## 1. Scope follows actual writers

`permitted_sources.json` is the exact source-edit allowlist, including baseline hashes and function/call-site anchors. Permissions apply only to a private copy; no retained input, production runner or installed tool changes.

| Private source | Permitted call sites | Explicit limits |
| --- | --- | --- |
| `common/router2.cc` | Existing D1 setup/call/queue observation/congestion/safe-stop hooks; diagnostic-session lifetime handoff | No changes to scores, comparator, visitation, RNG seed/draw consumption, neighbor/queue order, task ownership, placement or routing modes. |
| Eight existing D1 headers | Bounded recorder/writer/identity/live/trace/congestion/limits helpers | Same binary schema and durability. Include local enforcing byte interface and all its memory in existing reservations; no general telemetry framework. |
| Private `capture_native.py` | Final `json.dumps(data)+'\n'` write, temporary publication and error handling only | Original capture loops, values, ordering and complete serialized bytes unchanged. |
| Private `pre_route.py` | Final `effective_pre_route.json` write only | This additional metadata boundary is necessary for complete coverage. Preserve every seed/reset/check operation and exact complete JSON bytes. |
| `common/command.cc` | `executeMain` diagnostic `--write` destination/finish block; admitted output-session start/final close/error exits; `run_script_hook` output admission/identity bracket | Keep original `write_json_file`, CLI parser/options, Context operations, routing calls and hook execution order. No command semantics changes. |
| `xilinx/fasm.cc` | `Arch::writeFasm` destination opening/stream/flush/close/publication/error checks | Do not edit `FasmBackend`, `be.write_fasm()` invocation, any `write_*` generator, features, formatting or generation order. |
| Private D1 runner scripts and private copies of existing detached runner/worker/elapsed helper | Existing output writes/redirections, including bootstrap, terminal/deadline and notification artifacts | Preserve payload and existing launch/deadline/containment/notification behavior. No RUNNER-F2 redesign, new workers/attempts, alternate launch or production promotion. |

The extra pre-route metadata writer and private outer-runner writer sites are explicit minimal additions found by the inventory. They cannot be silently excluded from accounting or treated as blanket file-edit permission. Helper modules remain single-purpose, 50–150 lines. No global allocator/I/O interposition, LD_PRELOAD, PYTHONPATH substitution, FUSE/quota-service development or new deployment platform is authorized.

## 2. Authoritative output boundaries

`output_boundaries.json` identifies every application-output producer in the frozen decision/timing paths and in their build/fixture envelopes. It distinguishes two classes:

- Instrumented output: D1 binary records, selected traces, ownership records, canonical export, counters and metadata. Reserve a finite record's complete encoded size before acceptance; a native frame plus its sole JSONL export reserves 771 bytes.
- Existing backend output: decision capture, pre-route metadata, native capture, routed JSON, FASM and logs. Establish an enforcing stream maximum before opening/writing. Check the limit before accepting bytes into a buffer; the lowest-level destination may never flush bytes beyond that admission.

Different processes need not participate in D1's in-process recorder. They must obey the same cumulative allocation through a durable campaign reservation manifest and local enforcing byte limits. The local budget lifetime spans every relevant output stage; it must not die with Router2 before post-route capture/FASM/JSON. Final accepting recorder/run status cannot precede all mandatory native output closes. Moving diagnostic finalization/session ownership to the output tail changes neither routing execution nor binary layout.

Decision invocations retain one aggregate 1 MiB allowance for native capture, routed JSON, FASM **and the previously unclassified decision stream**, plus 16 KiB for stdout/stderr/pre-route/helper metadata. Sequential producers may draw exclusive local subleases from that admitted pool and return unused local capacity only after complete close. Outstanding maxima must never overcommit their enclosing reservation. Timing invocations retain 16 KiB and produce no graph, FASM, native or decision export. These are ceilings, not guarantees of sufficient capacity; a breach is nonaccepting. No silent enlargement or resampling.

Private hooks replace only output paths, so the two corresponding hook argv paths explicitly rebase to hash-frozen private copies. Native executable/fixture/database/XDC/seed/frequency/router/packing/placement flags otherwise remain identical. All variants receive `PYTHONDONTWRITEBYTECODE=1` identically to prevent undeclared Python cache artifacts. Old hook files remain pinned read-only templates; the implementation manifest must bind new actual hook hashes before build. A template hash is not the modified-hook hash.

The backend-output guard is active for an admitted fixture in both baseline and candidate, independently of the D1 recorder. With no D1 output path the recorder still performs no D1 allocation/clock/output/RNG work. Symmetric backend writer guards are the explicit exception for required external-output enforcement, charged and measured in both arms; they do not enable per-call telemetry in timing baselines or CPU tooling.

## 3. Reservation, enforcement and reconciliation

Before the first outer-launcher output, the private `admit_launch.py` must validate the explicit stage authorization, sample one absolute BOOTTIME origin, and durably reserve outer/bootstrap/finalization capacity. It then invokes only the frozen private detached expansion. Admission and launch setup count inside the same stage ceiling; forward remaining seconds, never start a fresh allocation after scheduling delay. A failed admitted launch consumes that stage attempt. Read-only user-manager/environment preflight does not authorize services or workers. Do not repeat the consumed RUNNER-F2 allocation or inherit its protocol here.

The one ledger has a stable campaign identity, category ceilings, consumed bytes, outstanding producer leases, known/unknown status, native timed-work totals and versioned successor digests. Build, F1 and F2 carry it forward; no reset, independent second allowance, pooling or auto-retry. Admission must be durably recorded before granting a producer its local maximum. A short/interrupted/unknown producer retains its full unspent reservation until independently reconciled; no speculative refund.

Count successful application-destination bytes once. Include buffered data at admission, temporary files, metadata, failed-prefix files, indexes, copies and job-private notification/log output. A rename without copying is not charged as a second payload. A copy or rewrite is charged again; deleting failed output gives no byte credit. Count rejected bytes separately without treating rejected bytes as a valid saved artifact. OS journal/page-cache/filesystem write amplification is not application diagnostic payload; every application-created campaign file remains in scope.

Logs use bounded pipe-to-destination writers. On exhaustion keep a labelled partial prefix, record rejected-byte counters and request a native safe stop rather than silently dropping data or blocking indefinitely. Extra transport bytes that were never accepted by the destination are not a second saved-output admission. Only the original external deadline may kill a long routing call; resource stop hooks retain their between-call/join/iteration boundaries. Baseline guard checks may be added at those same resource-only boundaries without per-call timing capture or changed routing decisions.

Post-run reconciliation independently compares actual files/bytes/digests/status against reservations and the boundary inventory. This is a secondary correctness check, never the primary enforcement. Unexpected files, a bypassing writer or mismatched accounting are nonaccepting even if below the total cap.

### Closing manifests without circular hashes

Pre-admit final manifest/close/outer-notification envelopes before publishing the stage ledger digest. Their bounded worst-case charge may be committed conservatively and unused capacity left spent. Distinguish measured artifact bytes, conservatively committed allowances and remaining reservations. Do not call a conservative charge a measured write count. Final ledger state must not contain its own digest or a manifest digest that would depend on itself. After precharging, compute the stable ledger digest, then publish the size-bounded build/stage manifest referencing it without a further ledger mutation. Private outer/notification writes remain within already spent envelopes. A failed final publication stays nonaccepting with its reservation retained. F1/F2 verify the legitimate successor chain, not a stale build digest after a prior stage advanced the ledger.

## 4. Incomplete artifacts never qualify

`output_acceptance.json` defines OUTPUT_CAP, OUTPUT_PARTIAL, OUTPUT_IO_ERROR, OUTPUT_RECONCILIATION_FAILED, OUTPUT_UNACCOUNTED and OUTPUT_IDENTITY_MISMATCH. They are campaign metadata outcomes, not new D1 binary record types or changed search results.

An enforcing writer returns a distinct failure on exhaustion; it never reports a shortened graph/FASM file as complete. Use exclusive admitted partial destinations, no-overwrite publication and mandatory finish checks. A valid-looking final name or parseable prefix cannot override a failed artifact status. A post-publication synchronization failure remains an I/O error even if the file is readable. Required close/status/independent audits must all succeed before artifact acceptance.

Output failure means **qualification failure**, not proof that routing failed or the CPU cannot fit. Existing ARC/constant/skipped/ABORT result classifications remain unchanged. Preserve live publication, completed writes and fsync-confirmed observations; successful synchronization does not establish arbitrary power-loss durability.

## 5. Resources and essential invariants

| Resource | Unchanged bound |
| --- | --- |
| Added native diagnostic memory | 64 MiB total, including new writer/bridge buffers, metadata, TLS/stack, native guard allocation and reserved terminal records; no extra backend allowance or fallback allocations |
| Cumulative diagnostic output | 256 MiB across B1/F1/F2, including failed/partial outputs and outstanding reservations |
| Category ceilings | 32 MiB identity, 64 MiB calls, 128 MiB congestion/external decision graph outputs, 24 MiB traces, 8 MiB terminal/index/log/helper metadata |
| Final reserve | 4 MiB; in-flight 9×4×771 = 27,756 bytes also reserved before calls |
| Native timed diagnostic work | 10 seconds shared across F1 and F2; ≤2 seconds per snapshot, ≤50 ms synchronous stall; safe-boundary nonacceptance on observed overrun |
| Overhead | Every comparison/seed: median ≤5% relative AND ≤100 ms absolute; paired RSS median and maximum positive delta ≤64 MiB |
| Timing matrix | Five comparisons × two seeds × (one warmup pair + nine measured pairs) × two processes = 200; 15-second sample cap, 100-second group caps |

Memory arenas remain 16+16+8+8+8+4+2+2 = 64 MiB. Output categories remain 32+64+128+24+8 = 256 MiB. Byte reservations prevail over nominal record capacities. Host wrapper capacity plans are separate and bounded; they cannot be claimed as native allocation proof. The existing 62 MiB draft mapping plus two unproven external allowances is not accepted by this amendment. I4 must implement and account for every native allocation or refuse activation before routing; B1 compilation alone cannot prove that enforcement works.

Timed blocks use one outermost interval per thread, sum non-overlapping diagnostic work across threads and native invocations, and carry totals through F1/F2. Include added native writer/admission/sync work. Exclude only inline scalar pop/peak updates as before; paired runtime captures their cost. Existing serializer computation is not relabelled diagnostic CPU self-time; any newly added guard work is measured. Host admission/reconciliation time is separately reported and charged to stage wall-clock limits, not mislabelled native CPU time. No prefix-only CPU overhead claim.

Native topology remains the pinned 42-net, 35-cell fixture's single ThreadContext with serial role 8; nine identities are recorder capacity only. Preserve original RNG ownership/seed/draw stream, task order, queue/comparator/visited/scoring/neighbors and routing modes. The required selector remains state[1] / $auto$ff.cc:337:slice$1525.Q / probe_a.A2, iteration1, ordinal1, bounded_serial. Placed bit49347 and correct directions do not prove native user-index/wire resolution or selected-call occurrence. Exact graph/decision/FASM equivalence and corruption controls remain mandatory. Weighted-graph policy comparison remains test-only.

## 6. Proposed staged qualification, no allocation

`budgets.json` partitions the old unallocated fixture proposal without increasing it:

| Stage | Proposed maximum | Attempt count | Scope of a focused PASS |
| --- | --- | --- | --- |
| I4 | No execution allocation | n/a | Private implementation/static correspondence only |
| B1 | 1,800 s | 1 | Four exact builds, dependencies/source/executable identities and build-output accounting; **no native execution** |
| F1 | 400 s | 1 | Functional equivalence, recorder/accounting/corruption/bounded-writer controls, native endpoint/selected-call verification and independent graph/FASM audits |
| F2 | 1,400 s | 1 | Full paired performance matrix and remaining final acceptance rows, with the same F1 identities |

F1's phases are120+100+60+40+80=400. F2's phases are80+1000+320=1400. Together they preserve the old preflight200/accounting100/weighted60/equivalence40/overhead1000/finalization400 =1800 fixture budget. With B1, the total proposal remains3600, not three1800-second jobs. Ceilings are not feasibility guarantees. No pooling, transfer, retries, substitute methods or automatic chaining. Preparation does not consume or authorize any attempt.

F1 uses eight decision invocations at sample IDs000000..000007. F2 retains all200 fresh timing invocations at000008..000207; controls use separate synthetic helper paths. Every sample remains single-use. F1 success cannot be inferred from preparation metadata or baseline graph totals alone. F2 requires the scoped F1 PASS, unchanged actual binary/hook/command/config/input identities and the carried ledger/self-time state. A source/binary drift invalidates that linkage; a separately reviewed new authorization is needed, never an automatic F1 rerun.

The acceptance ledger distinguishes I4_STATIC_PASS, B1_BUILD_PASS, F1_FUNCTIONAL_PASS, F2_PERFORMANCE_PASS and FULL_INSTRUMENTATION_QUALIFICATION. Useful compiled or functional evidence is retained even if a later tranche is pending or fails. It must not be advertised as full instrumentation qualification or 25 MHz CPU qualification. Full ACCEPT still requires every original row, including both median limits and the complete200-invocation matrix. No intermediate PASS authorizes integrated routing.

## 7. Faithful implementation limits and smallest continuation

No remaining requirement is knowingly waived. The inventory requires two narrowly identified additions beyond the shorthand three-writer list: the pre-route metadata write and private outer-runner output writes. Without those explicit permissions, claiming complete enforcement would remain impossible to establish. They are included in this proposed amendment; removing them requires a separately proven bounded-destination mechanism, not post-exit inspection.

Other unresolved items are implementation/qualification work: allocator/TLS capacity proof; session lifetime across export stages; native/Python enforcing interface; safe output-cap propagation; non-overlapping timers; quiescent ownership transaction/reconciliation; complete helper/runners and frozen actual hashes. R3 does not qualify any retained draft. No alternate reduced diagnostic profile is introduced; such a profile would require its own explicit claims and amendment.

Smallest continuation after R3 review: separately authorize I4 against this packet; implement the bounded writer/lease interface at the listed call sites, finish native memory/time/congestion controls, freeze source/hook/runner/admission-capacity identities, and perform static implementation review. Then consider separately authorized B1 compilation without demanding prior performance PASS. Authorize F1 only after executable identity review, F2 only after linked F1 PASS, and CPU diagnostics only after full instrumentation qualification plus a new bounded attempt budget.

No production sources, native implementation or installed tools are changed by R3. No compile, native fixture, integrated route, synthesis, installation or board action is authorized. Standalone arithmetic evidence remains intact; integrated routing, independent FASM signoff and25MHz timing qualification remain open.

Notification delivery failure never changes the detached command result. The result marker retains its original exit-status meaning. A separate output-accounting failure in a notification artifact can make qualification nonaccepting without rewriting an already recorded command result. Delivery itself is never qualification evidence.

Stage T0 is sampled on admission-entry invocation before stage-owned setup or identity checks. The admission helper may not hide preflight time outside the frozen ceiling. Cumulative native self-time is carried at every native admission: grant at most the remaining10s allowance, charge the completed non-overlapping measurement, and refuse new work after exhaustion. An interrupted/unmeasurable process retains its allowance as unknown/nonaccepting; F2 never starts a fresh self-time budget.

The unchanged `limits.json` fixture1800s/one-attempt fields describe the single aggregate fixture qualification program. F1 and F2 are distinct, single-use tranches of that program, not retries or additional combined-fixture opportunities. A failed tranche cannot restart the program. The old combined-fixture launch entry is superseded.

A private Python hook may add only the necessary hash-verified bounded-writer import/bootstrap in addition to its final write replacement. No sys.path/PYTHONPATH injection or other hook logic changes. Any extra module/codec/buffer allocations count inside the unchanged native diagnostic-memory ceiling.

### Remaining B1 destination prerequisite

Retained build evidence includes `compile/CMakeFiles/CMakeConfigureLog.yaml`. CMake writes that diagnostic directly; stdout/stderr capture does not enforce its size. Inventory any version-specific `CMakeOutput.log`, `CMakeError.log` or compiler file diagnostics under the actual pinned flags as well. They remain charged terminal/index diagnostics, not excluded build products. Freeze every such destination and an enforcing attachment before B1. A relay is acceptable only after proving the pinned tool opens/writes that destination without replacing/bypassing it; a directory quota is acceptable only if its existing setup/identity/cap is explicitly reviewed. Neither mechanism is presumed available or compatible here. No tool binary modification, mount, quota service, permission change, installation or exploratory build is authorized.

This is an explicit unresolved feasibility prerequisite, not a reason to discard the native writer amendment or weaken accounting. I4 may prepare/review that limited destination mechanism inside the D1 runner scope. If it cannot establish the bound, B1 must remain HOLD and the missing environment prerequisite must be reviewed separately. Post-run log-size checks do not discharge it. Core-file output is disabled identically with RLIMIT_CORE=0 in future admitted stage/native/helper processes; it must not become an unmetered output channel.
