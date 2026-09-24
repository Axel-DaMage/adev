# A-Dev Concept Traceability Matrix

This matrix is the canonical navigation aid for locating each core A-Dev concept across normative doctrine, guidance, adoption assets, evidence, and the explanatory book. It does not create new doctrine or validate the operational claims made by linked assets.

## Reading the matrix

- **Normative source** takes precedence when surfaces disagree.
- **Guide** explains application; **kit asset** is a copyable starting point; **book** is explanatory.
- **Operational evidence** must link to a direct artifact in the canonical [Homedir repository](https://github.com/scanalesespinoza/homedir). A repository-root link marked as a gap is not evidence of a specific result.
- **Maturity:** `established` means doctrine, guidance, and an adoption asset exist; `foundation` means the core model exists but evaluations or implementation examples remain incomplete; `partial` means a material link in the chain is still missing.

## Matrix

| Concept | Normative source | Guide | Kit asset | Operational evidence | Book chapter | Maturity |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline | [`ADEV.md` non-negotiables](../ADEV.md#non-negotiable-rules) | [`framework/practices`](practices/README.md) | [`BASELINE_template.json`](../starter-kit/BASELINE_template.json), [`DAY_0.md`](../starter-kit/DAY_0.md) | [`docs/evidence-index.md`](../docs/evidence-index.md) maps the principle, but no direct Homedir artifact is identified yet: [Homedir](https://github.com/scanalesespinoza/homedir) | [Chapter 04](../adevelopment-book/book/04-baseline-rules-of-engagement.md) | partial — direct operational citation missing |
| Atomic iterations | [`ADEV.md` operating flow](../ADEV.md#operating-flow) | [`QUALITY.md`](../QUALITY.md) | [`FIRST_WEEK.md`](../starter-kit/FIRST_WEEK.md), [`QUALITY_CYCLE_checklist.md`](../starter-kit/QUALITY_CYCLE_checklist.md) | Reference cases are listed in [`docs/evidence-index.md`](../docs/evidence-index.md), but no direct Homedir artifact is identified: [Homedir](https://github.com/scanalesespinoza/homedir) | [Chapter 03](../adevelopment-book/book/03-atomic-iterations.md) | established for doctrine and kit; operational citation gap |
| Evidence | [`ADEV.md` evidence rules](../ADEV.md#evidence-rules) | [`framework/evidence`](evidence/README.md) | [`FIRST_RELEASE.md`](../starter-kit/FIRST_RELEASE.md), [`DECISION_LOG.md`](../starter-kit/DECISION_LOG.md) | [`docs/evidence-index.md`](../docs/evidence-index.md) is an index, not a direct source; artifact-level Homedir links are a stated gap: [Homedir](https://github.com/scanalesespinoza/homedir) | [Chapter 05](../adevelopment-book/book/05-traceability-digital-thread.md) | partial — attribution migration pending |
| Policy | [`Hardness policy and precedence`](hardness/01-policy-and-precedence.md) | [`Hardness definition`](hardness/00-definition-and-scope.md) | [`valid-policy.json`](hardness/fixtures/valid-policy.json), [`policy-schema.json`](hardness/policy-schema.json) | No operational policy evaluation or direct Homedir artifact is recorded. | No dedicated policy chapter; [Chapter 04](../adevelopment-book/book/04-baseline-rules-of-engagement.md) is adjacent explanation. | foundation — kit and evidence gaps |
| Skill | [`Hardness skill contract`](hardness/02-skill-contract-template.md) | [`Hardness overview`](hardness/README.md) | [`Reference skill`](hardness/skills/adev-read-only-inspection/SKILL.md) | No behavioral evaluation or direct Homedir artifact is recorded. | No dedicated skill chapter; [Appendix A](../adevelopment-book/book/appendices/A-templates.md) is adjacent iteration guidance. | foundation — example and evaluation gaps |
| Authority | [`Hardness action risk and authority`](hardness/04-action-risk-authority-model.md) | [`Hardness precedence`](hardness/01-policy-and-precedence.md#precedence) | [`Expectations contract`](hardness/03-human-expectations-contract.md) | No direct operational authority-decision artifact is recorded. | [Chapter 02](../adevelopment-book/book/02-solo-architect.md) explains the architect role; [Chapter 08](../adevelopment-book/book-en/08-autonomy-security-and-responsibility.md) covers security. | foundation — operationalization gap |
| Trust ladder / Autonomy | [`Hardness trust ladder`](hardness/08-trust-ladder-and-autonomy-levels.md) | [`Per-repo configuration`](hardness/09-per-repo-configuration.md) | [`.ai-sdlc.yaml`](../starter-kit/.ai-sdlc.yaml), [`ai-sdlc-schema.json`](hardness/ai-sdlc-schema.json) | Observable metric signals mapped to Git/CI/APM logs; direct Homedir attribution pending. | [Chapter 08](../adevelopment-book/book-en/08-autonomy-security-and-responsibility.md) explains autonomy and responsibility. | established for doctrine and kit; operational evidence aggregation pending |
| Hardness | [`Hardness definition and scope`](hardness/00-definition-and-scope.md) | [`framework/hardness`](hardness/README.md) | [`Skill contract template`](hardness/02-skill-contract-template.md), [`.ai-sdlc.yaml`](../starter-kit/.ai-sdlc.yaml) | No agent-behavior evaluation or direct Homedir artifact is recorded. | No dedicated Hardness chapter; [Chapter 10](../adevelopment-book/book/10-closing.md) is only adjacent future-facing context. | foundation — evaluations and cross-agent proof pending |

## Explicit gaps and next use

1. Add direct Homedir artifact links only after verifying the referenced files, commits, pull requests, issues, releases, or workflow runs.
2. Create a policy-record template and a completed skill-contract example as separate kit cycles.
3. Add behavioral evaluations for Hardness before claiming predictable agent behavior beyond the defined foundation.
4. Use this matrix before changing a concept: update its authoritative row rather than duplicating the rule across doctrine, kit, evidence, and book surfaces.
