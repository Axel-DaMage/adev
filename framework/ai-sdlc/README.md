# AI-SDLC Declarative Pipeline Specification & Tooling

This directory contains the canonical normative specification, schema, example configurations, fixtures, and CI validation tooling for `.ai-sdlc.yaml`.

## Overview

`.ai-sdlc.yaml` is the declarative configuration contract placed at the root of a repository to govern autonomous and semi-autonomous AI coding agents across the entire software development lifecycle.

## Contents

- **[Specification (01-specification.md)](01-specification.md)**: Full normative specification defining schema architecture, Progressive Autonomy Ladder mappings, verification profiles, review policies, label taxonomy, model routing, and escalation triggers.
- **[JSON Schema (`../ai-sdlc.schema.json`)](../ai-sdlc.schema.json)**: Normative JSON Schema (Draft-07) validating `.ai-sdlc.yaml` files.
- **[Examples (`examples/`)](examples/)**: Production-grade `.ai-sdlc.yaml` configurations for multiple repository archetypes:
  - `01-high-assurance-backend.ai-sdlc.yaml`: High-assurance backend / microservice archetype with strict risk tiers and multi-role signoff.
  - `02-content-docs-site.ai-sdlc.yaml`: Documentation / content site archetype with automated linting and guarded auto-merge for doc fixes.
  - `03-library-monorepo.ai-sdlc.yaml`: Reusable library / monorepo archetype with matrix verification and semantic PR labeling.
- **[Fixtures (`fixtures/`)](fixtures/)**: Test fixtures demonstrating valid and invalid configurations for regression testing and CI verification.
- **[Scripts (`scripts/`)](scripts/)**: CI-ready validation tooling:
  - `validate-ai-sdlc.py`: Portable, zero-dependency Python 3 CLI for schema and semantic validation.
  - `validate-ai-sdlc.sh`: POSIX shell wrapper for CI pipelines.
  - `validate-ai-sdlc.ps1`: PowerShell validation script for Windows environments.

## Quick Start: Validating in CI

Run the validator against your repository's configuration:

```bash
# Using Python
python3 framework/ai-sdlc/scripts/validate-ai-sdlc.py --config .ai-sdlc.yaml

# Using Shell script
bash framework/ai-sdlc/scripts/validate-ai-sdlc.sh .ai-sdlc.yaml
```

The script exits with code `0` on success and non-zero on failure with structured diagnostic messages.
