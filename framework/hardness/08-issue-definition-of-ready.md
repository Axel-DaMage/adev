# Issue Definition-of-Ready and Atomicity Contract

## Purpose and Problem Statement

An autonomous or semi-autonomous software engineer agent requires explicit, bounded, and verifiable instructions before it begins execution. When issues are ambiguous, compound, under-specified, or missing durable context, agents exhibit characteristic failure modes:
1. **Scope sprawl**: Pursuing tangential changes, over-refactoring adjacent files, or attempting multi-stage projects in a single unmanageable PR.
2. **Hallucinated requirements**: Guessing undocumented domain rules, creating unwanted architectural abstractions, or assuming file paths that do not exist.
3. **Unverifiable completion**: Stopping upon code emission without executing deterministic verification or satisfying objective pass/fail criteria.
4. **Authority overreach**: Modifying protected branches, secrets, configuration, or external systems beyond the authorized risk tier.

This specification establishes the **normative intake contract** for agent-consumable issues within the A-Dev framework. It defines the Definition-of-Ready (DoR), the Atomicity Contract, context attachment standards, machine-checkable validation rules for CI pipelines, and formal escalation semantics when an issue cannot be satisfied.

## Position in the Hardness Architecture

The Issue Definition-of-Ready operates at the boundary between human intent and agent execution:

```
[ Human Intent / Issue Intake ] 
             │
             ▼ (08: Definition-of-Ready & Atomicity Contract)
[ Validated Agent-Consumable Issue ]
             │
             ▼ (03: Human Expectations Contract)
[ Authorized Expectations Boundary ]
             │
             ▼ (01: Policy Model & Precedence)
[ Applicable Hardness Policies ]
             │
             ▼ (02: Skill Contract & 04: Action Risk Model)
[ Bounded Skill Selection & Action Execution ]
             │
             ▼ (QUALITY.md: 50/50 Quality Cycle)
[ Deterministic Verification & Evidence Generation ]
```

---

## Normative Definition-of-Ready (DoR)

An issue is declared `READY_FOR_AGENT_EXECUTION` if and only if all mandatory fields are present, structurally valid, and satisfy the atomicity invariants defined below.

### Core Issue Fields

