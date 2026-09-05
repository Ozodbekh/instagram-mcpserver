---
paths:
  - "**/CLAUDE.md"
---

# CLAUDE.md files

`CLAUDE.md` holds what the code cannot state by itself: why a rule exists, what a field means,
which formula applies, what an endpoint or a tool promises. It is written for whoever opens the
directory next — human or AI.

## The rule

**Work is not finished until every `CLAUDE.md` you touched matches what the code now does.**

Same change, not later. A file describing an endpoint that no longer exists is worse than no file,
because it is trusted.

## Three levels

The root file loads at launch; a nested one loads **on demand**, when a file in that directory is
read. The deeper the file, the more specific. Nothing is repeated between levels — a fact lives at
the deepest level where it is still true.

```
CLAUDE.md                     the project
├── root/CLAUDE.md            the configuration
├── src/CLAUDE.md             what is an app and what is not
│   └── src/media/CLAUDE.md   the domain
└── tests/CLAUDE.md           the suite
```

**There is no version level.** This project's API is not versioned — see `api-drf.md`. A directory
per version is the thing sides-and-versions projects need and this one does not, and inventing the
level would create a file with nothing true to put in it.

| Level | Holds | Never holds |
|---|---|---|
| Project | stack, commands, the rules that apply to every line | anything app-specific |
| `root/` | what is configured, what is deliberately absent and why | application behaviour |
| App | models, field meanings, business rules, constraints, side effects, what it exposes | project rules |
| `tests/` | fixtures, what must be running, what is mocked | business rules |

After `/compact` the root file is re-read from disk; nested ones are not. Anything that must
survive a long session belongs at the root or in `docs/rules/`.

## Shape

Open with one line saying what the directory is, then only the sections that have something to say.
An app file usually runs **Status**, **Models**, the business rules under headings of their own,
**Exposed by**, **Open**, **Notes**. Never invent a section to fill it; never drop one that has
content.

Every file ends with the same note: current state only, no changelog, git is the history, update
this file after finishing work here.

`scripts/check-docs.sh` reports every `CLAUDE.md` older than a file beside it, and every `src/`,
`root/` or `tests/` path a `CLAUDE.md` names that does not exist. The first is a prompt to look,
not a verdict — a formatting pass changes a timestamp without changing behaviour. The second is
always a fault.

## Size

Under 200 lines. Longer files consume context and are followed less reliably. If an app file is
growing past that, either the app does too much, or the content is a project rule and belongs in
`docs/rules/`.

## What to write

What a reader cannot get from the code in ten seconds:

- **Field meaning**, not field type. `expires_at` is when Meta stops accepting the token, not
  `DateTimeField`.
- **Formulas and quotas, verbatim.** `engagement = (likes + comments) / reach`.
- **Thresholds with their unit and timezone.** A publishing quota, and the window it resets in.
- **Constraints, and what violating one returns.**
- **Side effects.** A row written, a token refreshed, a container created at Meta.
- **Which surface exposes what** — REST, an MCP tool, or neither.
- **Every deviation from a rule, and why.** A quirk kept on purpose is recorded here or the next
  reader will "fix" it.
- **What is Meta's behaviour rather than ours.** A field this codebase cannot change, an error
  code the Graph API returns, an eventual-consistency window — the next reader must not spend an
  afternoon looking for the bug in our code.

## What not to write

- **Anything that does not exist yet.** No planned apps, no "coming later", no directory not yet
  created. A `CLAUDE.md` is read as fact: list `insights/` before it exists and the next session
  imports from it. Plans belong in `docs/structure-decisions.md`.
- **A changelog.** Current state only. Git is the history, and a stale changelog costs context
  every session.
- **A file listing.** `docs/rules/structure.md` owns the tree.
- **Request and response schemas.** Those belong in `docs/api/`; the OpenAPI schema is generated.
  This says what an endpoint *means*.
- **Project rules.** Style, naming, error format and testing live in the root `CLAUDE.md` and
  `docs/rules/`. Two copies of a rule drift, and the next reader picks between them arbitrarily.
- **Anything unverified.** If you did not check it, do not write it. A Graph API field you
  remember is not a field you checked.

## Language

English, like every document here. Short sentences. Specific over general — "page size 20, max
100" beats "paginated sensibly".
