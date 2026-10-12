# Organization-Wide Policy Model: Baseline .ai-sdlc.yaml with Inheritance and Overrides

## Purpose and Scope

This normative specification defines the resolution algorithm, inheritance semantics, field-level merge operations, and non-overridable floor constraints for organization-wide `.ai-sdlc.yaml` policy documents in fleet operations.

When operating AI coding agents across multi-repository organizations, governance cannot rely on standalone, disconnected repository configurations. Central platform and security teams require durable organizational baselines that individual repositories inherit by default and can selectively specialize—without allowing any repository to weaken safety floors, evade security gates, or elevate agent authority beyond organizational boundaries.

This specification provides a deterministic, runtime-neutral resolution model implementable by any consumer (e.g., CI/CD pipelines, agent orchestration runtimes, policy engines, and pre-commit hooks).

---

## Architecture and Policy Hierarchy

Fleet-wide policy resolution operates on a multi-tier hierarchy:

```
┌─────────────────────────────────────────────────────────┐
│ Level 1: Platform & Hardness Canon Invariants           │ (Inviolable platform rules)
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│ Level 2: Organization Baseline Policy                   │ (.ai-sdlc.yaml at org root / catalog)
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│ Level 3: Domain / Business Unit Overlay (Optional)      │ (.ai-sdlc.yaml at group/team level)
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│ Level 4: Repository Policy Configuration                │ (.ai-sdlc.yaml in repo root)
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│ Level 5: Ephemeral Task / Session Overlays              │ (Runtime prompt & task boundaries)
└─────────────────────────────────────────────────────────┘
```

### Precedence and Inheritance Direction

1. **Top-Down Inheritance**: Base configuration defaults flow down from the Organization Baseline (Level 2) to Repository Policies (Level 4).
2. **Selective Override**: Repositories declare only delta specializations. Omitted fields automatically inherit their values from the upstream baseline.
3. **Monotonic Constraint Enforcement**: Downstream overlays may tighten restrictions, add required checks, narrow permissions, or lower risk tolerances. Downstream overlays **cannot** relax non-overridable security floors, remove mandatory checks, or exceed organizational authority ceilings.

---

## Document Structure (`.ai-sdlc.yaml`)

Every `.ai-sdlc.yaml` document conforms to the canonical JSON Schema defined in [`ai-sdlc-schema.json`](ai-sdlc-schema.json). The document contains five primary sections:

1. `schema_version`: Semantic version of the `.ai-sdlc.yaml` specification format (e.g., `"1.0.0"`).
2. `metadata`: Identification, scope (`organization` or `repository`), version, owner, and description.
3. `extends`: Inheritance directive specifying parent baseline URI/reference and resolution mode (`fail_closed` or `clamp_and_warn`).
4. `security_gates`: Non-bypassable safety mechanisms, vulnerability thresholds, branch protections, protected paths, and sandbox isolation requirements.
5. `agent_authority`: Bounded autonomous actions, maximum allowed risk tiers, allowlisted/denylisted tools, and network domain restrictions.
6. `quality_floors`: Test enforcement gates, verification proof requirements, and atomic iteration size limits.
7. `review_and_audit`: Review workflow enforcement, structured logging, telemetry retention, and digital thread tracking.

---

## Field-Level Merge Taxonomy and Operators

During policy resolution, every field in `.ai-sdlc.yaml` is resolved using one of seven formal merge operators.