| Field | Requirement | Type | Semantic Definition |
| --- | --- | --- | --- |
| `id` | Required | String | Unique tracking identifier (e.g., `#104`, `PROJ-123`, `GH-45`). |
| `title` | Required | String | Structured summary following Conventional Commits format: `<type>(<scope>): <imperative summary>`. |
| `type` | Required | Enum | One of: `spec`, `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `infra`. |
| `priority` | Required | Enum | One of: `critical`, `high`, `medium`, `low`. |
| `risk_tier` | Required | Enum | Authority risk tier matching the [Action Risk Model](04-action-risk-authority-model.md): `T0_READ_ONLY`, `T1_LOCAL_REVERSIBLE`, `T2_WORKSPACE_BRANCH`, `T3_EXTERNAL_PERSISTENT`. |
| `context` | Required | String / Markdown | Problem background, system impact, and rationale explaining *why* the change is required. |
| `objective` | Required | String | Single-sentence, unambiguous statement of the target state. |
| `in_scope` | Required | Array of Strings | Explicit list of deliverables, components, and files authorized for modification or creation. |
| `out_of_scope` | Required | Array of Strings | Explicit negative boundaries declaring what the agent **must not** touch, refactor, or migrate. |
| `acceptance_criteria` | Required | Array of Checkbox Items | Machine-checkable, observable, binary pass/fail statements. Minimum of 1 criterion. |
| `context_attachments` | Required | Array of Paths / Refs | Direct repo-relative paths to source files, specs, schemas, test suites, or prior ADRs. |
| `verification_contract` | Required | Object | Exact verification command(s) and expected evidence artifacts required to confirm success. |
| `step_budget` | Optional | Integer | Maximum execution iterations/steps allowed before mandatory halt/escalation (Default: `25`). |
| `stop_conditions` | Optional | Array of Strings | Explicit conditions that trigger immediate execution halt and human escalation. |

---

## Acceptance Criteria Specification

Acceptance criteria (AC) provide the deterministic stopping function for agent execution. Vague criteria cause hallucinated completeness or infinite execution loops.

### AC Format Requirements

1. **Checkbox format**: Every criterion must begin with `- [ ] ` in Markdown or exist as a distinct string in a structured list.
2. **Binary evaluability**: Every criterion must evaluate strictly to `TRUE` or `FALSE`. Subjective terms ("clean", "fast", "well-tested", "user-friendly") are strictly forbidden.
3. **Artifact or behavioral grounding**: Every criterion must reference an explicit file, API response, CLI exit code, or measurable invariant.

### Valid vs. Invalid Acceptance Criteria

| Invalid (Rejected by DoR) | Valid (Satisfies DoR) | Reason for Rejection |
| --- | --- | --- |
| "Refactor authentication to be cleaner." | "- [ ] `src/auth/token.ts` exports `verifyJwt(token: string): Promise<UserSession>` without modifying external signature." | Subjective; lacks target file and exact signature. |
| "Add good tests." | "- [ ] `npm test -- tests/auth.spec.ts` passes with 100% statement coverage on `src/auth/`." | Unverifiable threshold; lacks command and target test suite. |
| "Fix the flaky build." | "- [ ] `npm run build` completes with exit code 0 across 5 consecutive local runs." | Ambiguous success condition; lacks deterministic threshold. |
| "Make it support Windows." | "- [ ] Path separators in `src/utils/fs.ts` use `path.normalize` and pass `npm run test:win32`." | Missing concrete mechanism and verification path. |

---

## Atomicity Contract

The Atomicity Contract enforces the core A-Dev doctrine: **one iteration = one atomic PR = one focused architectural intent**. Compound issues overwhelm agent context windows and degrade verification fidelity.

### Atomicity Invariants

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ATOMICITY INVARIANTS                            │
├────────────────────────────────────────────────────────────────────────┤
│ 1. SINGLE RESPONSIBILITY   │ Exactly 1 architectural intent or fix     │
│ 2. INDEPENDENT TESTABILITY │ Verifiable in isolation without deps      │
│ 3. BOUNDED BLAST RADIUS    │ Max 10 modified source files per task     │
│ 4. 50/50 QUALITY CYCLE     │ Execution fits within 1 session budget    │
└────────────────────────────────────────────────────────────────────────┘
```

#### Invariant 1: Single Responsibility
An issue must address exactly one concern. An issue MUST NOT combine:
- A schema/data model change **AND** a complete UI redesign.
- A bug fix in domain logic **AND** an unsolicited framework upgrade.
- A new feature implementation **AND** legacy code cleanup across unrelated modules.

#### Invariant 2: Independent Testability
The issue must be verifiable against the current repository state without depending on unmerged pull requests, pending infrastructure deployments, or human manual interventions during execution.

#### Invariant 3: Bounded Blast Radius
- Maximum target file count: An atomic agent task SHOULD modify no more than **10 source files** (excluding generated locks, fixtures, or snapshots).
- Tasks touching cross-cutting surfaces must be partitioned into sequential atomic issues.

#### Invariant 4: Single-Cycle Execution Budget
The scope must fit within a single agent session following the A-Dev Broad Quality Cycle (50% code modification, 50% verification and evidence capture).

### Splitting Triggers & Decomposition Rules

When an issue violates any atomicity invariant, it must be split before execution according to the following heuristics:

