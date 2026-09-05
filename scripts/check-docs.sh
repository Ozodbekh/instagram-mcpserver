#!/usr/bin/env bash
set -uo pipefail

cd "$(dirname "$0")/.."

export LC_ALL=C

status=0
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

documented_paths() {
    awk '
        /^## Current tree/       { header = 1; next }
        header && !inside && /^```/ { inside = 1; next }
        inside && /^```/         { exit }
        !inside                  { next }
        {
            line = $0
            gsub(/│/, " ", line)
            if (line !~ /^ *(├── |└── )/) next

            match(line, /^ */)
            depth = RLENGTH / 4 + 1
            sub(/^ *(├── |└── )/, "", line)

            if (match(line, /  +/)) line = substr(line, 1, RSTART - 1)
            sub(/ ->.*$/, "", line)
            sub(/\/$/, "", line)
            sub(/ +$/, "", line)

            name[depth] = line
            path = name[1]
            for (i = 2; i <= depth; i++) path = path "/" name[i]
            print depth "\t" path "\t" line
        }
    ' docs/rules/structure.md
}

tracked_paths() {
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        git ls-files
        git ls-files --others --exclude-standard | grep -v '^\.claude/'
        printf '%s\n' .env .claude/settings.local.json
        return
    fi

    find . \
        \( -name .git -o -name .venv -o -name __pycache__ -o -name .pytest_cache \
           -o -name .ruff_cache -o -name .mypy_cache -o -name .idea -o -name .vscode \
           -o -name node_modules -o -name htmlcov -o -name media -o -name staticfiles \
           -o -name logs \) -prune -o \
        \( -type f -o -type l \) \
        ! -name '*.py[cod]' ! -name '*.log' ! -name 'db.sqlite3' ! -name '.coverage' \
        ! -name '.DS_Store' ! -name 'CLAUDE.local.md' \
        -print | sed 's|^\./||'
}

real_paths() {
    tracked_paths | sort -u | awk -F/ '
        { print }
        {
            path = $1
            for (i = 2; i < NF; i++) { print path; path = path "/" $i }
            if (NF > 1) print path
        }
    ' | sort -u
}

echo 'structure.md'

documented_paths > "$work/documented"
cut -f2 "$work/documented" | sort -u > "$work/documented_paths"
real_paths > "$work/real_paths"

