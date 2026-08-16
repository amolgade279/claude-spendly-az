# Step 1 — Database Setup: Implementation Plan

## Context

Spendly's `database/db.py` is currently a comment-only stub — `get_db()`, `init_db()`, `seed_db()` don't exist yet, and nothing in `app.py` creates or seeds a database. This blocks every downstream step (register/login persistence, profile, expense CRUD). `.claude/specs/step-1-database-spec.md` was written to remove all ambiguity — exact schema, exact function skeletons, exact seed data, a fixed 7-value category list enforced via `CHECK`, plus explicit implementation rules, error-handling expectations, and a Definition of Done checklist.

This plan turns that spec into concrete file diffs. Exploration confirmed the repo is a clean slate for this work: `database/db.py`/`__init__.py` have no real code to preserve, `app.py` has no DB imports/`secret_key`, and no `tests/`/`conftest.py` exist yet. Register/login POST handling is explicitly **out of scope** — that's Step 2, per `CLAUDE.md`'s roadmap and the spec's own Open Questions section (which flags `app.secret_key` as intentionally deferred too).

User confirmed: include the optional `tests/test_db.py` (recommended in the spec) since `pytest`/`pytest-flask` are pinned but unused so far.

The user also asked to save this plan itself as a file under the project's `.claude/plans/` folder (already present in `.gitignore`, so it's meant to hold local planning docs) — this happens as the first task after approval.

## Files to create/change

### 1. `database/db.py` — full implementation (replaces the stub)

```python
# Step 1 — Database Setup
# get_db()   — returns a SQLite connection with row_factory and foreign keys enabled
# init_db()  — creates all tables using CREATE TABLE IF NOT EXISTS
# seed_db()  — inserts sample data for development

import sqlite3

from werkzeug.security import generate_password_hash


# ------------------------------------------------------------------ #
# Connection                                                          #
# ------------------------------------------------------------------ #

def get_db():
    conn = sqlite3.connect("expense_tracker.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ------------------------------------------------------------------ #
# Schema                                                              #
# ------------------------------------------------------------------ #

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            amount      REAL NOT NULL,
            category    TEXT NOT NULL CHECK (category IN ('Food', 'Transport', 'Bills', 'Health', 'Entertainment', 'Shopping', 'Other')),
            description TEXT,
            date        TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_expenses_user_id   ON expenses (user_id);
        CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses (user_id, date);
    """)
    conn.commit()
    conn.close()


# ------------------------------------------------------------------ #
# Seed data                                                           #
# ------------------------------------------------------------------ #

def seed_db():
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing == 0:
        password_hash = generate_password_hash("Password123")
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@example.com", password_hash),
        )
        user_id = cursor.lastrowid

        expenses = [
            ("2026-08-01", "Food", 450.00, "Groceries"),
            ("2026-08-03", "Transport", 1200.00, "Cab to airport"),
            ("2026-08-05", "Bills", 2200.00, "Electricity"),
            ("2026-08-08", "Health", 380.00, "Pharmacy"),
            ("2026-08-10", "Entertainment", 999.00, "Movie tickets"),
            ("2026-08-12", "Shopping", 650.00, "New headphones"),
            ("2026-08-14", "Other", 220.00, "Miscellaneous"),
            ("2026-08-15", "Food", 340.00, "Dinner out"),
        ]
        for date, category, amount, description in expenses:
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, description, date) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, amount, category, description, date),
            )

        conn.commit()
    conn.close()
```

All SQL uses `?` placeholders — no f-strings/concatenation. `cursor.lastrowid` avoids a second query for the new user's id. `database/__init__.py` stays empty.

### 2. `app.py` — wire up startup calls

