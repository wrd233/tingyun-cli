# Tingyun CLI v1.1 Alarm-Driven Investigation Reliability

## Objective

v1.1 makes an alarm-driven investigation reproducible from an external Alarm
Seed through one exact historical Window, Candidate, target-correct Trace, Call
Tree, and deterministic compiled evidence product. It preserves the proven v1
runtime: Core Collect remains three logical requests, Runs remain immutable,
and no WRITE or UNKNOWN endpoint enters the runtime surface.

The four design rules are:

1. Preserve proven Runtime.
2. Repair evidence semantics.
3. Make selection exact.
4. Make composition deterministic.

## Acquisition contract

- Candidate wire identity and labels remain unchanged.
- `semantic_kind` is conservative: only `SpringController/` is Web,
  `DubboProvider/` is Dubbo provider, `requestType=BG` is background, and all
  other names (including bare HTTP verbs or blank names) are unknown.
- Trace action type is resolved from `semantic_kind + requestType`, never by
  splitting a composite label.
- Stable mappings are Web+WEB -> WEB, Web+TX -> TX, Web+TX,IF -> TX, and
  Background+BG -> BG.
- DubboProvider+TX,IF is `UNRESOLVED_TRACE_ACTION_TYPE` until direct Live proof
  exists, so `investigate_trace` is withheld.
- External `name` precedence is `name`, `text`, `host`, `domain`, `value`;
  dependency URI precedence is `uri`, `url`, `value`. No protocol is guessed.
- Recent response/error/throughput rankings retain the wire fields `response`,
  `error`, and `throught`, including unknown semantic/unit status.
- Exception signals distinguish thrown exceptions, logged errors,
  `error=false` log events, and unknown signals. Candidate
  `exceptionCountTotal` remains an uninterpreted wire metric.

## Selection contract

- Names are discovery conditions, not evidence identity.
- Candidate execution identity is `collect_run_id + item_ref` inside the exact
  bound Window.
- Candidate matching is deterministic `EXACT`, `STRONG`, `WEAK`, or
  `NOT_FOUND`; WEAK is never execution-eligible.
- Trace target checking is independent of HTTP success and returns
  `EXACT_TARGET`, `STRONG_TARGET`, `WRONG_TARGET`, or `UNVERIFIABLE`.
- Wrong-target Trace Runs stay auditable but cannot enter an Incident's
  Evidence Map.
- Trace samples remain separate from Candidate aggregates and are assessed as
  `ABNORMAL_ALIGNED`, `NORMAL_CONTRAST`, or `UNKNOWN` without a root-cause
  claim.
- Unresolved Dubbo/interface candidates use parent-transaction-first guidance;
  the CLI does not auto-execute a guessed direct action.

## Composition contract

- `depth evidence-compile` and `depth evidence-validate` are local-only: zero
  HTTP, zero new Run, and zero mutation of data-root/index/inflight state.
- The formal input is
  `schemas/investigation-manifest.schema.json`.
- Registries are explicit and finite: seeds, incidents, windows, Candidate
  bindings, Trace bindings, Call Tree bindings, and Source bindings.
- The compiler validates cross-window identity, exact item identity, canonical
  Incident lineage, target-correct Trace lineage, Call Tree lineage, Source
  role/artifact identity, Raw refs, and verified URL propagation.
- Core output is byte-stable for identical Manifest and immutable Runs and does
  not contain current timestamps, random identifiers, or temporary paths.
- Compilation produces evidence and readiness only. It does not generate a
  Word/Markdown report, an RCA, or an automatic next request.

## Required failure semantics

Compilation is `FAILED` when validation contains an `ERROR`. Required reason
codes include `CROSS_WINDOW_EVIDENCE_REJECTED`, `ITEM_REF_NOT_FOUND`,
`NONCANONICAL_INCIDENT_ID`, `WRONG_TARGET_TRACE_REJECTED`,
`BROKEN_CALL_TREE_LINEAGE`, `MISSING_RUN`, `MISSING_ARTIFACT`,
`INVALID_INVESTIGATION_MANIFEST`, `OUTPUT_DIR_NOT_EMPTY`,
`NONCANONICAL_SOURCE_BINDING`, and `UNRESOLVED_TRACE_ACTION_TYPE`.
Bound `FAILED`/`EMPTY` evidence is `UNUSABLE_ARTIFACT`; path escapes are
`UNSAFE_PATH_REF`; an absent/invalid historical Collect context is
`INVALID_WINDOW_CONTEXT`.

## Security and scope

Private Live Evidence may be read locally and reduced to structural fixtures.
Committed fixtures must use synthetic names, IDs, URLs, and SQL while retaining
field shape, equality, parent/child, and time relationships. Tokens,
Authorization, Cookies, internal IPs/URLs, real names, and real identities must
never be committed.

Out of scope: report generation, LLM/automatic RCA, automatic investigation
loops, Incident clustering, new broad Source surfaces, logs integration,
database access, SQL explain, queues, background jobs, SQLite, and Web UI.
