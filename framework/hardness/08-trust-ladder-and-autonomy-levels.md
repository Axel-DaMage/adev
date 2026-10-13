# Trust Ladder and Autonomy Levels

The Trust Ladder is A-Dev's canonical model for incrementally granting and revoking agent autonomy. It replaces binary permissions ("all-or-nothing") with observable, metric-gated autonomy levels.

## Core doctrine

1. **Autonomy is earned, not assumed**: An agent starts at Level 0 (`shadow`) or Level 1 (`suggest`) and advances only through sustained empirical evidence over a declared evaluation window.
2. **Hard boundaries govern action**: Every level strictly maps to allowed action classes from the [Action Risk and Authority Model](04-action-risk-authority-model.md) and respects [policy precedence](01-policy-and-precedence.md).
3. **Automatic demotion on SLO breach**: Trust is revocable instantly upon a safety violation or systematically upon quality Service Level Objective (SLO) degradation.
4. **Configurable per repository**: Autonomy levels, thresholds, and boundary globs are declared explicitly in [`.ai-sdlc.yaml`](09-per-repo-configuration.md).

---

## Canonical Autonomy Levels

```
 Level 5: auto-deploy      ── Full Continuous Delivery & Release with Canary Rollback
       ▲
 Level 4: auto-merge-all   ── Autonomous Merge across Standard Code Paths
       ▲
 Level 3: auto-merge-low   ── Autonomous Merge for Low-Risk Changes (Docs, Chores)
       ▲
 Level 2: auto-PR          ── Autonomous Branch, Commit & PR Creation (Human Merges)
       ▲
 Level 1: suggest          ── Advisory / Review Comments / Draft Diffs (No Git Writes)
       ▲
 Level 0: shadow           ── Passive Observation & Internal Simulation (Recommend Only)
```

### Level 0: `shadow` (Recommend Only / Passive Observation)

- **Purpose**: Baseline evaluation of agent reasoning, skill selection, and policy adherence in a live repository without impacting files, branches, or team workflows.
- **Authority**: R0 only (read-only inspection and local simulation).
- **Mutating capabilities**: None. Zero branch creation, zero commits pushed, zero PRs opened, zero comments published.
- **Human role**: Full operational practitioner. The agent runs as a passive sidecar or background observer.
- **Exit gate**: Consistent evaluation accuracy (>= 90%) and zero unintended side-effect attempts over a minimum observation window.

### Level 1: `suggest` (Advisory / Review Suggestions / Draft Proposals)

- **Purpose**: Agent provides structured advisory feedback, code review comments, proposed diff snippets, or issue triage recommendations.
- **Authority**: R0 + read-only collaborative surfaces (pull request review comments, issue responses, local dry-run patch proposals).
- **Mutating capabilities**: Cannot create git branches, commit code, or open pull requests autonomously.
- **Human role**: Active decider and executor. The human reviews suggestions and applies or discards them manually.
- **Exit gate**: Suggestion acceptance rate (>= 80%) and zero critical diagnostic errors over at least 20 interactive suggestions.

### Level 2: `auto-PR` (Autonomous Branch, Commit & PR Creation)

- **Purpose**: Agent autonomously implements tasks in isolated worktrees, creates atomic commits, verifies changes locally against test harnesses, and opens pull requests with structured evidence.
- **Authority**: R1 (local workspace mutations, local test executions, atomic commits) + R3 (PR creation only).
- **Mutating capabilities**: Dedicated branch creation (`feat/*`, `fix/*`), commit creation, PR submission via GitHub CLI (`gh pr create`). Merging or deploying is strictly forbidden.
- **Human role**: Reviewer and approver. A human reviews the PR diff, inspects the attached evidence and [human expectations contract](03-human-expectations-contract.md), and performs the merge.
- **Exit gate**: Merge Success Rate (>= 90%) without major human rewrites, CI First-Pass Rate (>= 85%), and Revert Rate (0%) over at least 20 PRs.

### Level 3: `auto-merge-low` (Autonomous Merge for Low-Risk Changes)