1. **Linguistic Conjunction Trigger**: If the objective contains "and also", "as well as", or multiple distinct verbs ("implement X, migrate Y, and rewrite Z"), it must be split.
2. **Layer Boundary Trigger**: If an issue spans multiple architectural layers (e.g., Database Migration + Backend API + Frontend Component), split into layer-scoped tasks.
3. **The 3-Iteration Rollout Rule**: New public-facing capabilities or breaking changes must follow a three-issue sequence:
   - *Iteration 1 (Introduction)*: Introduce new contract, engine, or schema behind a feature toggle or non-default path with isolated tests.
   - *Iteration 2 (Migration)*: Switch internal consumers or callers to the new implementation.
   - *Iteration 3 (Deprecation & Cleanup)*: Remove obsolete paths, legacy schemas, and transitional shims.

---

## Context Attachments and Grounding Contract

Agents MUST NOT perform unguided wide-repository discovery when the relevant files are known at issue creation time.

### Grounding Rules

1. **Repository-Relative Paths**: All attachments must be valid relative paths from the workspace root (e.g., `src/core/parser.ts`, `docs/specs/auth.md`).
2. **Durable Baseline Links**: Issues affecting governed standards must explicitly reference the governing documents (e.g., `ADEV.md`, `framework/hardness/01-policy-and-precedence.md`).
3. **No Phantom Paths**: Referencing files that do not exist is permitted ONLY when the explicit objective is to create those files.
4. **Targeted Discovery Anchor**: If exploratory reading is required, the issue must provide a specific starting file or search query.

---

## Escalation Semantics & Disposition Codes

When an agent or automated intake validator encounters an issue that cannot be satisfied or violates DoR, it must halt and return a structured disposition payload rather than guessing or silently failing.

```
                    ┌─────────────────────────┐
                    │ Issue Intake / Dispatch │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Validate DoR Rules    │
                    └──────┬───────────┬──────┘
                   PASS    │           │ FAIL
             ┌─────────────┘           └─────────────┐
             ▼                                       ▼
┌──────────────────────────┐             ┌──────────────────────────┐
│ Agent Execution Begins   │             │ Reject Issue at Intake   │
└────────────┬─────────────┘             │ (INTAKE_REJECT_*)        │
             │                           └──────────────────────────┘
      Runtime Anomaly?
      ┌──────┴──────┐
      │             │
   NO ▼          YES▼
┌───────────┐ ┌──────────────────────────┐
│ Complete  │ │ Escalate & Halt In-Flight│
│ & Evidence│ │ (EXEC_ESCALATE_*)        │
└───────────┘ └──────────────────────────┘
```

### Standard Disposition Codes

| Code | Trigger Phase | Cause | Mandatory Agent Action |
| --- | --- | --- | --- |
| `INTAKE_REJECT_MISSING_FIELD` | Intake / CI | One or more mandatory DoR fields (`objective`, `acceptance_criteria`, `verification_contract`) are missing. | Reject issue with list of missing fields. Do not begin execution. |
| `INTAKE_REJECT_UNBOUNDED_SCOPE` | Intake / CI | Issue violates atomicity invariants (e.g. missing `out_of_scope`, compound objectives). | Reject issue with proposed decomposition into atomic sub-tasks. |
| `INTAKE_REJECT_UNVERIFIABLE_AC` | Intake / CI | Acceptance criteria lack binary evaluability or concrete verification commands. | Reject issue; request deterministic criteria. |
| `EXEC_ESCALATE_BASELINE_BROKEN` | Pre-flight | Existing repository tests fail before any agent modifications are made. | Capture failure log, abort execution, escalate to maintainer. |
| `EXEC_ESCALATE_AMBIGUOUS_SPEC` | In-flight | Contradictory requirements or incompatible baseline contracts discovered. | Halt execution, report exact conflict with file/line evidence. |
| `EXEC_ESCALATE_AUTHORITY_EXCEEDED` | In-flight | Solution requires actions beyond declared `risk_tier` (e.g., editing CI secrets, destructive migrations). | Halt execution, request explicit human authorization. |
| `EXEC_ESCALATE_ATOMICITY_BREACH` | In-flight | Implementation requires modifying >10 files or crossing unstated domain boundaries. | Halt execution, present discovered dependency graph, propose sub-issues. |
| `EXEC_ESCALATE_BUDGET_EXHAUSTED` | In-flight | Step or iteration budget exceeded without passing verification. | Emit diagnostic report of attempted approaches, revert scratch state, escalate. |

