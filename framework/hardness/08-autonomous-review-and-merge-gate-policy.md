# Autonomous Review Policy and PR Risk Taxonomy for Merge Decisions

## Purpose and Scope

This specification defines the normative policy for evaluating pull requests (PRs) in autonomous, agent-assisted, and automated delivery pipelines. It provides:

1. A deterministic **PR Risk Taxonomy** with explicit classification criteria across four risk tiers.
2. The mapping onto canonical **pipeline labels** (`pr:risk-*`).
3. A **Required Review Evidence Matrix** defining mandatory CI checks, autonomous/adversarial review rigor, human sign-off thresholds, and rollback safeguards for each tier.
4. An unambiguous, **machine-implementable Merge-Gate Decision Table and Algorithm** for automated merge gates (such as the Hermes pipeline).

In A-Dev Hardness, merging a pull request is an **R3 action** (an external effect mutating the canonical repository baseline, as defined in [Action Risk and Authority Model](04-action-risk-authority-model.md)). This specification establishes the exact authority, evidence verification, and gating invariants required before an autonomous agent or automated pipeline may execute or authorize that R3 merge action.

---

## PR Risk Taxonomy

Every pull request introduces a measurable risk profile based on its semantic intent, modified subsystems, line churn, architectural sensitivity, and blast radius.

