# Hardness

Hardness is A-Dev's emerging framework for operationally governing agents so their behavior is bounded, explainable, verifiable, and aligned with user expectations.

It is not presented as an external technical standard. It is a working A-Dev term for turning intent into durable behavior through explicit policies, capability contracts, authority boundaries, earned trust ladders, and evidence.

## Start here

1. [`00-definition-and-scope.md`](00-definition-and-scope.md) defines the concept, intended outcomes, and boundaries.
2. [`01-policy-and-precedence.md`](01-policy-and-precedence.md) defines the minimum policy model and deterministic conflict resolution.
3. [`02-skill-contract-template.md`](02-skill-contract-template.md) defines the minimum contract for creating or reviewing an agent skill.
4. [`03-human-expectations-contract.md`](03-human-expectations-contract.md) turns a user request into explicit intent, authority, constraints, uncertainty, and stop conditions.
5. [`04-action-risk-authority-model.md`](04-action-risk-authority-model.md) classifies action effects and the approval, evidence, and escalation required for each.
6. [`05-policy-schema-and-fixtures.md`](05-policy-schema-and-fixtures.md) provides a local policy-record schema, fixtures, and reproducible structural validation.
7. [`06-agent-consumption-guide.md`](06-agent-consumption-guide.md) explains how an agent reads canon, selects a bounded skill, and applies policy without assuming a runtime.
8. [`07-compatibility-layer.md`](07-compatibility-layer.md) defines portable Hardness contracts and runtime adaptation without a runtime dependency.
9. [`08-trust-ladder-and-autonomy-levels.md`](08-trust-ladder-and-autonomy-levels.md) establishes the six canonical autonomy levels (`shadow`, `suggest`, `auto-PR`, `auto-merge-low`, `auto-merge-all`, `auto-deploy`), promotion criteria, demotion triggers, and SLOs.
10. [`09-per-repo-configuration.md`](09-per-repo-configuration.md) defines per-repository autonomy configuration via `.ai-sdlc.yaml` and the [`ai-sdlc-schema.json`](ai-sdlc-schema.json) contract.
9. [`08-prompt-injection-defense.md`](08-prompt-injection-defense.md) establishes the normative trust-boundary model, sanitization pipeline, and forbidden-action rules for untrusted content across all ingestion vectors.
9. [`08-autonomous-review-and-merge-gate-policy.md`](08-autonomous-review-and-merge-gate-policy.md) defines the PR risk taxonomy, required review evidence matrix, and machine-implementable merge-gate decision table.
9. [`08-issue-definition-of-ready.md`](08-issue-definition-of-ready.md) defines the intake contract for agent-consumable issues, atomicity invariants, machine-checkable CI validation rules, and escalation semantics.
9. [`08-org-wide-policy-model.md`](08-org-wide-policy-model.md) defines the normative specification for organization-wide `.ai-sdlc.yaml` resolution, inheritance, field merge semantics, and non-overridable security floors across repository fleets.

## Relationship to A-Dev

A-Dev governs disciplined delivery. Hardness makes the agent-facing part of that governance explicit:

`user expectation -> applicable policy -> bounded skill -> authorized action -> trust level gating -> evidence -> evaluation`
`user expectation -> applicable policy -> bounded skill -> untrusted input defense -> authorized action -> evidence -> evaluation`
`issue intake (DoR) -> user expectation -> applicable policy -> bounded skill -> authorized action -> evidence -> evaluation`

The existing baseline remains useful, but Hardness distinguishes universal doctrine, scoped policy, project overlay, reusable skill, earned autonomy level, and behavioral evidence so the baseline does not grow into an unreviewable list of rules.

## Current maturity

This is a foundation, not a completeness claim. The expectation contract, action risk classes, policy-record schema, reference skill, compatibility layer, trust ladder doctrine, and per-repo `.ai-sdlc.yaml` schema are defined; runtime-backed automated enforcement tooling and cross-agent proof are developed progressively across the lifecycle.