| Merge Operator | Mathematical Definition | Applicable Types | Semantic Behavior |
| --- | --- | --- | --- |
| `REPLACE_IF_PERMITTED` | $R = V_{repo}$ if $V_{repo} \in Domain$, else $V_{org}$ | Scalars (strings, identifiers) | Repo value replaces Org baseline value if permitted by schema and domain rules. |
| `MONOTONIC_FLOOR` | $R = \max(V_{org}, V_{repo})$ where higher is stricter | Ordinal / Numeric (coverage %, review count, severity) | Repo can only increase or match strictness; attempting to decrease is an illegal override violation. |
| `MONOTONIC_CEILING` | $R = \min(V_{org}, V_{repo})$ where lower is stricter | Ordinal / Numeric (risk level tier, diff line limit, files limit) | Repo can only decrease or match maximum allowed bounds; attempting to elevate is an illegal override violation. |
| `BOOLEAN_FLOOR_TRUE` | If $V_{org} == \text{true}$, then $R = \text{true}$; $V_{repo} = \text{false} \implies \text{VIOLATION}$ | Boolean flags | Security flags set to `true` at Org level cannot be set to `false` by any downstream repository. |
| `SET_UNION` | $R = V_{org} \cup V_{repo}$ | Lists of strings / patterns | Additive denylists and required sets. Repo can add additional restrictions or required checks, but cannot remove Org-mandated items. |
| `SET_INTERSECT` | $R = V_{org} \cap V_{repo}$ | Lists of strings / patterns | Restrictive allowlists. Repo can only permit a subset of what the Org allows; cannot introduce tools or endpoints not in Org allowlist. |
| `DEEP_MERGE_KEYED` | $R[k] = \text{Resolve}(V_{org}[k], V_{repo}[k])$ | Keyed Maps / Dictionaries | Recursive descent down the object graph applying leaf field merge operators. |

---

## Enumeration of Non-Overridable Floor Fields

The following fields represent organizational safety floors. Any attempt by a repository policy to weaken, disable, or bypass these fields constitutes an `ERR_AI_SDLC_FLOOR_VIOLATION` or `ERR_AI_SDLC_CEILING_VIOLATION`.

### 1. Security Gates

| Field Path | Merge Operator | Floor Constraint / Behavior | Rationale |
| --- | --- | --- | --- |
| `security_gates.secrets_scanning.enabled` | `BOOLEAN_FLOOR_TRUE` | Cannot be overridden to `false` if `true` in Org baseline. | Prevents credential and secret leaks into repositories across the fleet. |
| `security_gates.secrets_scanning.block_on_detect` | `BOOLEAN_FLOOR_TRUE` | Cannot be overridden to `false` if `true` in Org baseline. | Ensures CI/CD and commit blocks immediately halt execution on detected secrets. |
| `security_gates.vulnerability_threshold.max_allowed_severity` | `MONOTONIC_FLOOR` | Repo severity threshold cannot be weaker than Org baseline (`none` < `low` < `medium` < `high` < `critical`). | Prevents repositories from ignoring high-severity vulnerabilities flagged org-wide. |
| `security_gates.vulnerability_threshold.block_pr_on_floor` | `BOOLEAN_FLOOR_TRUE` | Cannot be overridden to `false` if `true` in Org baseline. | Ensures pull request checks block merging on policy-violating vulnerabilities. |
| `security_gates.admin_bypass_forbidden` | `BOOLEAN_FLOOR_TRUE` | Non-overridable immutable floor (`true`). | Forbids autonomous agents from utilizing `--admin` or administrator bypass privileges. |
| `security_gates.branch_protection.require_reviews_min` | `MONOTONIC_FLOOR` | Repo review count cannot be lower than Org floor ($V_{repo} \ge V_{org}$). | Guarantees minimum peer and human review threshold across all repositories. |
| `security_gates.branch_protection.block_force_push` | `BOOLEAN_FLOOR_TRUE` | Cannot be overridden to `false` if `true` in Org baseline. | Preserves git history and prevents rewriting of audited commits. |
| `security_gates.protected_paths` | `SET_UNION` | Org protected paths are strictly additive; repo cannot unprotect Org paths. | Protects CI workflows, security policies, and `.ai-sdlc.yaml` from autonomous tampering. |
| `security_gates.sandbox_isolation.required` | `BOOLEAN_FLOOR_TRUE` | Cannot be overridden to `false` if `true` in Org baseline. | Requires agent tool execution to occur in isolated container/sandbox environments. |
| `security_gates.sandbox_isolation.min_isolation_level` | `MONOTONIC_FLOOR` | Ordinal: `process` < `container` < `vm`. Repo cannot lower isolation level. | Prevents uncontained arbitrary code execution on shared build runners. |

### 2. Agent Authority and Risk Ceilings

