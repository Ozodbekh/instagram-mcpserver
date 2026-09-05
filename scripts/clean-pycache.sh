#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

removed=$(find . -type d -name __pycache__ -not -path './.venv/*' -not -path './.git/*' -print -exec rm -rf {} + | wc -l)

printf 'removed %s __pycache__ directories\n' "$removed"
