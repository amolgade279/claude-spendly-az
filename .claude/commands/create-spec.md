---
description: Generate a grounded, properly structured spec document (design, rules, acceptance criteria) for an upcoming Spendly roadmap Step
argument-hint: [step_number] [feature_slug] [scope_note]
arguments: [step_number, feature_slug, scope_note]
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Write
---

Write a spec document for Spendly roadmap Step `$step_number`, saved to `.claude/specs/step-$step_number-$feature_slug-spec.md`. A spec exists so implementation — by a person or by Claude Code — never has to guess at design; every decision in it must trace back to something already true in this repo, not be invented. This is not a dev/testing utility — the output is a committed project artifact, same standing as `.claude/specs/step-1-database-spec.md`.

Steps:

1. **Always start by stating what this command expects, before touching anything else:**
   ```
   /write-spec expects up to 3 arguments:
     1. step_number  — which roadmap Step (from CLAUDE.md) this spec is for
     2. feature_slug — short kebab-case name, used in the output filename
     3. scope_note   — optional: what this step should cover, only needed if CLAUDE.md doesn't already say

   Received: step_number=<value or "not given">, feature_slug=<value or "not given">, scope_note=<value or "not given">
   ```
   Show this every time, whether or not all three were passed.

2. **If `step_number` or `feature_slug` is missing, stop and ask — never guess or fall back to a default:**
   - Missing `step_number`: read the Roadmap section of `CLAUDE.md`, show it, and ask which Step this spec is for.
   - Missing `feature_slug`: propose one derived from that Step's roadmap label (e.g. Step 2 → `register-login`, Step 7 → `add-expense`) and confirm it — don't invent one silently.
   - A file already exists at `.claude/specs/step-$step_number-*-spec.md`: point this out and ask whether to revise the existing one or stop — never silently overwrite a spec.

3. **Ground the spec before writing a word of design.** Read each of these — don't answer from memory:
   - `CLAUDE.md` — the Roadmap table and Route status table, for what this Step is already on record as covering, plus the Tech constraints section
   - `app.py` — the exact placeholder route(s) this Step will replace (stub text, route signature, decorator)
   - `database/db.py` and every file already under `.claude/specs/` — existing schema, functions, and prior decisions this Step depends on or extends
   - the relevant file(s) under `templates/` — any forms, `{% if error %}` blocks, or markup already built and waiting for a backend
   - `claude-activity/claude-prompts.md` — prior constraints or decisions already stated for this area

   If `$scope_note` was given, treat it as intent, not as license to skip grounding — every concrete detail (field names, routes, existing markup) still has to trace back to what this step actually found in the repo, not to the note alone.

4. **If the feature's behavior is still ambiguous after grounding** (expected for roadmap Steps 5/6, which `CLAUDE.md` marks as unlabeled) **and no `scope_note` closes the gap, stop and ask** specific questions rather than guessing — e.g. "should the dashboard show a running total per category, a date-range filter, or both?" Wait for answers before drafting.

5. **Draft the spec using this section structure.** Keep every section unless it's genuinely not applicable (e.g. skip a schema table if this Step adds no columns) — never drop Grounding, Open Questions, Rules for implementation, or Acceptance Criteria:

   ```markdown
   # Step {N} — {Feature Title} Spec (Spendly)

   {One paragraph: what this spec defines and the contract it sets.}

   ## Grounding
   {Bullet list — each point cites a specific file/existing artifact this design is based on.}

   ## Scope
   **In scope:** ...
   **Out of scope:** ... (name which Step number it belongs to instead)

   ## Dependencies
   **Depends on:** ...
   **Blocks:** ...

   ## Design
   {Whatever the feature actually needs: schema table(s) + mermaid ER diagram if it touches the DB;
    route table + request/response behavior if it's route logic;
    function skeleton(s) — signature plus a comment, no docstrings, matching CLAUDE.md's code style — for new functions.}

   ## Validation & Constraints
   {Fixed lists, required fields, uniqueness rules — anything enforced at the DB, form, or route layer.}

   ## Rules for implementation
   {Hard constraints from CLAUDE.md's Tech constraints section, plus anything Step-specific.}

   ## Error handling expectations
   {What must fail, how, and which route/template surfaces it.}

   ## Open questions — deliberately left out
   {Anything explicitly deferred to a later Step, so it reads as a decision, not an oversight.}

   ## Acceptance Criteria
   {Checklist — see rules in step 6. This is what implementation is checked against to call the Step done.}
   ```

6. **Acceptance Criteria rules** — this section is what the user (or Claude Code) checks implementation against, so every line has to be independently verifiable:
   - One behavior per checkbox (`- [ ]`) — no compound criteria joined by "and."
   - Phrase each as an observable outcome, not an implementation detail — e.g. "`POST /register` with a duplicate email re-renders `register.html` with `error` set," not "uses a try/except."
   - Cover the happy path, every case named in Error handling expectations, and any existing test file this Step should extend (e.g. `tests/test_db.py`).
   - Always end the checklist with: "All queries/inputs follow the Rules for implementation above, with no exceptions."

7. **Before writing anything, restate the final filename and section list, and confirm** — this is a new committed file, not a scratch note.

8. **Write the file, then print a short summary**: filename, which sections were included (and which were skipped, with a one-line reason each), and the number of Acceptance Criteria items.

This command only ever produces or revises a file under `.claude/specs/`. It must never modify `app.py`, `database/db.py`, or any template — if verifying a detail requires reading those files, read them; don't edit them.