### Structured Escalation Payload Format

When an escalation or rejection occurs, the agent or CI validator MUST output a machine-readable summary:

```json
{
  "status": "ESCALATED",
  "disposition_code": "EXEC_ESCALATE_ATOMICITY_BREACH",
  "issue_id": "#104",
  "summary": "Task cannot be completed within single atomic boundary.",
  "evidence": {
    "files_affected_count": 14,
    "discovered_dependencies": [
      "src/database/models/user.ts",
      "src/api/controllers/auth.ts",
      "src/frontend/components/LoginModal.tsx"
    ],
    "explanation": "Modifying authentication tokens requires breaking changes to database schema and frontend session state."
  },
  "suggested_decomposition": [
    { "title": "feat(db): add token_version column to users table", "type": "feat" },
    { "title": "feat(api): support token_version validation in auth controller", "type": "feat" },
    { "title": "feat(ui): handle session revocation in login modal", "type": "feat" }
  ]
}
```

---

## Machine-Checkable Validation Rules

The following rules can be enforced by CI workflows, Git intake hooks, or automated issue triage bots to ensure all issues meet the Definition of Ready before agent dispatch.

| Rule ID | Target Surface | Check / Condition | Severity | Failure Message |
| --- | --- | --- | --- | --- |
| `DOR-VAL-001` | Title / Header | Title matches pattern `^(spec\|feat\|fix\|refactor\|docs\|test\|chore\|infra)(\([a-z0-9_-]+\))?:\s.+` | ERROR | Issue title must follow Conventional Commits formatting. |
| `DOR-VAL-002` | Issue Body | Section `## Objective` or `objective` field is present and non-empty. | ERROR | Missing mandatory Objective section. |
| `DOR-VAL-003` | Issue Body | Objective does not exceed 250 characters and contains a single sentence. | WARN | Objective should be a concise, single-sentence outcome. |
| `DOR-VAL-004` | Issue Body | Section `## Acceptance Criteria` contains at least one `- [ ] ` checkbox item. | ERROR | Issue must contain at least one verifiable checkbox criterion. |
| `DOR-VAL-005` | AC Items | No AC item contains banned subjective words (`clean`, `faster`, `better`, `robust`, `refactor nicely`). | ERROR | Acceptance criteria must be binary and objective. |
| `DOR-VAL-006` | Scope Boundary | Section `## In Scope` and `## Out of Scope` are both present with at least one item each. | ERROR | Explicit positive and negative scope boundaries are required. |
| `DOR-VAL-007` | Context Paths | All file paths listed in Context Attachments exist in repository (unless marked for creation in `in_scope`). | ERROR | Referenced attachment path does not exist in repository. |
| `DOR-VAL-008` | Verification | Section `## Verification` contains an executable code block with the verification command. | ERROR | Missing deterministic verification command. |
| `DOR-VAL-009` | Risk Tier | Valid risk tier is declared (`T0_READ_ONLY`, `T1_LOCAL_REVERSIBLE`, `T2_WORKSPACE_BRANCH`, `T3_EXTERNAL_PERSISTENT`). | ERROR | Invalid or missing risk_tier declaration. |
| `DOR-VAL-010` | Atomicity | Objective and Title do not contain banned conjunction triggers (`and also`, `plus also`, `migrate and rewrite`). | WARN | Compound issue detected. Consider splitting into atomic issues. |
| `DOR-VAL-011` | In-Scope Count | `in_scope` lists no more than 10 distinct files. | WARN | Large scope detected (>10 files). Verify issue cannot be partitioned. |
| `DOR-VAL-012` | Stop Conditions | Optional `## Stop Conditions` are formatted as bullet points if present. | WARN | Stop conditions must be formatted as an enumerated list. |

---

## Mapping to Issue Templates