| Field Path | Merge Operator | Ceiling / Floor Constraint | Rationale |
| --- | --- | --- | --- |
| `agent_authority.max_autonomous_risk_level` | `MONOTONIC_CEILING` | Ordinal: `read_only` (1) < `low_risk_write` (2) < `medium_risk_write` (3) < `high_risk_write` (4) < `unrestricted` (5). Repo cannot exceed Org ceiling. | Restricts agent action space to organizational risk tolerance. |
| `agent_authority.require_human_approval_for_risk_ge` | `MONOTONIC_FLOOR` | Repo threshold for requiring human approval cannot be higher (looser) than Org floor. | Guarantees human-in-the-loop gates for high-risk actions. |
| `agent_authority.forbidden_tools` | `SET_UNION` | Org forbidden tools are permanently blocked; repo cannot remove tools from this denylist. | Disallows dangerous system utilities, raw sockets, or policy evasion tools. |
| `agent_authority.allowed_tools` | `SET_INTERSECT` | Repo can only permit a subset of Org-approved tools ($V_{repo} \subseteq V_{org}$). | Prevents repositories from granting access to unauthorized capabilities. |
| `agent_authority.network_access.forbidden_domains` | `SET_UNION` | Org forbidden domains cannot be unblocked by any repository policy. | Prevents data exfiltration and untrusted egress destinations. |
| `agent_authority.network_access.allowed_domains` | `SET_INTERSECT` | Repo can only permit egress to a subset of Org-approved domains. | Constrains agent network connectivity to audited endpoints. |

### 3. Quality and Verification Floors

| Field Path | Merge Operator | Floor Constraint / Behavior | Rationale |
| --- | --- | --- | --- |
| `quality_floors.test_enforcement.require_tests_for_new_features` | `BOOLEAN_FLOOR_TRUE` | Cannot be overridden to `false` if `true` in Org baseline. | Ensures new code changes are accompanied by automated verification tests. |
| `quality_floors.test_enforcement.min_coverage_percent` | `MONOTONIC_FLOOR` | Repo coverage threshold cannot be set lower than Org baseline. | Upholds code quality and test coverage floors across the fleet. |
| `quality_floors.verification.require_clean_reproduction` | `BOOLEAN_FLOOR_TRUE` | Cannot be overridden to `false` if `true` in Org baseline. | Requires agents to verify issues through clean, reproducible execution. |
| `quality_floors.verification.reproduction_command_required` | `BOOLEAN_FLOOR_TRUE` | Cannot be overridden to `false` if `true` in Org baseline. | Enforces that verification evidence includes explicit executable commands. |
| `quality_floors.atomic_iterations.max_diff_lines_per_iteration` | `MONOTONIC_CEILING` | Repo maximum diff size cannot exceed Org ceiling ($V_{repo} \le V_{org}$). | Keeps agent iterations small, reviewable, and atomic. |
| `quality_floors.atomic_iterations.max_files_per_iteration` | `MONOTONIC_CEILING` | Repo maximum files touched cannot exceed Org ceiling ($V_{repo} \le V_{org}$). | Limits blast radius of single agent iterations. |

### 4. Review and Audit Floors

| Field Path | Merge Operator | Floor Constraint / Behavior | Rationale |
| --- | --- | --- | --- |
| `review_and_audit.pr_review_workflow.enforce_5_step_review` | `BOOLEAN_FLOOR_TRUE` | Cannot be overridden to `false` if `true` in Org baseline. | Mandates the 5-step PR review workflow before any PR merge. |
| `review_and_audit.pr_review_workflow.require_impact_analysis` | `BOOLEAN_FLOOR_TRUE` | Cannot be overridden to `false` if `true` in Org baseline. | Requires explicit impact analysis for every code change. |
| `review_and_audit.audit.structured_logging_enabled` | `BOOLEAN_FLOOR_TRUE` | Cannot be overridden to `false` if `true` in Org baseline. | Mandates structured event recording for digital thread traceability. |
| `review_and_audit.audit.retention_min_days` | `MONOTONIC_FLOOR` | Repo audit retention cannot be lower than Org baseline. | Ensures compliance logs meet organizational retention mandates. |
| `review_and_audit.audit.record_prompts_and_tool_calls` | `BOOLEAN_FLOOR_TRUE` | Cannot be overridden to `false` if `true` in Org baseline. | Preserves full agent interaction audit trail for post-incident review. |

