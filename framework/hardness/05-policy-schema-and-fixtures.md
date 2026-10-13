# Policy Schema and Fixtures

[`policy-schema.json`](policy-schema.json) is a local, vendor-neutral JSON Schema Draft 7 contract for the minimum policy record described in the [policy and precedence model](01-policy-and-precedence.md). It validates the record's structural fields; it does not evaluate behavior, resolve live conflicts, or grant permissions.

## Included fields

The schema requires a stable ID, statement, level, fully declared scope, authority, precedence, rationale, exceptions, evidence requirements, owner, review trigger/date, and expiry action/date. These fields keep a policy reviewable without binding Hardness to an agent vendor or runtime.

## Fixtures and local validation

- [`fixtures/valid-policy.json`](fixtures/valid-policy.json) must satisfy the schema.
- [`fixtures/valid-prompt-injection-policy.json`](fixtures/valid-prompt-injection-policy.json) defines a valid policy record for untrusted-content handling and prompt-injection defense.
- [`fixtures/untrusted-content-envelope-example.json`](fixtures/untrusted-content-envelope-example.json) demonstrates sanitized and enveloped data structures across multiple ingestion vectors.
- [`fixtures/invalid-policy-missing-owner.json`](fixtures/invalid-policy-missing-owner.json) must fail because `owner` is required.

Run from the repository root with PowerShell or Python:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ./framework/hardness/scripts/validate-policy-fixtures.ps1
```

```bash
python3 ./framework/hardness/scripts/validate-hardness.py
```

The scripts parse the local schema and fixtures with built-in standard libraries, verifying policy fields and structural constraints without external dependencies. Fixtures are synthetic and are not operational evidence. When a future policy cites an operational source, it must follow the direct-artifact attribution rule in [`ADEV.md`](../../ADEV.md#evidence-rules).

## Boundary

This is a structural foundation only. Executable policy enforcement, policy storage/lifecycle tooling, and behavioral evaluations remain separate future cycles.
