# AI-SDLC on GitHub Actions — Reusable Workflows

The pipeline stages live as `workflow_call` workflows in this repository —
the reference implementation of the A-Dev automation specs. Any repository
adopts the pipeline by adding a thin caller workflow; no persistent
infrastructure is required.

## Adopting `ai-sdlc-implement`

```yaml
# .github/workflows/ai-sdlc.yml in the consuming repo
name: ai-sdlc
on:
  issues:
    types: [labeled]

jobs:
  implement:
    if: github.event.label.name == 'ready-to-implement'
    uses: Axel-DaMage/adev/.github/workflows/ai-sdlc-implement.yml@v1
    with:
      issue-number: ${{ github.event.issue.number }}
      scc-ref: v0.5.0            # pin a release, never float main
    secrets:
      SC_API_KEY: ${{ secrets.SC_API_KEY }}
      SC_BASE_URL: ${{ secrets.SC_BASE_URL }}   # optional — provider default if unset
```

Required repo secret: `SC_API_KEY` (provider key, e.g. an OmniRoute token or
OpenAI key). `SC_BASE_URL` selects the endpoint (OmniRoute, OpenAI, any
OpenAI-compatible API).

## Contract

| Guarantee | Mechanism |
|-----------|-----------|
| Agent never touches git state | `scc --no-commit` (feature-detected); the workflow owns branch/commit/push/PR |
| Budget ceilings | `max-seconds` (default 900s) + `max-steps` (default 60) inputs → `SC_BUDGET_EXCEEDED` on exhaustion |
| Idempotent dispatch | skips when an `issue-N-*` PR already exists; `concurrency` group per issue |
| Machine-consumable outcome | run manifest (`--output-format json` / `--summary-file`), audit JSONL, artifacts uploaded every run |
| Issue feedback | comment posted with exit code + manifest summary |
| GraphQL-free | issue fetch and PR creation use REST endpoints |

## Flags used (progressive enhancement)

The workflow probes `scc chat --help` and enables each flag only when the
pinned version supports it — `scc-ref` can lag the feature train safely:

`--no-commit` · `--audit-log` · `--summary-file` · `--output-format json` ·
`--max-seconds` · `--max-steps` · `--prompt-file`

## Security notes

- `GITHUB_TOKEN` is scoped to `contents/pull-requests/issues: write` for the
  calling repo only.
- The agent config writes the API key into `$HOME/.sc-agent/config.json`
  inside the ephemeral runner — never into the workspace or the PR.
- For forked repos, do not run this workflow on `pull_request_target` with
  secrets; intake on `issues.labeled` only.
