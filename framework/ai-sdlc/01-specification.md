# A-Dev AI-SDLC Declarative Configuration Specification

**Status:** Normative Contract  
**Schema Identifier:** `https://adev.dev/schemas/v1/ai-sdlc.schema.json`  
**Schema File:** [`framework/ai-sdlc.schema.json`](../ai-sdlc.schema.json) / [`framework/schema/ai-sdlc.schema.json`](../schema/ai-sdlc.schema.json)  
**File Convention:** `.ai-sdlc.yaml` or `.ai-sdlc.yml` (or `.ai-sdlc.json`) placed at repository root  

---

## 1. Executive Summary & Purpose

Modern software development with autonomous and semi-autonomous AI coding agents requires clear, unambiguous, machine-readable contracts governing:
1. What commands verify acceptable behavior.
2. How much autonomy and authority the agent is granted.
3. How pull requests are reviewed, gated, and merged.
4. What label taxonomy tracks risk, change types, and lifecycle stages.
5. Which foundation model tiers are suited for distinct tasks.
6. When and how the agent must stop and escalate to human maintainers.

`.ai-sdlc.yaml` is the canonical per-repository declarative configuration contract for the entire AI-assisted software development lifecycle (AI-SDLC). It bridges the repository's human intent (stored in [`ADEV.md`](../../ADEV.md) and the Living Baseline) with automated tooling, CI/CD runners, and autonomous coding agents.

---

## 2. Core Architecture & Schema Invariants

### 2.1 Schema Resolution and File Placement
- The canonical location for repository configuration is `./.ai-sdlc.yaml` at the root of the repository.
- Runtimes MUST accept `.ai-sdlc.yaml`, `.ai-sdlc.yml`, or `.ai-sdlc.json`.
- Configurations MUST declare `version: "1.0"` (or compliant semver string matching `^[0-9]+(\.[0-9]+)*$`).
- Schema validation MUST be performed against [`framework/ai-sdlc.schema.json`](../ai-sdlc.schema.json).

### 2.2 Top-Level Sections
A valid `.ai-sdlc.yaml` specification is composed of six primary sections:
1. `repository`: Metadata and operational archetype.
2. `autonomy`: Trust level on the Progressive Autonomy Ladder, risk boundaries, sandboxing, tool permissions, and forbidden actions.
3. `verification`: Named verification profiles, commands, timeouts, coverage gates, and evidence artifacts.
4. `review`: Human review policies, AI bot review integration (CodeRabbit), sign-off matrices, auto-merge constraints, and branch protection.
5. `labels`: Label taxonomy definitions, prefixes, enforcement flags, and color coding.
6. `model_routing`: Task-to-model tier routing hints, context budgets, and cost governance.
7. `escalation`: Contact directory, automated stop triggers, and escalation dispositions.

---

## 3. The Progressive Autonomy Ladder & Risk Matrix

A-Dev defines a 5-level **Progressive Autonomy Ladder** governing agent authority. Each autonomy level maps strictly to maximum permitted **Action Risk Classes** ($R_0$ through $R_3$) as defined in the [Action Risk and Authority Model](../hardness/04-action-risk-authority-model.md).

```
Level 4: Full Lifecycle Autonomy ─── [ R0 + R1 + R2 + Bounded R3 + Auto-Recovery ]
Level 3: Guarded Merge ───────────── [ R0 + R1 + R2 + Guarded R3 Auto-Merge ]
Level 2: Autonomous PR ───────────── [ R0 + R1 + R2 (Branch + PR Creation) ]
Level 1: Assisted Iteration ──────── [ R0 + R1 (Local Workspace Only) ]
Level 0: Advisory / Read-Only ────── [ R0 Only (Inspection & Diff Generation) ]
```

### 3.1 Ladder Levels and Semantic Definitions