---

## Normative Resolution Algorithm

Any policy consumer (CLI tool, CI runner, agent orchestrator, or gatekeeper daemon) MUST implement the resolution algorithm in accordance with the following normative specification.

### Algorithm Inputs and Options

- `OrgBaselineDoc`: Parsed organizational baseline document.
- `RepoOverrideDoc`: Parsed repository override document (optional; may be empty or omitted).
- `Options`:
  - `mode`: Resolution enforcement mode:
    - `FAIL_CLOSED` (Default): Terminate resolution with a fatal exit error upon detecting any floor/ceiling violation.
    - `CLAMP_AND_WARN`: Enforce the organizational floor by clamping the violating value back to the baseline value, logging an explicit violation warning in the audit manifest.
  - `strict_schema`: Boolean indicating whether unknown root fields trigger rejection.

### Resolution Steps

```
Algorithm: ResolvePolicy(OrgBaselineDoc, RepoOverrideDoc, Options)
------------------------------------------------------------------
Input:  OrgBaselineDoc (Object), RepoOverrideDoc (Object or Null), Options (Object)
Output: ResolutionManifest containing ResolvedPolicy, ProvenanceMap, and Violations

Step 1: Schema Validation
    Validate OrgBaselineDoc against ai-sdlc-schema.json.
    If OrgBaselineDoc is invalid:
        Throw ERR_AI_SDLC_INVALID_SCHEMA with validation errors.

    If RepoOverrideDoc is not Null:
        Validate RepoOverrideDoc against ai-sdlc-schema.json.
        If RepoOverrideDoc is invalid:
            Throw ERR_AI_SDLC_INVALID_SCHEMA with validation errors.

Step 2: Initialization
    ResolvedPolicy ← DeepClone(OrgBaselineDoc)
    ProvenanceMap  ← New KeyValueMap()
    ViolationsList  ← New List()

    For each leaf path P in OrgBaselineDoc:
        ProvenanceMap[P] ← {
            source: "org_baseline",
            baseline_value: OrgBaselineDoc[P],
            override_value: Null,
            resolved_value: OrgBaselineDoc[P],
            operator: LookupOperator(P),
            status: "inherited"
        }

    If RepoOverrideDoc is Null:
        Return AssembleManifest(ResolvedPolicy, ProvenanceMap, ViolationsList)

Step 3: Mode and Hierarchy Determination
    ResolutionMode ← Options.mode OR RepoOverrideDoc.extends.mode OR "fail_closed"

Step 4: Recursive Field-Level Merge
    For each field path P present in RepoOverrideDoc:
        OrgValue  ← LookupPath(OrgBaselineDoc, P)
        RepoValue ← LookupPath(RepoOverrideDoc, P)
        Operator  ← LookupOperator(P)

        Case Operator of:

        1. REPLACE_IF_PERMITTED:
            ResolvedPolicy[P] ← RepoValue
            ProvenanceMap[P] ← {
                source: "repo_override",
                baseline_value: OrgValue,
                override_value: RepoValue,
                resolved_value: RepoValue,
                operator: Operator,
                status: "overridden"
            }

        2. BOOLEAN_FLOOR_TRUE:
            If OrgValue == true And RepoValue == false:
                Violation ← CreateViolation(
                    code: "ERR_AI_SDLC_FLOOR_VIOLATION",
                    path: P,
                    baseline_value: true,
                    attempted_value: false,
                    reason: "Cannot disable mandatory security floor flag"
                )
                ViolationsList.Add(Violation)
                If ResolutionMode == "FAIL_CLOSED":
                    Throw Violation
                Else:
                    ResolvedPolicy[P] ← true
                    ProvenanceMap[P].status ← "clamped_to_floor"
                    ProvenanceMap[P].resolved_value ← true
            Else:
                ResolvedPolicy[P] ← RepoValue
                ProvenanceMap[P].status ← (OrgValue == RepoValue) ? "inherited" : "overridden"
                ProvenanceMap[P].resolved_value ← RepoValue

        3. MONOTONIC_FLOOR:
            // Compare strictness: StrictnessIndex(RepoValue) vs StrictnessIndex(OrgValue)
            If StrictnessIndex(RepoValue) < StrictnessIndex(OrgValue):
                Violation ← CreateViolation(
                    code: "ERR_AI_SDLC_FLOOR_VIOLATION",
                    path: P,
                    baseline_value: OrgValue,
                    attempted_value: RepoValue,
                    reason: "Repository override is weaker than organizational minimum floor"
                )
                ViolationsList.Add(Violation)
                If ResolutionMode == "FAIL_CLOSED":
                    Throw Violation
                Else:
                    ResolvedPolicy[P] ← OrgValue
                    ProvenanceMap[P].status ← "clamped_to_floor"
                    ProvenanceMap[P].resolved_value ← OrgValue
            Else:
                ResolvedPolicy[P] ← RepoValue
                ProvenanceMap[P].status ← "tightened_floor"
                ProvenanceMap[P].resolved_value ← RepoValue

        4. MONOTONIC_CEILING:
            // Compare limits: LimitIndex(RepoValue) vs LimitIndex(OrgValue)
            If LimitIndex(RepoValue) > LimitIndex(OrgValue):
                Violation ← CreateViolation(
                    code: "ERR_AI_SDLC_CEILING_VIOLATION",
                    path: P,
                    baseline_value: OrgValue,
                    attempted_value: RepoValue,
                    reason: "Repository override exceeds organizational maximum ceiling"
                )
                ViolationsList.Add(Violation)
                If ResolutionMode == "FAIL_CLOSED":
                    Throw Violation
                Else:
                    ResolvedPolicy[P] ← OrgValue
                    ProvenanceMap[P].status ← "clamped_to_ceiling"
                    ProvenanceMap[P].resolved_value ← OrgValue
            Else:
                ResolvedPolicy[P] ← RepoValue
                ProvenanceMap[P].status ← "tightened_ceiling"
                ProvenanceMap[P].resolved_value ← RepoValue

        5. SET_UNION (Additive Denylists & Protected Sets):
            ResolvedSet ← DistinctUnion(OrgValue, RepoValue)
            ResolvedPolicy[P] ← ResolvedSet
            ProvenanceMap[P] ← {
                source: "merged",
                baseline_value: OrgValue,
                override_value: RepoValue,
                resolved_value: ResolvedSet,
                operator: Operator,
                status: "additive_union"
            }

        6. SET_INTERSECT (Restrictive Allowlists):
            If OrgValue is Null or Empty:
                ResolvedSet ← RepoValue
            Else:
                ResolvedSet ← DistinctIntersect(OrgValue, RepoValue)
            ResolvedPolicy[P] ← ResolvedSet
            ProvenanceMap[P] ← {
                source: "merged",
                baseline_value: OrgValue,
                override_value: RepoValue,
                resolved_value: ResolvedSet,
                operator: Operator,
                status: "restrictive_intersect"
            }

        7. DEEP_MERGE_KEYED:
            Recurse down sub-tree for child keys.

Step 5: Post-Resolution Invariants Check
    Assert(ResolvedPolicy.security_gates.secrets_scanning.enabled == true)
    Assert(ResolvedPolicy.security_gates.admin_bypass_forbidden == true)
    Assert(ResolvedPolicy.security_gates.protected_paths contains ".ai-sdlc.yaml")

Step 6: Manifest Assembly
    Metadata ← {
        org_baseline_version: OrgBaselineDoc.metadata.version,
        repo_policy_version: RepoOverrideDoc.metadata.version OR "none",
        resolved_at: CurrentIsoUtcTimestamp(),
        mode: ResolutionMode,
        resolution_hash: Sha256(JsonCanonicalString(ResolvedPolicy)),
        violations_count: ViolationsList.Length
    }

    Return ResolutionManifest {
        resolved_policy: ResolvedPolicy,
        metadata: Metadata,
        provenance: ProvenanceMap,
        violations: ViolationsList
    }
```