while read -r path; do
    echo "  missing: $path"
    parent=$(dirname "$path")
    before=$(awk -F'\t' -v parent="$parent" -v path="$path" '
        { entry = $2 }
        entry == path                                     { next }
        parent == "." && index(entry, "/")                { next }
        parent != "." && index(entry, parent "/") != 1    { next }
        parent != "." && index(substr(entry, length(parent) + 2), "/") { next }
        entry < path { previous = entry; next }
        { print previous "\t" entry; exit }
        END { if (!seen) print previous "\t" }
    ' "$work/documented")
    [ -n "$before" ] && echo "    goes between ${before%%	*} and ${before##*	}" |
        sed 's/ and $/ and the end of that directory/;s/between  and/between the start and/'
    status=1
done < <(comm -13 "$work/documented_paths" "$work/real_paths")

while read -r path; do
    echo "  stale entry: $path"
    status=1
done < <(comm -23 "$work/documented_paths" "$work/real_paths")

while read -r path; do
    echo "  listed twice: $path"
    status=1
done < <(cut -f2 "$work/documented" | sort | uniq -d)

while read -r message; do
    echo "  $message"
    status=1
done < <(awk -F'\t' '
    {
        depth = $1; path = $2; name = $3
        parent = (depth == 1) ? "" : substr(path, 1, length(path) - length(name) - 1)
        if ((parent in previous) && previous[parent] > name)
            print "out of order: " path " comes after " parent "/" previous[parent]
        previous[parent] = name
    }
' "$work/documented")

echo 'CLAUDE.md'

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git log --format='@%ct' --name-only --no-renames | awk '
        /^@/    { stamp = substr($0, 2); next }
        NF == 0 { next }
        !($0 in when) { when[$0] = stamp }
        END {
            for (path in when) {
                depth = split(path, part, "/")
                if (part[depth] != "CLAUDE.md") continue
                documented[substr(path, 1, length(path) - length(part[depth]) - 1)] = when[path]
            }
            for (path in when) {
                depth = split(path, part, "/")
                if (depth == 1 || part[depth] == "CLAUDE.md") continue
                directory = substr(path, 1, length(path) - length(part[depth]) - 1)
                if (!(directory in documented)) continue
                if (when[path] <= documented[directory]) continue
                if (when[path] <= newest[directory]) continue
                newest[directory] = when[path]
                blame[directory] = path
            }
            for (directory in blame)
                print "  older than " blame[directory] ": " directory "/CLAUDE.md"
        }
    ' | sort
else
    echo '  not a git repository — the staleness check needs history'
fi

echo 'forecasts in CLAUDE.md'

while read -r message; do
    echo "  $message"
    status=1
done < <(
    find . -name CLAUDE.md -not -path './.venv/*' -not -path './.git/*' -not -path './docs/*' \
        -not -path './CLAUDE.md' |
        while read -r file; do
            grep -ohE '`(src|root|tests)/[A-Za-z0-9_/.-]+`' "$file" | tr -d '`' | sort -u |
                while read -r path; do
                    [ -e "$path" ] || echo "$file names a path that does not exist: $path"
                done
        done
)

echo 'routes in docs/api'

while read -r route; do
    [ -z "$route" ] && continue
    documented=$(printf '%s' "$route" | sed -E 's/<[a-z]+:([a-z_]+)>/{\1}/g')
    grep -rqF "$documented" docs/api/ && continue

    leaf=$(printf '%s' "$documented" | sed -E 's|.*/([^/]+/)$|\1|')
    prefix=${documented%"$leaf"}
    [ -n "$prefix" ] &&
        grep -rlF "$prefix" docs/api/ | xargs -r grep -qlF "$leaf" && continue

    echo "  $documented is routed and appears in no docs/api file"
    status=1
done < <(grep -rho "path('[^']*'" src --include=urls.py 2>/dev/null | sed "s/path('//;s/'$//" | sort -u)

echo 'pages on the docs/api map'

while read -r page; do
    needle=${page#docs/api/}
    grep -qF "$needle" docs/api/README.md && continue

    echo "  $needle is a page and no row of docs/api/README.md names it"
    status=1
done < <(find docs/api -name '*.md' -not -name README.md | sort)

echo 'claims in CLAUDE.md'

number_of() {
    case "$(printf '%s' "$1" | tr 'A-Z' 'a-z')" in
        one) echo 1 ;;      two) echo 2 ;;      three) echo 3 ;;    four) echo 4 ;;
        five) echo 5 ;;     six) echo 6 ;;      seven) echo 7 ;;    eight) echo 8 ;;
        nine) echo 9 ;;     ten) echo 10 ;;     eleven) echo 11 ;;  twelve) echo 12 ;;
        thirteen) echo 13 ;; fourteen) echo 14 ;; fifteen) echo 15 ;; sixteen) echo 16 ;;
        seventeen) echo 17 ;; eighteen) echo 18 ;; nineteen) echo 19 ;; twenty) echo 20 ;;
        *) echo '' ;;
    esac
}

report() {
    echo "  $1"
    status=1
}

while read -r file; do
    [ -z "$file" ] && continue
    directory=$(dirname "$file")

    if [ -f "$directory/models.py" ]; then
        word=$(grep -ohiE '\b[a-z]+ models?, migrated' "$file" | head -1 | cut -d' ' -f1)
        claimed=$(number_of "$word")
        real=$(grep -c '^class ' "$directory/models.py")
        [ -n "$claimed" ] && [ "$claimed" != "$real" ] &&
            report "$file says $word models, $directory/models.py holds $real"
    fi

    for module in services selectors; do
        grep -qiE "\bno $module\b" "$file" && [ -f "$directory/$module.py" ] &&
            report "$file says no $module, $directory/$module.py exists"
    done

    routes=$(find "$directory" -name urls.py -exec grep -ho 'path(' {} + | wc -l)

    grep -qiE '\bno endpoints\b' "$file" && [ "$routes" -gt 0 ] &&
        report "$file says no endpoints, $directory routes $routes"

    word=$(grep -ohiE '\b[a-z]+ endpoints\b' "$file" | head -1 | cut -d' ' -f1)
    claimed=$(number_of "$word")
    [ -n "$claimed" ] && [ "$routes" -gt 0 ] && [ "$claimed" != "$routes" ] &&
        report "$file says $word endpoints, $directory routes $routes"
done < <(find src -name CLAUDE.md 2>/dev/null | sort)

echo 'tools on the mcp surface'

if [ -d src/mcp_server/tools ] && [ -f src/mcp_server/CLAUDE.md ]; then
    while read -r tool; do
        grep -qF "$tool" src/mcp_server/CLAUDE.md && continue
        echo "  $tool is a tool and src/mcp_server/CLAUDE.md does not name it"
        status=1
    done < <(grep -rhoE '^(async )?def [a-z_]+' src/mcp_server/tools --include='*.py' |
        sed -E 's/^(async )?def //' | grep -v '^_' | sort -u)
fi

exit $status
