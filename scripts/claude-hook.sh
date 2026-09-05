#!/usr/bin/env bash
set -uo pipefail

cd "$(dirname "$0")/.."

payload=$(cat)

read_field() {
    printf '%s' "$payload" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for key in '$1'.split('.'):
    data = data.get(key, '') if isinstance(data, dict) else ''
print(data)
" 2>/dev/null
}

case "${1:-}" in
    documentation)
        file=$(read_field 'tool_input.file_path')
        case "$file" in
            */src/*.py) ;;
            *) exit 0 ;;
        esac

        document=$(dirname "$file")/CLAUDE.md
        [ -f "$document" ] || exit 0
        [ "$document" -nt "$file" ] && exit 0

        python3 - "$document" <<'PY'
import json
import sys

print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PostToolUse',
        'additionalContext': (
            f'{sys.argv[1]} is older than the code beside it. Non-negotiable 9: an app is not '
            'done until its CLAUDE.md matches what the code now does — same change, not later.'
        ),
    }
}))
PY
        exit 0
        ;;

    gate)
        marker=${TMPDIR:-/tmp}/instagram-mcpserver-docs-gate-$(read_field 'session_id')
        [ -e "$marker" ] && exit 0

        report=$(./scripts/check-docs.sh 2>&1) && exit 0

        : > "$marker"
        printf '%s\n' "$report" >&2
        echo 'check-docs.sh is red. Non-negotiables 8, 9 and 10: documentation is part of the change,' >&2
        echo 'not a follow-up. Fix what is listed above, or say why it stays.' >&2
        exit 2
        ;;
esac

exit 0
