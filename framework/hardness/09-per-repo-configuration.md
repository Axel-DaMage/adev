# Per-Repository Hardness Configuration (`.ai-sdlc.yaml`)

This specification defines the schema, structure, and usage of `.ai-sdlc.yaml`, the per-repository configuration file that declares an agent's active trust level, boundary paths, promotion criteria, and automatic demotion triggers.

## Purpose

1. **Version-controlled autonomy**: Repository autonomy is committed to git in `.ai-sdlc.yaml`, making permissions transparent, reviewable, and auditable.
2. **Explicit risk boundaries**: Defines which file paths are low-risk (eligible for autonomous merge at Level 3) versus high-risk (strictly requiring human sign-off).
3. **Deterministic SLO enforcement**: Codifies the numeric promotion gates, demotion thresholds, and recovery protocols from the [Trust Ladder](08-trust-ladder-and-autonomy-levels.md).

---

## Canonical File Location

The canonical configuration file MUST be located at the root of the repository:

```
<repo-root>/.ai-sdlc.yaml
```

(Alternatively, `.ai-sdlc.json` is supported for strict JSON toolchains.)

---

## Configuration Schema Reference

The configuration format is governed by the JSON Schema contract [`ai-sdlc-schema.json`](ai-sdlc-schema.json).

### Key Configuration Sections

| Section | Required | Description |
| --- | --- | --- |
| `version` | Yes | Specification version (e.g. `"1.0.0"`). |
| `trust_ladder` | Yes | Active autonomy level, target promotion level, evaluation windows, promotion gates, demotion SLOs, and rehabilitation rules. |
| `risk_boundaries` | Yes | Glob patterns for low-risk paths (eligible for Level 3 auto-merge), high-risk paths (mandatory human review), and protected branches. |
| `automated_merge_rules` | Yes | Pre-merge verification constraints (CI status, review clearance, merge method). |
| `deployment` | No | Continuous delivery settings, canary verification duration, and automated rollback triggers for Level 5. |
| `audit_and_observability` | Yes | Telemetry mode, evidence retention strategy, and decision logging settings. |

---

## Annotated Starter Configuration

Below is a complete example of a production-ready `.ai-sdlc.yaml` configured at **Level 2 (`auto-PR`)** working toward **Level 3 (`auto-merge-low`)**:

```yaml
version: "1.0.0"
repository: "Axel-DaMage/adev"

trust_ladder:
  # Active operational level: shadow | suggest | auto-PR | auto-merge-low | auto-merge-all | auto-deploy
  current_level: "auto-PR"
  target_level: "auto-merge-low"

  evaluation_window:
    min_pull_requests: 20
    min_days: 14

  promotion_gates:
    min_merge_success_rate: 0.90      # 90% of PRs merged without human rework
    max_revert_rate: 0.00             # 0% reverts allowed during evaluation
    max_escalation_rate: 0.05         # <= 5% unhandled escalations
    min_ci_first_pass_rate: 0.85      # >= 85% passing CI on first attempt
    min_policy_conformance_rate: 1.00 # 100% policy compliance

  demotion_triggers:
    max_revert_rate_slo: 0.02         # Demote if revert rate exceeds 2%
    max_consecutive_failures: 2       # Demote on 2 consecutive broken builds/merges
    max_escalation_rate_slo: 0.10     # Demote if escalation exceeds 10%
    instant_demotion_on_security_breach: true
    demote_to_level: "suggest"

  rehabilitation:
    cooldown_days: 7
    required_clean_runs: 10
    requires_human_signoff: true

risk_boundaries:
  # Paths eligible for autonomous merge at Level 3 (auto-merge-low)
  low_risk_paths:
    - "docs/**"
    - "*.md"
    - "starter-kit/**"
    - "publishing-kit/**"
    - "framework/fixtures/**"
    - "tests/fixtures/**"

  # Paths strictly requiring human sign-off regardless of level (unless L5 auto-deploy)
  high_risk_paths:
    - ".github/workflows/**"
    - "security/**"
    - "auth/**"
    - "billing/**"
    - "migrations/**"
    - "framework/hardness/policy-schema.json"
    - "framework/hardness/ai-sdlc-schema.json"

  protected_branches:
    - "main"
    - "release/*"

automated_merge_rules:
  require_all_ci_passing: true
  require_zero_blocking_reviews: true
  require_no_unresolved_comments: true
  allowed_merge_methods:
    - "squash"
    - "merge"
  delete_branch_after_merge: true

deployment:
  enabled: false
  target_environments:
    - "staging"
  canary_verification_duration_minutes: 15
  auto_rollback_on_health_failure: true

audit_and_observability:
  log_decisions: true
  evidence_retention: "repository-record"
  metrics_collection: "git-native"
```

---

## Configuration Profiles by Level

### Profile 1: Level 0 (`shadow`) / Level 1 (`suggest`)
```yaml
trust_ladder:
  current_level: "suggest"
  target_level: "auto-PR"
  evaluation_window:
    min_pull_requests: 20
    min_days: 7
  promotion_gates:
    min_merge_success_rate: 0.80
    max_revert_rate: 0.00
    max_escalation_rate: 0.10
    min_ci_first_pass_rate: 0.80
    min_policy_conformance_rate: 1.00
  demotion_triggers:
    instant_demotion_on_security_breach: true
    demote_to_level: "shadow"
```

### Profile 2: Level 4 (`auto-merge-all`)
```yaml
trust_ladder:
  current_level: "auto-merge-all"
  target_level: "auto-deploy"
  evaluation_window:
    min_pull_requests: 100
    min_days: 30
  promotion_gates:
    min_merge_success_rate: 0.99
    max_revert_rate: 0.005
    max_escalation_rate: 0.02
    min_ci_first_pass_rate: 0.98
    min_policy_conformance_rate: 1.00
  demotion_triggers:
    max_revert_rate_slo: 0.01
    max_consecutive_failures: 2
    max_escalation_rate_slo: 0.05
    instant_demotion_on_security_breach: true
    demote_to_level: "auto-merge-low"
```

---

## Local Schema Validation

Validate `.ai-sdlc.yaml` or `.ai-sdlc.json` against `ai-sdlc-schema.json`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ./framework/hardness/scripts/validate-ai-sdlc-fixtures.ps1
```

Or run the cross-platform python validator:

```bash
python3 ./framework/hardness/scripts/validate-hardness.py
```
