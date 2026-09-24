#!/usr/bin/env bash
# AI-SDLC Configuration Validator Wrapper for CI and local workflows
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${1:-.ai-sdlc.yaml}"

python3 "${SCRIPT_DIR}/validate-ai-sdlc.py" "${CONFIG_FILE}"