- **Purpose**: Agent autonomously creates, validates, and merges low-risk pull requests (classified R0/R1 effects: documentation updates, formatting fixes, non-breaking dependency updates with green CI, localized tests, and designated chore tasks).
- **Authority**: R1 + R3 (PR creation and PR merge for declared low-risk path patterns).
- **Required automated gates**:
  - 100% passing CI suite (tests, linters, type checks).
  - Branch protection rules fully satisfied.
  - Zero blocking review comments (CodeRabbit, bot scanners, peer reviewers).
  - No modification to protected high-risk paths.
- **Escalation trigger**: Any PR modifying files outside the declared low-risk globs, failing a test, or triggering a policy warning immediately pauses and escalates to human review (falls back to Level 2 behavior for that task).
- **Human role**: Asynchronous auditor of low-risk merges; active reviewer for standard and high-risk PRs.
- **Exit gate**: Sustained 0% revert rate and >= 98% merge success rate on low-risk PRs over at least 50 pull requests.

### Level 4: `auto-merge-all` (Autonomous Merge across Standard Code Paths)

- **Purpose**: Agent autonomously merges qualifying PRs across standard application features, refactoring, and bug fixes once all deterministic gates, comprehensive test harnesses, security scanners, and hardness policies pass.
- **Authority**: R1 + R3 (PR creation and PR merge across all standard repository surfaces).
- **High-risk boundary**: Explicitly designated high-risk surfaces (e.g. `.github/workflows/**`, `auth/**`, `billing/**`, schema migrations, security policies) remain restricted by repository policy and require explicit human architect approval.
- **Required automated gates**:
  - Deterministic test harness passing (unit, integration, contract, mutation).
  - Static application security testing (SAST) and secret scanning passing.
  - Policy conformance validation passing.
- **Human role**: Strategic architect and systems reviewer. Inspects weekly quality density, audits metrics, and handles high-risk exception escalations.
- **Exit gate**: Merge Success Rate >= 99%, Revert Rate < 0.5%, Escalation Rate < 3% over at least 100 pull requests, with automated canary and rollback infrastructure verified.

### Level 5: `auto-deploy` (Continuous Delivery & Autonomous Release)

- **Purpose**: End-to-end continuous autonomous delivery: from task pickup and atomic implementation to PR creation, automated merge, and autonomous deployment to staging and production environments under continuous telemetry monitoring.
- **Authority**: Full SDLC lifecycle (R0, R1, R3 + deployment triggers and automated rollback execution).
- **Required automated gates**:
  - All Level 4 merge gates satisfied.
  - Staging smoke tests and integration tests passing.
  - Automated canary deployment verification with active telemetry (error budget, latency p99, error rate).
  - Automated zero-downtime rollback hook activated upon canary anomaly or health check failure.
- **Human role**: Strategic governance, SLO definition, and incident post-mortem review (if triggered).

---

## Autonomy Level Comparison Matrix

| Level | Name | Allowed Action Risk | Git Push / Branch | PR Creation | PR Merge Authority | Deployment Authority | Default Gatekeeper |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **L0** | `shadow` | R0 | ❌ No | ❌ No | ❌ No | ❌ No | Full Human Operation |
| **L1** | `suggest` | R0 | ❌ No | ❌ No | ❌ No | ❌ No | Human Decides & Executes |
| **L2** | `auto-PR` | R1, R3 (PR open) | ✅ Workspace branches | ✅ Yes | ❌ No | ❌ No | Human Reviews & Merges |
| **L3** | `auto-merge-low` | R1, R3 (low-risk merge) | ✅ Workspace branches | ✅ Yes | ✅ Low-risk paths only | ❌ No | Automated CI + Human for high-risk |
| **L4** | `auto-merge-all` | R1, R3 (all standard merge) | ✅ Workspace branches | ✅ Yes | ✅ Standard code paths | ❌ No | Automated CI/CD + Hardness Gates |
| **L5** | `auto-deploy` | R0–R3 + Deploy | ✅ Workspace branches | ✅ Yes | ✅ Full repo paths | ✅ Staging & Production | Automated Canary + Telemetry Monitor |