---

## Error Codes and Diagnostic Format

When an illegal override is attempted, resolution tools MUST emit structured diagnostics using the standardized error codes:

| Error Code | Meaning | Example Scenario |
| --- | --- | --- |
| `ERR_AI_SDLC_INVALID_SCHEMA` | Structural or type error in YAML/JSON document | Missing required `schema_version` or invalid type for `min_coverage_percent`. |
| `ERR_AI_SDLC_FLOOR_VIOLATION` | Attempt to weaken a mandatory security floor or threshold | Setting `secrets_scanning.enabled: false` or `require_reviews_min: 0` when Org floor is `1`. |
| `ERR_AI_SDLC_CEILING_VIOLATION` | Attempt to elevate agent authority or size limit above ceiling | Setting `max_autonomous_risk_level: high_risk_write` when Org ceiling is `low_risk_write`. |
| `ERR_AI_SDLC_IMMUTABLE_OVERRIDE` | Attempt to override a locked or immutable organizational field | Overriding `admin_bypass_forbidden: false`. |
| `ERR_AI_SDLC_CIRCULAR_INHERITANCE` | Cycle detected in multi-tier policy inheritance graph | Policy A extends Policy B which extends Policy A. |

### Diagnostic Output Example

```json
{
  "error": "ERR_AI_SDLC_FLOOR_VIOLATION",
  "field": "security_gates.secrets_scanning.enabled",
  "baseline_value": true,
  "attempted_value": false,
  "operator": "BOOLEAN_FLOOR_TRUE",
  "mode": "fail_closed",
  "message": "Illegal override at 'security_gates.secrets_scanning.enabled': cannot disable mandatory organizational security floor."
}
```

