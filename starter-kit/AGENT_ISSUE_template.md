# <type>(<scope>): <imperative summary>

<!--
A-Dev Agent-Consumable Issue Template (Definition-of-Ready Contract)
Reference: framework/hardness/08-issue-definition-of-ready.md
-->

## Metadata
- **Type**: `spec` | `feat` | `fix` | `refactor` | `docs` | `test` | `chore` | `infra`
- **Priority**: `critical` | `high` | `medium` | `low`
- **Risk Tier**: `T0_READ_ONLY` | `T1_LOCAL_REVERSIBLE` | `T2_WORKSPACE_BRANCH` | `T3_EXTERNAL_PERSISTENT`
- **Step Budget**: 25

## Context
<!-- Explain the problem, why this change is needed, and any architectural background. -->

## Objective
<!-- Single-sentence, unambiguous statement of the target state. -->

## In Scope
<!-- Explicit list of files and components authorized for creation or modification (max 10 files). -->
- `<repo-relative-path>`: <specific deliverable>

## Out of Scope
<!-- Explicit negative boundaries declaring what must NOT be touched, refactored, or migrated. -->
- Do not modify `<unrelated module>`.
- Do not refactor `<adjacent architecture>`.

## Context Attachments
<!-- Direct repo-relative paths to existing source files, schemas, specs, or test suites. -->
- `<path/to/source.ext>`
- `<path/to/test.ext>`

## Acceptance Criteria
<!-- Verifiable, binary pass/fail statements. Every item must evaluate strictly to TRUE or FALSE. -->
- [ ] <Observable condition or verifiable assertion>
- [ ] <Observable condition or verifiable assertion>

## Verification Contract
<!-- Deterministic CLI command(s) and expected evidence artifacts to prove completion. -->
```bash
<verification-command>
```
**Expected Evidence**: <description of required evidence artifact / exit code 0>

## Stop Conditions
<!-- Conditions requiring immediate execution halt and human escalation (Optional). -->
- Pre-existing tests fail prior to modification.
- Required action exceeds declared Risk Tier.
