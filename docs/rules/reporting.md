---
paths:
  - "docs/rules/reporting.md"
---

# Reporting

How much to write **after** the work is done. This is about the answer, not about the code.

## The rule

**Report the outcome, not the work.** The diff already shows what changed and the test run
already shows that it passes. Neither needs a prose copy, and a copy costs tokens on every
single turn.

Default for a finished task: **under ten lines**. A one-file change is one or two sentences.
Write more only for something the user cannot see otherwise — a failure, a decision that is
theirs to make, or a part of the scope you could not finish.

## Keep

- What is true now, in one line.
- What was verified, with the number: `41 tests pass`, never `everything works`.
- What is not done, and why.
- A real open question.

## Cut

- A list or table of every file touched. That is `git diff --stat`.
- Restating the plan you just carried out.
- Arguing that each change is correct when nobody disputed it.
- Section headers on a short answer — headers turn two sentences into a report.
- Anything already said earlier in the same conversation.
- Praising the result: "excellent", "now everything is consistent".

## Never claim a call you did not make

Tests mock Meta. "The publish works" after a mocked test means the mock was satisfied, and saying
otherwise is the one kind of wrong report that costs somebody a real post. Say what ran.

## A question is not a task

Asked a question, answer it. No summary, no next steps, no offer to continue.

## Commits

The same principle, already written down in `git.md`: subject under 60 characters, body about
five lines, and the commit belongs to the repository owner — no assistant named in it anywhere.