---

## Provenance and Digital Thread Record

To guarantee end-to-end traceability (digital thread), every resolved policy output MUST include a provenance attribution record showing the lineage of each resolved parameter:

```json
{
  "provenance": {
    "security_gates.secrets_scanning.enabled": {
      "source": "org_baseline",
      "baseline_value": true,
      "override_value": null,
      "resolved_value": true,
      "status": "inherited"
    },
    "security_gates.protected_paths": {
      "source": "merged",
      "baseline_value": [".github/workflows/**", "SECURITY.md", ".ai-sdlc.yaml"],
      "override_value": ["src/legacy-core/**"],
      "resolved_value": [".github/workflows/**", "SECURITY.md", ".ai-sdlc.yaml", "src/legacy-core/**"],
      "status": "additive_union"
    },
    "quality_floors.test_enforcement.min_coverage_percent": {
      "source": "repo_override",
      "baseline_value": 80,
      "override_value": 90,
      "resolved_value": 90,
      "status": "tightened_floor"
    }
  }
}
```

---

## Reference Implementation and Fixtures

- **JSON Schema**: [`ai-sdlc-schema.json`](ai-sdlc-schema.json) validates the structural integrity of both baseline and override documents.
- **Fixtures**:
  - Valid Org Baseline: [`fixtures/ai-sdlc/org-baseline.yaml`](fixtures/ai-sdlc/org-baseline.yaml) (and [`.json`](fixtures/ai-sdlc/org-baseline.json))
  - Valid Repository Override: [`fixtures/ai-sdlc/repo-override-valid.yaml`](fixtures/ai-sdlc/repo-override-valid.yaml) (and [`.json`](fixtures/ai-sdlc/repo-override-valid.json))
  - Invalid Floor Violation Override: [`fixtures/ai-sdlc/repo-override-floor-violation.yaml`](fixtures/ai-sdlc/repo-override-floor-violation.yaml) (and [`.json`](fixtures/ai-sdlc/repo-override-floor-violation.json))
  - Expected Resolved Policy: [`fixtures/ai-sdlc/resolved-policy-expected.yaml`](fixtures/ai-sdlc/resolved-policy-expected.yaml) (and [`.json`](fixtures/ai-sdlc/resolved-policy-expected.json))
- **Executable Resolver**: [`scripts/resolve_ai_sdlc.py`](scripts/resolve_ai_sdlc.py) implements the normative algorithm in portable Python with zero external dependencies.
- **Automated Verification Suite**: [`scripts/test_ai_sdlc_resolution.py`](scripts/test_ai_sdlc_resolution.py) tests all merge operations, floor enforcement, clamping modes, and error diagnostics.