| Level | Identifier | Canonical Label | Permitted Risk Tiers | Operational Capabilities | Human Gate |
|---|---|---|---|---|---|
| **0** | `L0` / `A0` | `autonomy:a0-human-only` | `R0` (Read-only) | Read repository, query search, analyze code, output advisory comments and proposed patches. | Human executes all actions. Agent has zero write authority. |
| **1** | `L1` / `A1` | `autonomy:a1-assisted` | `R0`, `R1` (Local Mutation) | Create local scratchpad files, edit workspace code, execute local build/test verification. | Human reviews all local commits and pushes branches manually. |
| **2** | `L2` / `A2` | `autonomy:a2-autonomous-pr` | `R0`, `R1`, `R2` (Shared Mutation) | Create task branches, edit code, run verification profiles, generate evidence, push branch, open pull requests. | Human review and approval required before merging to main. |
| **3** | `L3` / `A3` | `autonomy:a3-guarded-merge` | `R0`, `R1`, `R2`, conditional `R3` | Complete Level 2 capabilities plus automated merging of PRs when all strict verification profiles pass and review policies are satisfied. | Automated gating for bounded scopes; human sign-off mandatory for infrastructure/security. |
| **4** | `L4` / `A4` | `autonomy:a4-full-lifecycle` | `R0`, `R1`, `R2`, `R3` | Orchestrate multi-stage delivery, dispatch sub-agents, monitor staging/production rollouts, execute automated rollbacks upon failure. | Policy-bounded autonomy; escalates only on policy breach, budget exhaustion, or unrecoverable error. |

### 3.2 Action Risk Classes ($R_0$ to $R_3$)

- **$R_0$ — Read-Only & Inspection:** Non-destructive operations (file reads, text searches, dependency queries, status inspections). Zero persistent side effects.
- **$R_1$ — Reversible Local Mutation:** File writes within local workspace, local test/build execution, branch creation, local git commits. Isolated to the active worktree.
- **$R_2$ — Shared Multi-Party Mutation:** Remote git push, pull request creation, issue comments, build artifact publishing to non-production registries.
- **$R_3$ — High-Impact / Privileged / Irreversible:** Merging PRs to default/protected branches, production deployments, secret access, altering repository rulesets or branch protection, using administrative bypass flags (`--admin`).

### 3.3 Sandboxing and Security Rules
- **Workspace Confinement:** When `workspace_only_writes: true`, agents MUST NOT write outside the repository root or active worktree.
- **Network Boundaries:** `network_access` defines allowed external calls (`none`, `restricted`, `package-registries-only`, `full`).
- **Forbidden Actions Invariant:** The following operations MUST remain strictly forbidden unless explicit administrative override is configured:
  1. `force_push` to protected branches (`main`, `master`, `release/*`).
  2. `admin_bypass` (e.g. `gh pr merge --admin` or bypassing branch protection).
  3. `modify_rulesets` or altering repository security policies.
  4. `direct_commit_to_main`.
  5. `expose_secrets` (printing tokens, dumping credential environment variables).

---

## 4. Verification Profiles

The `verification` block specifies deterministic verification suites that establish proof of correctness for code changes.

```yaml
verification:
  default_profile: "standard"
  profiles:
    fast:
      description: "Fast inner-loop checks (lint, format, quick unit tests)"
      commands:
        - "npm run lint"
        - "npm run test:fast"
      timeout_seconds: 60
      working_directory: "."
      required_on: ["inner_loop", "on_save"]
    standard:
      description: "Standard CI validation (typecheck, full test suite, build)"
      commands:
        - "npm run typecheck"
        - "npm test"
        - "npm run build"
      timeout_seconds: 300
      working_directory: "."
      required_on: ["pre_pr", "pr_review"]
    strict:
      description: "Strict release and merge gating"
      commands:
        - "npm run test:coverage"
        - "npm run security:audit"
      timeout_seconds: 900
      coverage_threshold:
        line: 85
        branch: 80
      artifacts:
        - "coverage/lcov.info"
        - "test-results.xml"
      required_on: ["pre_merge", "release"]
```

### 4.1 Verification Lifecycle Triggers
Profiles declare `required_on` triggers:
- `inner_loop`: Invoked by agents during local iteration cycles.
- `on_save`: Invoked on incremental file modifications.
- `pre_commit`: Invoked prior to committing local changes.
- `pre_pr`: Invoked prior to pushing branch and opening a pull request.
- `pr_review`: Invoked during automated or peer PR review.
- `pre_merge`: Mandatory gating suite before merge execution.
- `release`: Verification suite before tag or package publication.
- `nightly` / `manual`: Scheduled or ad-hoc diagnostic runs.

### 4.2 Pass Criteria and Evidence
A verification profile passes if and only if:
1. Every command in `commands` exits with code `0`.
2. Total execution time does not exceed `timeout_seconds`.
3. If `coverage_threshold` is specified, measured coverage equals or exceeds required metrics.
4. If `artifacts` are specified, listed evidence files exist upon completion.

---

## 5. Review & Merge Policy

The `review` section defines human and automated review rules for pull requests.