---

## Promotion Transition Criteria

Autonomy elevation is strictly sequential. An agent cannot skip levels (e.g. from Level 1 directly to Level 3).

| Transition | Minimum Sample Size | Observation Window | Required Metric Gates | Evidence Artifact |
| --- | --- | --- | --- | --- |
| **L0 → L1** | 30 simulated tasks | >= 7 days | Simulation Accuracy >= 90%<br>Side-effect violations = 0 | Shadow execution audit log |
| **L1 → L2** | 20 review suggestions | >= 7 days | Suggestion Acceptance Rate >= 80%<br>Critical diagnostic errors = 0 | PR review suggestion log |
| **L2 → L3** | 20 pull requests | >= 14 days | Merge Success Rate (MSR) >= 90%<br>CI First-Pass Rate (FPR) >= 85%<br>Revert Rate (RR) = 0%<br>Policy Conformance Rate (PCR) = 100% | PR history + test run telemetry |
| **L3 → L4** | 50 pull requests | >= 21 days | Low-risk Merge Success Rate >= 98%<br>Revert Rate (RR) < 1.0%<br>Escalation Rate (ER) < 5.0%<br>Zero unauthorized path modifications | Automated merge log + Git revert log |
| **L4 → L5** | 100 pull requests | >= 30 days | Standard Merge Success Rate >= 99%<br>Revert Rate (RR) < 0.5%<br>Escalation Rate (ER) < 2.0%<br>Verified automated canary & rollback hooks | Deployment logs + APM telemetry record |

---

## Demotion Triggers and Automatic Demotion

Demotion is the immediate or rolling reduction of an agent's trust level when observed signals violate safety invariants or breach defined Service Level Objectives (SLOs).

```
   Normal State ───────► SLO Breach / Safety Violation ───────► Automatic Demotion
        ▲                                                               │
        │                                                               ▼
   Re-promotion ◄────── Cooldown + RCA + Clean Runs ◄──────── Reduced Level
```

### 1. Instant Hard Demotions (Safety Breaches)

An instant demotion executes immediately, freezes pending automated actions, and demotes the repository or agent trust level to **Level 0** or **Level 1**:

- **Unauthorized High-Risk Mutation**: Attempting an R2 or R3 action without explicit authorization or on a protected path.
- **Security Rule Violation**: Attempting to use `--admin` to bypass branch protection, disable security scanners, or expose credentials/tokens.
- **Policy Invariant Breach**: Modifying files declared immutable or bypassing mandatory verification gates.
- **Circuit Breaker Halt**: 3 consecutive unexpected runtime crashes or infinite loop detections.

### 2. Rolling SLO Demotions (Quality Degradation)

When metrics calculated over the sliding evaluation window breach the demotion threshold, the system automatically demotes the trust level by one or more steps:

| Current Level | Demotion Trigger / SLO Breach | Demoted Level | System Action |
| --- | --- | --- | --- |
| **Level 5** (`auto-deploy`) | Production incident, failed canary without rollback, or Revert Rate > 1.0% | **Level 2** (`auto-PR`) | Deploy permissions revoked; merges disabled; requires human triage. |
| **Level 4** (`auto-merge-all`) | Revert Rate > 2.0%, CI First-Pass Rate < 80%, or 2 consecutive merge failures | **Level 3** (`auto-merge-low`) | Standard code auto-merge disabled; only low-risk paths allowed. |
| **Level 3** (`auto-merge-low`) | Any revert on low-risk auto-merged PRs (RR > 0%), or Escalation Rate > 10% | **Level 2** (`auto-PR`) | All auto-merging disabled; all PRs require human review and merge. |
| **Level 2** (`auto-PR`) | Merge Success Rate < 70%, or CI First-Pass Rate < 60% over 10 PRs | **Level 1** (`suggest`) | PR creation disabled; restricted to draft suggestions. |
| **Level 1** (`suggest`) | Diagnostic error rate > 40%, or repeated hallucinated suggestions | **Level 0** (`shadow`) | Interactive suggestions disabled; relegated to passive audit. |

