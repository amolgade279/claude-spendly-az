# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Spendly — a personal expense-tracker web app built as a scaffolded teaching project. Flask backend, server-rendered Jinja2 templates, vanilla CSS/JS. Features are added incrementally and tracked as numbered "Steps" (see stub comments in `app.py` and `database/db.py`).

## Commands

```bash
python -m venv venv
source venv/Scripts/activate      # Git Bash on Windows
pip install -r requirements.txt
python app.py                     # runs on http://127.0.0.1:5001, debug mode on
pytest                            # run tests
```

There is no build step, linter, or frontend bundler — templates and static assets are served directly by Flask.

## Architecture

```
claude-spendly-az/
├── app.py                    Flask app — ALL routes live here, no blueprints
├── requirements.txt
│
├── database/
│   ├── __init__.py           empty
│   └── db.py                 ⚠ NOT IMPLEMENTED — spec-only stub (get_db/init_db/seed_db)
│
├── templates/
│   ├── base.html             shared shell: navbar + {% block content %} + footer
│   ├── landing.html    ─┐
│   ├── login.html        │
│   ├── register.html     │  each {% extends "base.html" %}
│   ├── terms.html        │
│   └── privacy.html    ─┘
│
├── static/
│   ├── css/style.css         ONE stylesheet, section-commented, CSS-variable driven
│   └── js/main.js            video-modal logic only; loads on every page
│
└── claude-activity/
    └── claude-prompts.md     chronological log of prompts used to build each feature
```

**Request flow:**

```
Browser
  │  GET /route
  ▼
app.py route function
  │
  ├─ implemented   → render_template("page.html")
  │                      │
  │                      ▼
  │                 templates/base.html
  │                   ├─ {% block content %}  ← page-specific markup
  │                   └─ links via url_for(...), never hardcoded paths
  │                      │
  │                      ▼
  │              static/css/style.css + static/js/main.js
  │
  └─ unimplemented → returns plain string, e.g. "Add expense — coming in Step 7"
```

**Route status** (`app.py`):

| Route                    | Status        | Notes                                  |
|---------------------------|---------------|-----------------------------------------|
| `/`                       | ✅ implemented | `landing.html`                          |
| `/register`               | ✅ implemented | `register.html` (UI only, no backend)   |
| `/login`                  | ✅ implemented | `login.html` (UI only, no backend)      |
| `/terms`, `/privacy`      | ✅ implemented | static legal pages                      |
| `/logout`                 | 🚧 placeholder | "coming in Step 3"                      |
| `/profile`                | 🚧 placeholder | "coming in Step 4"                      |
| `/expenses/add`           | 🚧 placeholder | "coming in Step 7"                      |
| `/expenses/<id>/edit`     | 🚧 placeholder | "coming in Step 8"                      |
| `/expenses/<id>/delete`   | 🚧 placeholder | "coming in Step 9"                      |

When implementing a 🚧 route, replace the placeholder return string with real logic — keep the route signature as-is.

**Key conventions per area:**

- `database/db.py` → raw SQLite, no ORM. `get_db()` returns a connection with `row_factory` and foreign keys enabled; `init_db()` uses `CREATE TABLE IF NOT EXISTS`; `seed_db()` inserts dev sample data.
- `static/css/style.css` → reuse existing `:root` variables (`--accent`, `--ink*`, `--paper*`, `--radius-*`); add new rules under the matching section comment, not appended at the end.
- `static/js/main.js` → any new handler must look up its elements and return early if missing, since this file loads on pages (login/register/terms/privacy) that don't have the modal markup.

## Code style

**Python (`app.py`, `database/`)**
- Double quotes for strings.
- Section dividers as comment banners for grouping routes, e.g.:
  ```python
  # ------------------------------------------------------------------ #
  # Routes                                                              #
  # ------------------------------------------------------------------ #
  ```
- One blank line between route functions; route decorator directly above `def`.
- No docstrings/type hints in use — keep new code consistent with the plain, minimal style already there rather than introducing them ad hoc.

**Templates (`templates/*.html`)**
- 4-space indentation.
- Every page template starts with `{% extends "base.html" %}`, then `{% block title %}`, then `{% block content %}` — in that order.
- `url_for(...)` for all internal links/hrefs, never hardcoded paths.
- Blank line after opening a wrapping `<div>`/`<section>` before its first child (see `login.html`), and a blank line before the closing tag — keeps templates readable despite the nesting.

