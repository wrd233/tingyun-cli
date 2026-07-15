# Research Maintenance and Generated Views

## Canonical boundary

The complete protocol history remains in four canonical files under `research/protocol/`:

- `endpoint-contracts.yaml`: Endpoint and Variant ledger, request/response shapes, lineage, environment and evidence observations.
- `workflows.yaml`: Capability and Recipe definitions plus bounded workflow relationships.
- `tingyun-capability-protocol.md`: human-readable protocol interpretation, qualification and investigation narrative.
- `gaps-and-conflicts.md`: unresolved, split and closed gaps with focused validation tasks.

Do not delete historical observations to make these files smaller. Do not hand-maintain another Endpoint or Capability table. Runtime promotion is owned by `src/tingyun_cli/promotion.py`; the generated view joins that registry to the protocol Capability IDs through `protocol_capability`.

## Deterministic generated products

```bash
PYTHONPATH=src python3 research/tools/research_views.py generate
PYTHONPATH=src python3 research/tools/research_views.py check
```

`research/generated/research-index.json` is the Agent interface. It contains stable source hashes; generated counts and distributions; compact Endpoint records; Capability -> Endpoint/Workflow/Gap/Runtime references; parsed capability-matrix claims; workflow requirements; parsed Gap status; orphan contracts; and health issues. `research-overview.md` is the human navigation view. The machine view and semantic diff have committed schemas in `schemas/research-view.schema.json` and `schemas/research-diff.schema.json`.

Generation performs 0 HTTP and 0 LLM calls. It has no current-time field, uses stable sorting, and emits byte-identical output for identical canonical inputs and Runtime promotion registry.

## Health rules

`check` fails when:

- advertised Endpoint or Variant totals drift from generated totals;
- Endpoint, Capability, Workflow, Gap or Variant IDs are duplicated;
- two Endpoints claim the same method/path or two Variants of one Endpoint have the same normalized discriminant;
- Capability, Workflow or Gap references point to unknown objects;
- a Runtime row has no canonical `protocol_capability` mapping;
- a promoted Runtime Endpoint is unknown or not classified `READ`;
- a promoted Runtime capability is not canonically `VERIFIED`;
- the human capability matrix claims `VERIFIED` while the canonical Workflow capability ledger does not;
- committed generated files differ from a fresh deterministic build.

Orphan Endpoint/Capability IDs are reported for review but are not automatically errors: the ledger intentionally preserves supporting, write, rejected and historical contracts that no current Recipe consumes.

## Research diff

Git remains the version system. To generate a compact semantic view between any two committed/generated indices:

```bash
PYTHONPATH=src python3 research/tools/research_views.py diff \
  --before /tmp/base-research-index.json \
  --after research/generated/research-index.json \
  --output /tmp/research-diff.json
```

The diff reports added/removed/modified Endpoint contracts, Capability verification or Runtime maturity changes, and Gap status changes. “Removed” means removed from the compared research view; it does not authorize deleting historical evidence.

## Capture integration sequence

1. Register and locally inspect the new source according to `research/sources/README.md`.
2. Merge new observations into the existing Endpoint/Variant instead of overwriting environment differences.
3. Update Capability/Workflow/Gap references only when exact evidence supports the relationship.
4. Run the existing protocol consistency checker and Research View `check`.
5. Review the generated semantic diff before committing regenerated products.
6. Promote Runtime only after identity, read-only safety, request budget, fixture, failure semantics and immutable Run behavior are all closed.

Protocol verification does not imply Runtime promotion. A Runtime promotion must remain traceable in the generated Capability row and must not make a research-only variant executable.