Add the import under the existing `flask` import, and a new banner-commented block right after `app = Flask(__name__)` that calls `init_db()`/`seed_db()` at module scope (matches the spec's instruction and the existing banner style, e.g. the `# Routes #` banner):

```python
from flask import Flask, render_template

from database.db import init_db, seed_db

app = Flask(__name__)


# ------------------------------------------------------------------ #
# Database setup                                                      #
# ------------------------------------------------------------------ #

init_db()
seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #
... (rest of app.py unchanged — no secret_key, no register/login POST logic; that's Step 2)
```

### 3. `tests/conftest.py` (new)

No `conftest.py`/`pytest.ini`/`pyproject.toml` exists yet, and `tests/` will have no `__init__.py`, so plain `pytest` (per `CLAUDE.md`'s documented command) would add `tests/` — not the repo root — to `sys.path`, breaking `from database.db import ...`. Bootstrap the repo root onto `sys.path` here, and centralize the DB-isolation fixture:

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield tmp_path
```

`get_db()` hardcodes the relative filename `"expense_tracker.db"` per the spec's fixed no-argument signature — `monkeypatch.chdir(tmp_path)` makes that relative path resolve inside a fresh temp directory per test, so tests never touch the real dev database and don't need `get_db()`'s signature changed.

### 4. `tests/test_db.py` (new)

Six tests, each using the `isolated_db` fixture:

- `test_init_db_creates_tables_and_indexes` — queries `sqlite_master` for both tables and both indexes.
- `test_category_check_constraint` — inserting an expense with `category="NotACategory"` raises `sqlite3.IntegrityError`.
- `test_seed_db_inserts_demo_user_and_expenses` — demo user exists, password hash round-trips via `check_password_hash` (and isn't stored as plaintext), exactly 8 expenses exist for that user.
- `test_seed_db_is_idempotent` — calling `seed_db()` twice still leaves 1 user / 8 expenses.
- `test_duplicate_email_raises_integrity_error` — second insert with the same email raises `sqlite3.IntegrityError`.
- `test_bogus_user_id_raises_integrity_error` — inserting an expense with `user_id=9999` raises `sqlite3.IntegrityError` (confirms FK pragma is active).

CHECK/FK violations raise synchronously on `conn.execute(...)` in SQLite, so no `conn.commit()` is needed inside the `pytest.raises` blocks. No new dependencies — `tmp_path`/`monkeypatch` are core pytest fixtures already available via the pinned `pytest==8.3.5`; `pytest-flask`'s `client` fixture isn't needed since no Flask route is under test.

### 5. Save this plan

Create `.claude/plans/` (doesn't exist on disk yet, already gitignored) and write this plan's content to `.claude/plans/step-1-database-plan.md`, as the user requested.

## Definition of Done → how it's satisfied

| Item | Satisfied by |
|---|---|
| `get_db`/`init_db`/`seed_db` implemented | §1 |
| `app.py` calls `init_db()`/`seed_db()` on startup | §2 |
| DB file created on startup | `sqlite3.connect(...)` inside `get_db()` creates it; `init_db()` runs at import time |
| Both tables + indexes + CHECK exist | manual `.schema` check + `test_init_db_creates_tables_and_indexes` |
| Demo user with hashed password | `test_seed_db_inserts_demo_user_and_expenses` |
| 8 seed expenses across all 7 categories | same test (count == 8), hardcoded list in `seed_db()` |
| No duplicate seed data on repeated runs | `COUNT(*)` guard + `test_seed_db_is_idempotent` |
| App starts without errors | manual `python app.py` check |
| FK enforcement works | `PRAGMA foreign_keys = ON` in `get_db()` + `test_bogus_user_id_raises_integrity_error` |
| All queries parameterized | every statement uses `?` — verified by reading the diff |
| Can log in with demo creds | not testable until Step 2 exists; hash round-trip assertion gives confidence today |
| Optional `tests/test_db.py` | §3 + §4 |

## Verification steps

1. `python app.py` from repo root — no traceback, then Ctrl+C.
2. `sqlite3 expense_tracker.db ".schema"` — both tables, both indexes, and the `category` CHECK constraint text appear.
3. `sqlite3 expense_tracker.db "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM expenses;"` — expect `1` and `8`.
4. Run `python app.py` again — counts still `1`/`8` (no duplication).
5. `pytest tests/test_db.py -v` — all 6 tests pass.
6. Confirm `expense_tracker.db` isn't staged by git (already gitignored).

## Critical files

- `database/db.py` (rewrite)
- `app.py` (small addition)
- `tests/conftest.py` (new)
- `tests/test_db.py` (new)
- `.claude/plans/step-1-database-plan.md` (new — copy of this plan)