**CSS (`static/css/style.css`)**
- 4-space indentation, one selector block per rule.
- All colors, radii, fonts via `var(--...)` from `:root` — no bare hex values except the two documented one-off bar colors (`#5b7fa6`, `#8b5e83`).
- File is organized into banner-commented sections (same `/* ---- */` divider style as Python); add new rules under the matching section, don't append to the end of the file.

**JavaScript (`static/js/main.js`)**
- ES5-leaning style: `var` (not `let`/`const`), `function` expressions rather than arrow functions.
- Guard clause up top (`if (!a || !b) return;`) before wiring up any listeners — required since this file loads on every page.
- Double quotes for strings, matching Python/HTML.

## Tech constraints

- **Pinned deps only** — `requirements.txt` pins Flask 3.1.3, Werkzeug 3.1.6, pytest 8.3.5, pytest-flask 1.3.0. Don't add new dependencies for small features; prior work explicitly kept diffs dependency-free (e.g. footer links, legal pages).
- **No ORM** — `database/db.py` is spec'd around raw `sqlite3` (`get_db`/`init_db`/`seed_db`). Don't introduce SQLAlchemy or similar.
- **No frontend build tooling** — no npm/webpack/vite/bundler. CSS/JS are plain static files served directly by Flask; don't introduce a build step or transpilation.
- **Single-file app** — all routes live in `app.py`; no blueprints or package split. Keep new routes there unless the file grows large enough to justify restructuring (not the case yet).
- **DB file is gitignored** — `expense_tracker.db` (per `.gitignore`) is the expected SQLite filename; never commit it.
- **`.env` reserved, not yet used** — gitignored for future secrets/config. No secret handling exists yet — don't hardcode credentials when that's introduced.
- **Dev server only** — `app.run(debug=True, port=5001)` in `app.py`. Not configured for production (no WSGI server, no env-based config switching, debug mode leaks stack traces).
- **Python 3.14** is the interpreter used in this environment; there's no `pyproject.toml` or pinned Python version, so avoid relying on syntax that wouldn't run on a more conservative 3.x.

## Implemented vs Roadmap

Step numbers below come directly from in-code markers (`app.py` placeholder strings, the "Step 1" comment in `database/db.py`) — not invented. Steps 2, 5, 6 aren't labeled anywhere in the code; they're left as gaps rather than guessed at.

**Implemented**
- ✅ Landing page (`/`) — hero, features, CTA section, video modal
- ✅ Register page (`/register`) — UI only, form does not persist a user yet
- ✅ Login page (`/login`) — UI only, form does not authenticate yet
- ✅ Terms (`/terms`) and Privacy (`/privacy`) — static legal content
- ✅ Shared layout, nav, footer with legal links

**Roadmap**

```
Step 1 → Database setup .......... get_db / init_db / seed_db   [database/db.py — spec only, not started]
Step 2 → ??? (not labeled in code — likely register/login persistence, since UI exists but nothing is saved)
Step 3 → Logout ................... app.py:29  [placeholder]
Step 4 → Profile .................. app.py:34  [placeholder]
Step 5 → ??? (not labeled — likely an expense list / dashboard view)
Step 6 → ??? (not labeled)
Step 7 → Add expense .............. app.py:49  [placeholder]
Step 8 → Edit expense ............. app.py:54  [placeholder]
Step 9 → Delete expense ........... app.py:59  [placeholder]
```

Practical implication: **Step 1 (database) blocks everything after it** — register/login persistence, profile, and all expense CRUD all depend on `get_db`/`init_db` existing first. If asked to implement a later step, check whether `database/db.py` needs to be built first.

## Working conventions (from prior work in `claude-activity/claude-prompts.md`)

- Changes tend to be scoped tightly to one feature/section at a time — e.g. "touch only the hero section, not features/CTA/footer/nav" — rather than broad refactors.
- Legal/placeholder content (terms, privacy) intentionally leaves bracketed placeholders like `[Effective Date]`, `[Contact Email]`, `[Governing Jurisdiction]` — these are boilerplate, not lawyer-reviewed, and shouldn't be filled with invented values.
- `claude-activity/claude-prompts.md` is a running log of prompts used to build features chronologically — check it for context on why a section looks the way it does before changing it.