Pull requests are classified into four mutually exclusive risk tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          PR RISK TAXONOMY                              │
├──────────────┬───────────────────────────────┬─────────────────────────┤
│ Tier         │ Scope & Semantic Boundary     │ Pipeline Label          │
├──────────────┼───────────────────────────────┼─────────────────────────┤
│ Low          │ Non-functional, docs, assets  │ pr:risk-low             │
│ Medium       │ Localized functional change   │ pr:risk-medium          │
│ High         │ Cross-cutting / API / schema  │ pr:risk-high            │
│ Critical     │ Security / auth / core infra  │ pr:risk-critical        │
└──────────────┴───────────────────────────────┴─────────────────────────┘
```

### 1. Low Risk (`pr:risk-low`)

- **Definition**: Changes with zero runtime behavioral execution risk and negligible blast radius.
- **Included changes**:
  - Documentation, markdown guides, book text, comments, typo corrections (`docs/`, `publishing-kit/`, `*.md`).
  - Static non-executable assets, templates, examples without executable scripts.
  - Development-only formatting, linter configuration tweaks with no compilation or build semantics changes.
- **Boundaries and Constraints**:
  - Zero modifications to production source code, business logic, runtime scripts, or executable binaries.
  - Zero modifications to database schemas, migrations, secrets, auth, or CI/CD deploy workflows.
  - Scope: $\le 10$ files modified.

### 2. Medium Risk (`pr:risk-medium`)

- **Definition**: Localized, well-bounded functional changes with contained blast radius and high testability.
- **Included changes**:
  - Localized bug fixes within a single subsystem or module.
  - New isolated feature additions that do not alter existing interfaces or contracts.
  - Internal refactoring covered by existing comprehensive unit and integration test suites.
  - Additions or updates to unit, integration, or synthetic evaluation test suites.
  - Non-breaking minor/patch updates to internal dependencies.
- **Boundaries and Constraints**:
  - Contained within a single subsystem or isolated domain.
  - Zero breaking changes to public APIs, external contracts, or data formats.
  - Zero modifications to core orchestration, cryptography, authentication, authorization, or persistent database migrations.
  - Churn: typically $\le 500$ lines changed/added.

### 3. High Risk (`pr:risk-high`)

- **Definition**: Changes with broad blast radius, cross-subsystem effects, sensitive domain touchpoints, or potential regression hazards.
- **Included changes**:
  - Core architectural modifications, orchestration layer changes, state machine transitions.
  - Public API contract changes, deprecations, or modifications to inter-service protocols.
  - Non-destructive database schema changes, table additions, new persistent indices.
  - Major dependency upgrades, runtime framework upgrades, or build toolchain changes.
  - Modifications to CI/CD workflows, build/test pipelines, release scripts, or validation tooling.
  - Performance-critical paths, concurrency primitives, caching layers, or data serialization formats.
  - Large-scale refactoring spanning multiple subsystems (> 500 lines changed).
- **Boundaries and Constraints**:
  - Requires full regression coverage and documented backward compatibility.
  - Does not modify root security invariants, cryptographic core, or destructive persistence operations.

### 4. Critical Risk (`pr:risk-critical`)

- **Definition**: Changes with catastrophic failure potential, security-critical implications, irreversible state mutations, or systemic availability risk.
- **Included changes**:
  - Authentication, authorization, access control, token/secret handling, cryptographic primitives.
  - Privilege escalation paths, permission boundaries, hardness policy enforcement engine modifications.
  - Destructive database schema migrations (column/table drops, irreversible data transformations).
  - Production infrastructure definitions, root deployment configurations, release signing keys.
  - Emergency hotfixes deployed under active incident response.
  - Any attempt to modify branch protection rules, required checks, rulesets, or merge-gate criteria.
- **Boundaries and Constraints**:
  - Any change touching security-critical paths is classified as `critical` regardless of line count (even 1-line changes).

---

## Classification Rules and Path Heuristics

### Classification Principles

1. **Ceiling Rule (Maximum Risk Principle)**: If a PR touches files or behaviors across multiple risk tiers, the entire PR MUST be classified at the highest applicable tier.
2. **Fail-Safe Default-to-High Rule**: If automated classifiers cannot unambiguously determine the risk tier, or if classification confidence is below 100%, the PR MUST default to `high` until explicitly classified.
3. **No Phantom Low Rule**: Adding a single line of runtime or build code to a documentation PR immediately promotes the PR from `low` to `medium` or higher.

### Path Pattern Mapping Matrix

| File / Path Pattern | Semantic Scope | Base Risk Tier |
|---|---|---|
| `docs/**`, `*.md`, `publishing-kit/**`, `collateral/**` | Documentation and editorial | `pr:risk-low` |
| `starter-kit/examples/**`, `starter-kit/templates/**` | Non-executable reference assets | `pr:risk-low` |
| `tests/**`, `*_test.go`, `*.test.ts`, `tests/*.py` | Test-only additions and improvements | `pr:risk-medium` |
| `src/**` (single module, isolated non-core) | Localized feature/fix | `pr:risk-medium` |
| `src/core/**`, `src/orchestrator/**`, `src/api/**` | Core architecture & public APIs | `pr:risk-high` |
| `migrations/**`, `db/schema.sql` (non-destructive) | Additive database changes | `pr:risk-high` |
| `.github/workflows/**`, `scripts/build.*` | CI/CD and build toolchain | `pr:risk-high` |
| `package.json`, `go.mod`, `Cargo.toml` | Dependency additions / upgrades | `pr:risk-high` |
| `src/auth/**`, `src/crypto/**`, `src/security/**` | Security, auth, cryptography | `pr:risk-critical` |
| `migrations/**` (destructive drops / rewrites) | Irreversible data mutations | `pr:risk-critical` |
| `framework/hardness/policy-schema.json`, merge gate rules | Hardness governance engine | `pr:risk-critical` |

---

## Pipeline Label Taxonomy (`pr:risk-*`)

The pipeline tracks PR risk through standardized GitHub labels.

### Canonical Labels

| Label | Associated Tier | Description |
|---|---|---|
| `pr:risk-low` | Low | Non-functional, docs, formatting, or asset updates. |
| `pr:risk-medium` | Medium | Localized functional fix or feature with high testability. |
| `pr:risk-high` | High | Cross-subsystem, API, schema, CI/CD, or architectural changes. |
| `pr:risk-critical` | Critical | Security, auth, destructive schema, or core governance changes. |

### Label Governance and Lifecycle

1. **Assignment**: Upon PR creation or head commit push, the automated classifier assigns exactly one `pr:risk-*` label.
2. **Single Label Invariant**: A PR MUST have exactly one valid `pr:risk-*` label. If zero or multiple `pr:risk-*` labels exist, the merge gate MUST evaluate to `BLOCK`.
3. **Human Override Protocol**:
   - An authorized human maintainer may upgrade or downgrade a risk label.
   - Any label downgrade (e.g., `pr:risk-high` $\to$ `pr:risk-medium`, or `pr:risk-critical` $\to$ `pr:risk-high`) MUST include an explicit rationale recorded in the PR review thread before merge.
4. **Anti-Tampering Invariant**: Autonomous agents are strictly forbidden from self-downgrading a PR's risk label to bypass review requirements.
5. **Head Commit Invalidation**: Any new commit pushed to the PR head branch invalidates all previous approvals, reviews, and CI status evaluations, requiring re-classification.

---

## Required Review Evidence Matrix

The table below defines the normative evidence required for a PR to be eligible for merge:

| Dimension | `pr:risk-low` | `pr:risk-medium` | `pr:risk-high` | `pr:risk-critical` |
|---|---|---|---|---|
| **CI & Automated Checks** | Lint, format, docs build, static link verification. (PASS) | Full unit tests, integration tests, type checks, lint, build. (PASS) | Full test suite, integration tests, SAST / security scanner, regression tests, clean build artifacts. (PASS) | Full CI suite, SAST, dependency vulnerability scan, migration dry-run, end-to-end integration tests. (PASS) |
| **Autonomous / Adversarial Review** | Automated diff sanity check; verify only low-risk paths modified. | Formal Adversarial Review: diff verification, invariant checks, edge case probing. (`APPROVED`, 0 blocking/actionable findings) | In-depth Adversarial Review: multi-perspective architectural compliance, failure mode analysis, backward compatibility proof. (`APPROVED`) | Comprehensive Adversarial Audit: dual-agent or deep security audit report covering attack surface and failure recovery. (`APPROVED`) |
| **Human Sign-Off** | 0 human reviews required (Autonomous merge permitted). | 0 human reviews required if strict Adversarial Review passes; otherwise 1 human review. | **$\ge 1$ Human Maintainer / CODEOWNER approval mandatory.** | **$\ge 2$ Human Approvers (including Domain/Security Owner) mandatory.** |
| **Rollback & Operational Evidence** | Standard git revert capability. | Verified isolated changeset; clean single-commit revert path. | Documented rollback plan in PR body; verified zero-downtime / backward compatibility. | Tested rollback script / migration rollback procedure; feature flag or staged rollout plan verified. |
| **Autonomous Merge Allowed?** | **YES** (Agent may self-merge when checks pass). | **YES** (Agent may self-merge when checks and adversarial review pass). | **NO** (Agent cannot merge without human approval). | **NO** (Agent never authorized to self-merge). |

---

## Review Comment Taxonomy & Resolution

Review findings from automated tools, adversarial agents, and human reviewers are classified into three severity levels:

```
┌────────────────────────────────────────────────────────────────────────┐
│                       COMMENT SEVERITY TAXONOMY                        │
├────────────┬───────────────────────────────────────┬───────────────────┤
│ Level      │ Definition                            │ Gate Impact       │
├────────────┼───────────────────────────────────────┼───────────────────┤
│ 🔴 BLOCKING │ Bugs, security hazards, regressions   │ BLOCKS MERGE      │
│ 🟡 ACTIONABLE| Improvements, test gaps, edge cases │ BLOCKS MERGE*     │
│ 🟢 NITPICK  │ Style, phrasing, optional suggestions │ DOES NOT BLOCK    │
└────────────┴───────────────────────────────────────┴───────────────────┘
* Must be resolved or explicitly converted to tracked issue with maintainer approval.
```

- 🔴 **BLOCKING**: Any functional defect, test failure, security vulnerability, breaking API change without deprecation, or invariant violation. **Gate Action**: `BLOCK`.
- 🟡 **ACTIONABLE**: Important architectural suggestions, missing non-critical edge cases, test quality improvements, or performance concerns. **Gate Action**: `BLOCK` until resolved by code change or explicitly acknowledged and deferred by a maintainer into a tracked follow-up issue.
- 🟢 **NITPICK**: Cosmetic formatting, minor naming preference, typographical comment changes. **Gate Action**: Does not block merge.

---

## Merge-Gate Decision Table & Evaluation Algorithm

### Formal Evaluation Model

The merge gate is a deterministic pure function $f(V) \to D$, mapping an input state vector $V$ to a discrete decision $D \in \{\text{MERGE}, \text{WAIT}, \text{BLOCK}, \text{ESCALATE}\}$.

#### Input Vector Definition

$$V = (R, S_{CI}, S_{AR}, S_{HR}, C_{mergeable}, C_{comments}, C_{head}, A_{admin})$$

| Component | Symbol | Allowed Domain | Description |
|---|---|---|---|
| **Risk Tier** | $R$ | `low`, `medium`, `high`, `critical`, `invalid` | Derived from the single active `pr:risk-*` label. |
| **CI Status** | $S_{CI}$ | `SUCCESS`, `PENDING`, `FAILURE`, `NEUTRAL` | Aggregated status check rollup. |
| **Adversarial Review** | $S_{AR}$ | `APPROVED`, `CHANGES_REQUESTED`, `PENDING`, `NONE` | Outcome of autonomous adversarial review. |
| **Human Review** | $S_{HR}$ | `APPROVED_2+`, `APPROVED_1`, `CHANGES_REQUESTED`, `PENDING`, `NONE` | Validated human review approvals. |
| **Git Mergeable** | $C_{mergeable}$ | `CLEAN`, `CONFLICTING`, `UNKNOWN` | Git branch mergeability state. |
| **Comment Status** | $C_{comments}$ | `CLEAN`, `ACTIONABLE_UNRESOLVED`, `BLOCKING_UNRESOLVED` | Unresolved comment status. |
| **Commit Head Guard** | $C_{head}$ | `MATCH`, `MISMATCH` | Verifies evaluation SHA equals PR current HEAD SHA. |
| **Admin Bypass** | $A_{admin}$ | `TRUE`, `FALSE` | Detects forbidden attempt to use `--admin` flag. |

---

### Step 1: Invariant Pre-Checks (Fail-Fast Gate)

Evaluate the following rules in strict sequence. If any rule matches, return immediately:

1. **Admin Bypass Rule**: If $A_{admin} = \text{TRUE} \implies \mathbf{BLOCK}$ (*Hardness Security Violation: `--admin` flag forbidden*).
2. **Label Validity Rule**: If $R = \text{invalid} \implies \mathbf{BLOCK}$ (*Missing, unknown, or multiple `pr:risk-*` labels*).
3. **Head Freshness Rule**: If $C_{head} = \text{MISMATCH} \implies \mathbf{BLOCK}$ (*Stale evaluation: PR head commit has changed*).
4. **Merge Conflict Rule**: If $C_{mergeable} = \text{CONFLICTING} \implies \mathbf{BLOCK}$ (*Merge conflicts present*).
5. **Mergeable Pending Rule**: If $C_{mergeable} = \text{UNKNOWN} \implies \mathbf{WAIT}$ (*GitHub mergeability calculation in progress*).
6. **CI Failure Rule**: If $S_{CI} = \text{FAILURE} \implies \mathbf{BLOCK}$ (*Required CI checks failed*).
7. **Blocking Comments Rule**: If $C_{comments} = \text{BLOCKING_UNRESOLVED} \implies \mathbf{BLOCK}$ (*Unresolved blocking comments exist*).
8. **Actionable Comments Rule**: If $C_{comments} = \text{ACTIONABLE_UNRESOLVED} \implies \mathbf{BLOCK}$ (*Unresolved actionable comments exist*).
9. **Changes Requested Rule**: If $S_{AR} = \text{CHANGES_REQUESTED} \lor S_{HR} = \text{CHANGES_REQUESTED} \implies \mathbf{BLOCK}$ (*Changes requested by reviewer*).
10. **CI Pending Rule**: If $S_{CI} = \text{PENDING} \implies \mathbf{WAIT}$ (*CI checks currently running*).

---

### Step 2: Risk-Tier Decision Truth Table

When all Invariant Pre-Checks pass ($S_{CI} = \text{SUCCESS}$, $C_{mergeable} = \text{CLEAN}$, $C_{comments} = \text{CLEAN}$, $C_{head} = \text{MATCH}$, $A_{admin} = \text{FALSE}$), evaluate the row matching $(R, S_{AR}, S_{HR})$:

| Rule # | Risk Tier ($R$) | Adversarial Review ($S_{AR}$) | Human Review ($S_{HR}$) | Decision ($D$) | Rationale |
|:---:|---|---|---|:---:|---|
| **L1** | `low` | `APPROVED` or `NONE` | Any non-rejecting | **`MERGE`** | Low-risk criteria met. Autonomous merge authorized. |
| **L2** | `low` | `PENDING` | Any non-rejecting | **`WAIT`** | Autonomous diff sanity check in progress. |
| **M1** | `medium` | `APPROVED` | Any non-rejecting | **`MERGE`** | Medium-risk criteria met via certified Adversarial Review. |
| **M2** | `medium` | `NONE` | `APPROVED_1` or `APPROVED_2+` | **`MERGE`** | Medium-risk criteria met via human approval. |
| **M3** | `medium` | `PENDING` | `NONE` or `PENDING` | **`WAIT`** | Adversarial review in progress. |
| **M4** | `medium` | `NONE` | `PENDING` | **`WAIT`** | Awaiting review completion. |
| **H1** | `high` | `APPROVED` | `APPROVED_1` or `APPROVED_2+` | **`MERGE`** | High-risk criteria met: Adversarial review + Human approval present. |
| **H2** | `high` | `APPROVED` | `NONE` or `PENDING` | **`ESCALATE`** | Awaiting mandatory human maintainer sign-off. |
| **H3** | `high` | `PENDING` | Any | **`WAIT`** | Adversarial review in progress. |
| **H4** | `high` | `NONE` | `APPROVED_1` or `APPROVED_2+` | **`WAIT`** | Awaiting required adversarial review completion. |
| **C1** | `critical` | `APPROVED` | `APPROVED_2+` | **`MERGE`** | Critical-risk criteria met: Adversarial review + $\ge 2$ Human approvals present. |
| **C2** | `critical` | `APPROVED` | `APPROVED_1` | **`ESCALATE`** | Critical-risk requires second human sign-off (Domain/Security Owner). |
| **C3** | `critical` | `APPROVED` | `NONE` or `PENDING` | **`ESCALATE`** | Critical-risk awaiting dual human sign-offs. |
| **C4** | `critical` | `PENDING` | Any | **`WAIT`** | Adversarial audit in progress. |
| **C5** | `critical` | `NONE` | Any | **`WAIT`** | Awaiting required adversarial audit completion. |

---

## Machine-Implementable Evaluation Algorithm

Below is the reference algorithm implemented in deterministic pseudocode for automated merge gate engines:

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class Decision(str, Enum):
    MERGE = "MERGE"
    WAIT = "WAIT"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"

class RiskTier(str, Enum):
    LOW = "pr:risk-low"
    MEDIUM = "pr:risk-medium"
    HIGH = "pr:risk-high"
    CRITICAL = "pr:risk-critical"

class StatusCheck(str, Enum):
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    FAILURE = "FAILURE"
    NEUTRAL = "NEUTRAL"

class ReviewState(str, Enum):
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    PENDING = "PENDING"
    NONE = "NONE"

@dataclass
class MergeGateContext:
    pr_number: int
    head_sha: str
    evaluated_sha: str
    risk_labels: List[str]
    mergeable: str              # "CLEAN", "CONFLICTING", "UNKNOWN"
    ci_status: StatusCheck
    adversarial_review: ReviewState
    human_approval_count: int
    human_changes_requested: bool
    unresolved_blocking_comments: int
    unresolved_actionable_comments: int
    admin_flag_requested: bool

@dataclass
class GateResult:
    decision: Decision
    reason: str
    violations: List[str]

def evaluate_merge_gate(ctx: MergeGateContext) -> GateResult:
    # 1. Invariant: Anti-admin security rule
    if ctx.admin_flag_requested:
        return GateResult(
            Decision.BLOCK,
            "Security Violation: --admin bypass flag is strictly forbidden.",
            ["FORBIDDEN_ADMIN_BYPASS"]
        )

    # 2. Invariant: Risk label validation
    valid_risk_labels = [r.value for r in RiskTier]
    matching_labels = [lbl for lbl in ctx.risk_labels if lbl in valid_risk_labels]
    if len(matching_labels) != 1:
        return GateResult(
            Decision.BLOCK,
            f"Risk Label Invariant Violated: PR must have exactly 1 valid pr:risk-* label. Found: {matching_labels}",
            ["INVALID_RISK_LABEL_COUNT"]
        )
    risk = RiskTier(matching_labels[0])

    # 3. Invariant: Head freshness guard (prevent TOCTOU race conditions)
    if ctx.head_sha != ctx.evaluated_sha:
        return GateResult(
            Decision.BLOCK,
            f"Head Commit Invalidation: Evaluated SHA ({ctx.evaluated_sha}) does not match current PR HEAD ({ctx.head_sha}).",
            ["STALE_EVALUATION_SHA"]
        )

    # 4. Invariant: Mergeability check
    if ctx.mergeable == "CONFLICTING":
        return GateResult(
            Decision.BLOCK,
            "Git merge conflict detected. Rebase on target branch required.",
            ["MERGE_CONFLICTS"]
        )
    if ctx.mergeable == "UNKNOWN":
        return GateResult(
            Decision.WAIT,
            "Git mergeability calculation is pending from GitHub.",
            ["MERGEABILITY_PENDING"]
        )

    # 5. Invariant: CI check status
    if ctx.ci_status == StatusCheck.FAILURE:
        return GateResult(
            Decision.BLOCK,
            "CI status check rollup failed.",
            ["CI_FAILED"]
        )

    # 6. Invariant: Review comments resolution
    if ctx.unresolved_blocking_comments > 0:
        return GateResult(
            Decision.BLOCK,
            f"There are {ctx.unresolved_blocking_comments} unresolved BLOCKING review comments.",
            ["UNRESOLVED_BLOCKING_COMMENTS"]
        )
    if ctx.unresolved_actionable_comments > 0:
        return GateResult(
            Decision.BLOCK,
            f"There are {ctx.unresolved_actionable_comments} unresolved ACTIONABLE review comments.",
            ["UNRESOLVED_ACTIONABLE_COMMENTS"]
        )

    # 7. Invariant: Changes requested
    if ctx.adversarial_review == ReviewState.CHANGES_REQUESTED or ctx.human_changes_requested:
        return GateResult(
            Decision.BLOCK,
            "Reviewers have requested changes on this pull request.",
            ["CHANGES_REQUESTED"]
        )

    # 8. Invariant: CI pending
    if ctx.ci_status == StatusCheck.PENDING:
        return GateResult(
            Decision.WAIT,
            "CI status checks are currently running.",
            ["CI_PENDING"]
        )

    # 9. Tier-Specific Evidence Verification
    if risk == RiskTier.LOW:
        if ctx.adversarial_review == ReviewState.PENDING:
            return GateResult(Decision.WAIT, "Adversarial sanity review in progress.", ["AR_PENDING"])
        return GateResult(Decision.MERGE, "Low-risk PR passed all checks. Autonomous merge authorized.", [])

    elif risk == RiskTier.MEDIUM:
        if ctx.adversarial_review == ReviewState.PENDING:
            return GateResult(Decision.WAIT, "Adversarial review in progress.", ["AR_PENDING"])
        if ctx.adversarial_review == ReviewState.APPROVED or ctx.human_approval_count >= 1:
            return GateResult(Decision.MERGE, "Medium-risk PR approved by certified review evidence.", [])
        return GateResult(Decision.WAIT, "Awaiting adversarial review or human sign-off.", ["REVIEW_PENDING"])

    elif risk == RiskTier.HIGH:
        if ctx.adversarial_review == ReviewState.PENDING:
            return GateResult(Decision.WAIT, "Adversarial review in progress.", ["AR_PENDING"])
        if ctx.adversarial_review != ReviewState.APPROVED:
            return GateResult(Decision.WAIT, "Awaiting required adversarial review approval.", ["AR_REQUIRED"])
        if ctx.human_approval_count < 1:
            return GateResult(
                Decision.ESCALATE,
                "High-risk PR requires at least 1 human maintainer/CODEOWNER approval.",
                ["HUMAN_APPROVAL_REQUIRED"]
            )
        return GateResult(Decision.MERGE, "High-risk PR passed CI, adversarial review, and human approval.", [])

    elif risk == RiskTier.CRITICAL:
        if ctx.adversarial_review == ReviewState.PENDING:
            return GateResult(Decision.WAIT, "Critical-tier adversarial audit in progress.", ["AR_PENDING"])
        if ctx.adversarial_review != ReviewState.APPROVED:
            return GateResult(Decision.WAIT, "Awaiting critical adversarial audit approval.", ["AR_REQUIRED"])
        if ctx.human_approval_count < 2:
            return GateResult(
                Decision.ESCALATE,
                f"Critical-risk PR requires at least 2 human approvers (Domain/Security Owner). Current: {ctx.human_approval_count}.",
                ["DUAL_HUMAN_APPROVAL_REQUIRED"]
            )
        return GateResult(Decision.MERGE, "Critical PR passed CI, deep audit, and dual human approvals.", [])

    return GateResult(Decision.BLOCK, "Unhandled state in merge-gate evaluation.", ["UNKNOWN_STATE"])
```

---

## Security Invariants and Auditability

1. **Explicit Merge Record**: Every merge executed by the pipeline MUST generate a durable merge record containing:
   - Evaluated Commit SHA and target branch tip SHA.
   - Assigned Risk Tier and labeling source.
   - CI Workflow Run URLs and status check rollup digest.
   - Adversarial Review summary and Reviewer IDs.
   - Human Approver IDs and timestamps.
2. **No `--admin` Bypass Invariant**: The `--admin` flag bypasses all safety checks and branch protections. Hardness strictly forbids agents from invoking `gh pr merge --admin` under any standard operating condition.
3. **Emergency Break-Glass Protocol**: If emergency production recovery requires bypassing the merge gate, the action MUST be executed manually by authorized human architects outside the autonomous loop, and the rationale MUST be logged in the repository incident log.