```yaml
review:
  required_approvals: 1
  code_review_bots:
    coderabbit:
      enabled: true
      blocking_severities: ["critical", "high", "BLOCKING"]
      treat_actionable_as_blocking: false
  signoff_matrix:
    r0:
      required_human_approvals: 0
      auto_merge_eligible: true
    r1:
      required_human_approvals: 0
      auto_merge_eligible: true
    r2:
      required_human_approvals: 1
      auto_merge_eligible: false
    r3:
      required_human_approvals: 2
      required_roles: ["architect", "security_lead"]
      auto_merge_eligible: false
  auto_merge:
    enabled: false
    max_risk_tier: "R1"
    merge_method: "squash"
    required_status_checks:
      - "ci/tests"
      - "ci/lint"
    require_linear_history: true
    delete_branch_on_merge: true
  branch_protection:
    protected_branches: ["main"]
    enforce_admin_bypass_prevention: true
```

### 5.1 Signoff Matrix & Risk Partitioning
- **$R_0$ / $R_1$:** Low-risk documentation or typo fixes may be configured with 0 human approvals and auto-merge eligibility.
- **$R_2$:** Standard feature and bug-fix changes require at least 1 human approval.
- **$R_3$:** Architectural, security, or infrastructural modifications require 2+ human approvals with role enforcement (e.g. `architect`, `security_lead`).

### 5.2 Auto-Merge Invariants
Auto-merge MUST ONLY execute when:
1. `review.auto_merge.enabled` is `true`.
2. The pull request risk class does not exceed `review.auto_merge.max_risk_tier`.
3. All `required_status_checks` report `SUCCESS`.
4. All CodeRabbit and bot review comments with severities in `blocking_severities` are resolved.
5. No unresolved merge conflicts exist.

---

## 6. Label Taxonomy

The `labels` section defines canonical metadata tags applied to issues and pull requests to ensure observable pipeline state.

```yaml
labels:
  enforce_on_prs: true
  enforce_on_issues: false
  taxonomy:
    risk:
      prefix: "risk:"
      required: true
      enforce_single: true
      values:
        - name: "risk:r0"
          description: "Read-only inspection"
          color: "0e8a16"
        - name: "risk:r1"
          description: "Reversible local mutation"
          color: "2cbe4e"
        - name: "risk:r2"
          description: "Shared multi-party mutation"
          color: "fbca04"
        - name: "risk:r3"
          description: "High-impact privileged mutation"
          color: "d93f0b"
    type:
      prefix: "type:"
      required: true
      values:
        - name: "type:feat"
          description: "New functional capability"
          color: "a2eeef"
        - name: "type:fix"
          description: "Bug fix or error resolution"
          color: "d73a4a"
        - name: "type:spec"
          description: "Specification or contract update"
          color: "0075ca"
        - name: "type:doc"
          description: "Documentation update"
          color: "0052cc"
```

### 6.1 Standard Label Namespaces
1. `risk:` — Action risk tier (`risk:r0`, `risk:r1`, `risk:r2`, `risk:r3`).
2. `autonomy:` — Progressive autonomy level (`autonomy:a0-human-only` through `autonomy:a4-full-lifecycle`).
3. `type:` — Change category (`type:feat`, `type:fix`, `type:spec`, `type:doc`, `type:refactor`, `type:chore`).
4. `stage:` — Delivery stage (`stage:01-contract`, `stage:02-impl`, `stage:03-verify`, `stage:04-review`).
5. `status:` — Execution state (`status:in-progress`, `status:blocked`, `status:needs-human-input`, `status:verified`).

---

## 7. Model Routing Hints & Cost Governance

Model routing hints allow orchestrators to assign appropriate foundation model capabilities to each task category based on complexity and assurance requirements.

```yaml
model_routing:
  default_tier: "balanced"
  task_profiles:
    architecture_and_contracts:
      tier: "reasoning"
      preferred_models:
        - "claude-3-7-sonnet"
        - "o3-mini"
        - "deepseek-r1"
      temperature: 0.1
      max_context_tokens: 128000
    code_generation:
      tier: "balanced"
      preferred_models:
        - "claude-3-7-sonnet"
        - "gemini-2.5-pro"
        - "gpt-4o"
      temperature: 0.2
    fast_triage_and_docs:
      tier: "fast"
      preferred_models:
        - "claude-3-5-haiku"
        - "gemini-2.5-flash"
        - "gpt-4o-mini"
      temperature: 0.3
  cost_governance:
    max_budget_per_run_usd: 5.00
    max_turns_per_session: 50
    alert_threshold_usd: 2.50
```

