---
description: Insert N random dummy expenses for a given user, spread across the last M months
argument-hint: [user_id] [count] [months]
arguments: [user_id, count, months]
disable-model-invocation: true
allowed-tools: Bash(python3 *)
---

Insert `$count` random expenses for user `$user_id`, dated randomly within the last `$months` months (today back to today minus `$months` months). Dev/testing utility only — not part of the app itself.

Steps:

1. **Always start by stating what this command expects, before touching anything else:**
   ```
   /seed-expense expects 3 arguments in order:
     1. user_id — which user the expenses belong to
     2. count   — how many expenses to create
     3. months  — how many months back to spread them across

   Received: user_id=<value or "not given">, count=<value or "not given">, months=<value or "not given">
   ```
   Fill in the actual values received for `$user_id`, `$count`, `$months` (or "not given" for any that are empty). Show this every time, whether or not all three were passed.

2. **If any of the three is missing, stop and ask for it — never guess or fall back to a default:**
   - Ask only for the ones actually missing, not all three if only one is missing.
   - Missing `user_id`: look up all rows in `users` and show them (`id`, `name`, `email`) as context, then ask which id to use. If `users` is empty, say so and tell me to run `/seed-user` first instead of asking.
   - Missing `count`: ask how many expenses to create.
   - Missing `months`: ask how many months back to spread them across.
   - Wait for my answer before doing anything else — don't insert anything until all three are known.
   - Treat an invalid value the same as missing: a `user_id` that doesn't exist in `users`, or a `count`/`months` that isn't a positive whole number, gets pointed out and asked again rather than silently corrected.

3. Once all three are confirmed, restate the final values being used before moving on.

4. If `database/db.py` has a working `get_db()`, use it: `from database.db import get_db`. If it's still just the Step 1 stub, connect the same way `get_db()` will: `sqlite3.connect("expense_tracker.db")`, `row_factory = sqlite3.Row`, `PRAGMA foreign_keys = ON`.

5. Confirm the table exists first, in case this runs before `init_db()` ever has:
   ```sql
   CREATE TABLE IF NOT EXISTS expenses (
       id          INTEGER PRIMARY KEY AUTOINCREMENT,
       user_id     INTEGER NOT NULL,
       amount      REAL NOT NULL,
       category    TEXT NOT NULL,
       description TEXT,
       date        TEXT NOT NULL,
       created_at  TEXT NOT NULL DEFAULT (datetime('now')),
       FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
   );
   ```

6. Generate the confirmed number of rows, each:
   - `category`: random choice of `Food`, `Travel`, `Bills` (the set already used elsewhere in this project).
   - `amount`: random, in ₹ — Food 100–600, Travel 300–2000, Bills 500–3000.
   - `description`: a short realistic pick matching the category, e.g. Food → "Groceries" / "Dinner out" / "Lunch"; Travel → "Cab ride" / "Metro card top-up" / "Fuel"; Bills → "Electricity" / "Mobile recharge" / "Internet bill".
   - `date`: a random day between today and the confirmed number of months ago, computed from the actual current date at run time — never hardcode a date. Format `YYYY-MM-DD`.
   - Leave `created_at` to its `DEFAULT (datetime('now'))` — don't set it explicitly; it should reflect when the row was actually inserted, not the backdated expense date.

7. Insert all rows in one transaction (`executemany`, or a loop with a single `commit()` at the end) — not one Bash call per row.

8. Print a short summary: how many rows were inserted, for which user (`id`, `name`, `email`), the actual date range covered, and a category breakdown count (e.g. `Food: 7, Travel: 6, Bills: 7`).

Run this inline (e.g. a `python3 -c "..."` or heredoc) rather than adding a new script file to the repo.
