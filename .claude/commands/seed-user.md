---
description: Insert one dummy/test user into the Spendly database for local dev and testing
argument-hint: [name] [email]
arguments: [name, email]
disable-model-invocation: true
allowed-tools: Bash(python3 *)
---

Insert one dummy user into `expense_tracker.db`. Dev/testing utility only — not part of the app itself.

**Name:** `$name` — if empty, invent a realistic placeholder.
**Email:** `$email` — if empty, use `dummy+<random 4-digit number>@example.com` (avoids colliding with the `email` `UNIQUE` constraint on repeat runs).
**Password:** always `Password123`, hashed before storing — never write it plain.

Steps:

1. If `database/db.py` has a working `get_db()`, use it: `from database.db import get_db`. If it's still just the Step 1 stub, connect the same way `get_db()` will: `sqlite3.connect("expense_tracker.db")`, `row_factory = sqlite3.Row`, `PRAGMA foreign_keys = ON`.
2. Make sure the table exists first, in case this runs before `init_db()` ever has:
   ```sql
   CREATE TABLE IF NOT EXISTS users (
       id            INTEGER PRIMARY KEY AUTOINCREMENT,
       name          TEXT NOT NULL,
       email         TEXT NOT NULL UNIQUE,
       password_hash TEXT NOT NULL,
       created_at    TEXT NOT NULL DEFAULT (datetime('now'))
   );
   ```
3. Hash the password with `werkzeug.security.generate_password_hash` (Werkzeug's already a project dependency — nothing new to install).
4. `INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)`.
5. On a `UNIQUE` violation on `email`: if I passed the email explicitly, tell me it's taken and stop; if it was auto-generated, retry once with a new random suffix.
6. Print the new user's `id`, `name`, `email`, and the plaintext password, so I can log in and verify right away.

Run this inline (e.g. a short `python3 -c "..."`) rather than adding a new script file to the repo.