### 7.1 Model Tiers
- **`fast`:** Low-latency, cost-efficient models for linting, typo corrections, documentation, and label triage.
- **`balanced`:** High-capability generalist models for core feature implementation, test creation, and refactoring.
- **`reasoning`:** Extended-thinking / deep-reasoning models for architectural contracts, formal schema design, security audits, and complex debugging loops.
- **`custom`:** Domain-specific or fine-tuned self-hosted models.

---

## 8. Escalation Contacts & Stop Triggers

The `escalation` section defines human-in-the-loop safeguards. When an autonomous run encounters boundary conditions or repeated failures, it MUST halt and escalate.

```yaml
escalation:
  contacts:
    - role: "architect"
      name: "Platform Architect"
      github_handle: "@platform-architect"
      email: "architect@example.com"
    - role: "security_lead"
      name: "AppSec Team"
      github_handle: "@security-team"
      email: "security@example.com"
  triggers:
    max_test_retry_loops: 3
    risk_escalation: true
    policy_violation: true
    budget_exceeded: true
    security_finding: true
    merge_conflict_unresolvable: true
  on_escalation: "stop_and_notify"
```

### 8.1 Automated Stop Triggers
Agents MUST immediately stop autonomous execution when:
1. **Loop Limit Reached (`max_test_retry_loops`):** Consecutive test-fix loops reach the configured threshold (default 3).
2. **Risk Escalation (`risk_escalation`):** The task requires higher risk permissions than `max_autonomous_risk_tier`.
3. **Policy Breach (`policy_violation`):** An action triggers a rule in `forbidden_actions` or attempts restricted filesystem/network operations.
4. **Budget Cap (`budget_exceeded`):** Token spend or runtime cost exceeds `cost_governance.max_budget_per_run_usd`.
5. **Security Finding (`security_finding`):** A SAST tool, secret scanner, or vulnerability check detects high/critical vulnerabilities.
6. **Merge Conflict (`merge_conflict_unresolvable`):** Git branch conflicts cannot be cleanly resolved autonomously.

---

## 9. Validation Rules Usable in CI

A compliant CI validation pipeline MUST verify both **syntactic schema conformance** and **semantic cross-field invariants**:

### 9.1 Syntactic Validation
- Document parses valid JSON or YAML without syntax errors.
- Document conforms strictly to JSON Schema [`framework/ai-sdlc.schema.json`](../ai-sdlc.schema.json).
- No undefined properties exist (`additionalProperties: false`).

### 9.2 Semantic Cross-Field Invariants
1. **Default Profile Consistency:** `verification.default_profile` MUST exist in `verification.profiles`.
2. **Autonomy vs Risk Tier Alignment:**
   - Level 0 (`L0`) $\implies$ `max_autonomous_risk_tier` MUST be `"R0"`.
   - Level 1 (`L1`) $\implies$ `max_autonomous_risk_tier` MUST be `"R0"` or `"R1"`.
   - Level 2 (`L2`) $\implies$ `max_autonomous_risk_tier` MUST be $\le$ `"R2"`.
   - Level 3 (`L3`) / Level 4 (`L4`) $\implies$ `max_autonomous_risk_tier` MAY be up to `"R3"`.
3. **Auto-Merge Risk Constraint:** `review.auto_merge.max_risk_tier` MUST NOT exceed `autonomy.max_autonomous_risk_tier`.
4. **Auto-Merge Check Requirement:** If `review.auto_merge.enabled: true`, `review.auto_merge.required_status_checks` MUST contain at least one check name.
5. **Escalation Contact Availability:** If any trigger in `escalation.triggers` is enabled, `escalation.contacts` MUST contain at least one contact with a valid `github_handle`, `email`, or `slack_channel`.
6. **Command Integrity:** All entries in `verification.profiles.<name>.commands` MUST be non-empty strings.
7. **Label Prefix Coherence:** For every label category with a `prefix`, all label `values[].name` entries MUST start with that prefix.

---

## 10. Summary & Adoption Matrix

| Dimension | Minimal Adoption | Full Enterprise Adoption |
|---|---|---|
| **File Location** | `.ai-sdlc.yaml` | `.ai-sdlc.yaml` |
| **Autonomy Level** | `2` (Autonomous PR) | `2` or `3` (Guarded Merge) |
| **Verification Profiles** | `fast`, `standard` | `fast`, `standard`, `strict`, `mutation` |
| **Review Policy** | 1 approval, CodeRabbit enabled | Role-based signoff matrix, auto-merge gates |
| **Labeling** | `risk:`, `type:` | `risk:`, `autonomy:`, `type:`, `stage:`, `status:` |
| **Escalation** | Lead developer GitHub handle | Multi-role directory with PagerDuty & Slack |