### 3. Rehabilitation and Recovery Protocol

After demotion, trust is never restored automatically. The following steps are required before re-evaluation for promotion:

1. **Root Cause Analysis (RCA)**: A documented incident record detailing why the failure occurred, what policy or test was missing, and what corrective guardrail was added.
2. **Mandatory Cooldown Period**: Minimum 7 calendar days at the reduced autonomy level.
3. **Required Clean Runs**: Minimum 10 consecutive defect-free PRs/runs at the reduced level with 100% CI pass and 0% reverts.
4. **Architect Sign-Off**: Explicit human approval recorded in the repository decision log before restoring the previous trust level.

---

## Observable Signals and Metrics Mapping

Every gating metric must map to a deterministic, queryable data source. The following table specifies the canonical metrics, formulas, and observable signals:

| Metric Name | Identifier | Mathematical Formula | Observable Data Source / Signal | Promotion Threshold | Demotion SLO Threshold | Window |
| --- | --- | --- | --- | --- | --- | --- |
| **Merge Success Rate** | `MSR` | `(PRs_merged_without_rework / PRs_created) * 100%` | GitHub CLI (`gh pr list --json state,reviews,comments`), review iteration count | >= 90% (L2→L3)<br>>= 98% (L3→L4)<br>>= 99% (L4→L5) | < 70% (L2)<br>< 90% (L3)<br>< 95% (L4) | Rolling 20–100 PRs |
| **Revert Rate** | `RR` | `(Merged_PRs_reverted_or_hotfixed / Total_merged_PRs) * 100%` | Git history (`git log --grep="^Revert"`), rollback commits, incident tags | 0.0% (L2→L3)<br>< 1.0% (L3→L4)<br>< 0.5% (L4→L5) | > 0.0% (L3)<br>> 2.0% (L4)<br>> 1.0% (L5) | Rolling 30 days |
| **Escalation Rate** | `ER` | `(Runs_requiring_human_takeover / Total_runs) * 100%` | Agent execution logs, unhandled error traps, policy escalation events | < 5.0% (L3→L4)<br>< 2.0% (L4→L5) | > 10.0% (L3)<br>> 5.0% (L4)<br>> 3.0% (L5) | Rolling 20 runs |
| **CI First-Pass Rate** | `FPR` | `(PRs_passing_CI_on_run_1 / Total_PRs_created) * 100%` | CI status check rollup (`gh pr view --json statusCheckRollup`), GitHub Actions API | >= 85% (L2→L3)<br>>= 95% (L3→L4)<br>>= 98% (L4→L5) | < 60% (L2)<br>< 80% (L3/L4) | Rolling 20 PRs |
| **Policy Conformance Rate** | `PCR` | `(Runs_with_zero_policy_violations / Total_runs) * 100%` | Hardness evaluation log, branch protection rejection events | 100.0% (all levels) | < 100.0% (Instant demotion) | Continuous (1 error triggers) |
| **Canary Health Rate** | `CHR` | `(Deployments_passed_canary / Total_deployments) * 100%` | APM metrics, canary evaluator telemetry, synthetic monitor status | >= 99.5% (L4→L5) | < 99.0% (L5) | Rolling 30 days |
| **Mean Time to Rollback** | `MTTR` | `Sum(T_restore - T_anomaly) / Total_rollbacks` | Deployment pipeline event timestamps, incident resolution logs | <= 5 minutes (L5 promotion) | > 10 minutes (L5 SLO breach) | Per event |

---

## Summary of Guarantees

The Trust Ladder ensures that:
- No agent operates with unverified authority.
- Every privilege escalation is backed by empirical performance data.
- Safety failures result in immediate, deterministic demotion.
- All boundaries, thresholds, and levels are declared in code via `.ai-sdlc.yaml`.