This specification maps directly to GitHub Issue Forms, GitLab Issue Templates, and Linear/Jira ticket configurations.

### Field-by-Field Cross-Platform Mapping

| Spec Field (DoR) | GitHub Issue Form (`.yml`) | GitLab / Markdown (`.md`) | Linear / Jira |
| --- | --- | --- | --- |
| `title` | Issue Title input | Issue Title | Issue Title / Summary |
| `type` | `dropdown` (id: `type`) | Frontmatter `type:` | Issue Type |
| `risk_tier` | `dropdown` (id: `risk_tier`) | Frontmatter `risk_tier:` | Custom Field: `Risk Tier` |
| `objective` | `textarea` (id: `objective`) | `## Objective` | Description (Lead sentence) |
| `context` | `textarea` (id: `context`) | `## Context` | Description (Background) |
| `in_scope` | `textarea` (id: `in_scope`) | `## In Scope` | Description (In Scope) |
| `out_of_scope` | `textarea` (id: `out_of_scope`) | `## Out of Scope` | Description (Out of Scope) |
| `acceptance_criteria` | `textarea` (id: `acceptance_criteria`) | `## Acceptance Criteria` | Checklist / Subtasks |
| `context_attachments` | `textarea` (id: `context_attachments`) | `## Context Attachments` | Links / Attachments |
| `verification_contract` | `textarea` (id: `verification`) | `## Verification Contract` | Test Script / Acceptance Test |

---

## Reference Examples

### Example 1: Compliant Agent-Consumable Issue (Passes DoR)

```markdown
# fix(auth): prevent session fixation on password reset

## Context
During password reset, existing active sessions are not invalidated, allowing an attacker with an old session cookie to maintain unauthorized access after credential updates.

## Objective
Invalidate all existing session tokens in Redis when a user completes the password reset flow.

## In Scope
- `src/services/auth_service.py`: Add `revoke_all_sessions(user_id)` call to `complete_password_reset`.
- `tests/services/test_auth_service.py`: Add unit tests for session invalidation during password reset.

## Out of Scope
- Do not modify session token generation logic.
- Do not refactor the Redis client connection pool.
- Do not alter UI reset forms or email templates.

## Context Attachments
- `src/services/auth_service.py`
- `src/storage/redis_session_store.py`
- `tests/services/test_auth_service.py`

## Acceptance Criteria
- [ ] `complete_password_reset` calls `session_store.revoke_all_user_sessions(user_id)`.
- [ ] Unit test `test_password_reset_invalidates_all_active_sessions` passes.
- [ ] Existing test suite `pytest tests/services/test_auth_service.py` passes with 0 failures.

## Verification Contract
```bash
pytest tests/services/test_auth_service.py -v
```

## Risk & Authority
- **Risk Tier**: `T2_WORKSPACE_BRANCH`
- **Step Budget**: 15
```

### Example 2: Non-Compliant Issue (Rejected at Intake)

```markdown
# Fix auth and rewrite database layer

## Description
The auth service is slow and weird. Let's fix it, clean up the messy code in the user controller, and also switch the database from MongoDB to PostgreSQL so we are ready for next quarter. Make sure it's fast and well tested.
```

**Intake Validation Report**:
- ❌ `DOR-VAL-001`: Title violates Conventional Commits format and contains compound verb phrase ("Fix auth and rewrite").
- ❌ `DOR-VAL-002`: Missing explicit `## Objective` section.
- ❌ `DOR-VAL-004`: Missing verifiable `- [ ] ` checkbox criteria.
- ❌ `DOR-VAL-005`: Contains subjective terms ("fast", "well tested", "clean up messy code").
- ❌ `DOR-VAL-006`: Missing `## In Scope` and `## Out of Scope` sections.
- ❌ `DOR-VAL-008`: Missing deterministic verification command.
- ❌ `DOR-VAL-010`: Severe atomicity violation (combines bug fixing, refactoring, and database engine replacement).
- **Disposition**: `INTAKE_REJECT_UNBOUNDED_SCOPE`
