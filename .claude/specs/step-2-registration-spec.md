# Step 2 — Registration Spec (Spendly)

This spec defines the contract for making `POST /register` actually create a user — replacing the current GET-only, UI-only route with one that validates input, persists to the `users` table via `database/db.py`, and handles the failure cases the template already has markup for. On success, the user is redirected to `/login` with a one-time success message confirming account creation. Login persistence and session handling are explicitly out of scope (see Scope below) — this document only covers account creation and the display-only success message on redirect.

## Grounding

- `app.py:25-27` — the current route: `@app.route("/register")` / `def register(): return render_template("register.html")`. GET-only, no `methods=`, no logic.
- `templates/register.html` — the form already posts `name`, `email`, `password` to `/register` (`action="/register"`, `method="POST"`), and already has an `{% if error %}<div class="auth-error">{{ error }}</div>{% endif %}` block waiting for a route to populate `error`. The password field's placeholder text is `"Min. 8 characters"` — a promise not yet enforced anywhere. There is currently no confirm-password field in the template — this was found missing during manual testing and is added by this spec (see Scope).
- `database/db.py` (implemented per `.claude/specs/step-1-database-spec.md`) — `get_db()` returns a `sqlite3.Row`-factory connection with foreign keys on; the `users` table is `(id, name, email UNIQUE, password_hash, created_at)`.
- `.claude/specs/step-1-database-spec.md`'s route table already names the query pattern for this step: `INSERT INTO users (...)` — catch the `UNIQUE` violation on `email`, re-render `register.html` with `error=`.
- `CLAUDE.md` Tech constraints — raw `sqlite3`, no ORM, no new dependencies, pinned `Flask 3.1.3` / `Werkzeug 3.1.6`. `werkzeug.security` (`generate_password_hash`) is already used in `database/db.py`'s seed data, so it needs no new import path, just reuse in `app.py`.
- `templates/login.html` — exists and is linked from `register.html`'s `auth-switch` footer (`url_for('login')`), confirming `/login` is the natural redirect target after account creation since no session exists yet to log the user in automatically. It currently has an `{% if error %}` block but nothing for a success message.
- `static/css/style.css:459-461` — `.auth-error` reuses `var(--danger-light)` / `var(--danger)` for its background/text. The same file also defines `--accent-light` / `--accent` (`style.css:13-14`), already used elsewhere (e.g. `.stat-delta-positive`) for positive/affirmative styling — the natural pair to model a new `.auth-success` class on, without inventing a new color.
- `app.py`'s `/login` route (`app.py:30-32`) is currently `GET`-only and takes no query parameters — there's no session/flash infrastructure (`app.secret_key` is unset, per `step-1-database-spec.md`'s open question), so a one-time message has to travel via a query string, not `flask.flash`.
- `tests/test_db.py` + `tests/conftest.py` — the `isolated_db` fixture (`tmp_path` + `monkeypatch.chdir`) already isolates DB state per test; no Flask `app`/`client` fixture exists yet in `conftest.py`.

## Scope

**In scope:**
- `POST /register` — server-side validation of `name`, `email`, `password`, `confirm_password`; insert into `users`; duplicate-email handling; redirect on success.
- Updating the `/register` route decorator to accept `GET` and `POST`.
- Adding a `confirm_password` field to `templates/register.html`, with server-side validation that it matches `password`.
- A one-time, display-only success message on `/login` after a successful registration redirect, passed via a query parameter — not a session/flash mechanism, and not authentication logic.
- The minimal change to the `/login` route needed to read that query parameter and pass a `success` value to `login.html` (still `GET`-only, still no auth — see Out of scope below).

**Out of scope:**
- Login persistence (`POST /login` handling credentials, session/`app.secret_key` setup) — belongs to a separate, not-yet-numbered login-persistence spec. `CLAUDE.md`'s roadmap and `step-1-database-spec.md` both originally grouped register+login under "Step 2," but this spec deliberately narrows to registration only, per explicit scoping decision. The `/login` route change described above is display-only plumbing for the success message, not login functionality.
- `/logout` — Step 3.
- `/profile` — Step 4.
- Any expense CRUD — Steps 7, 8, 9.
- Case-insensitive email uniqueness (SQLite's `UNIQUE` on `email` is case-sensitive as defined in Step 1) — not changed here; see Open Questions.

## Dependencies

**Depends on:** Step 1 (`database/db.py` — `get_db()`, `init_db()`, the `users` table and its `UNIQUE` constraint on `email`). Step 1 is already implemented.

**Blocks:** The deferred login-persistence spec (a user must be able to register before logging in), and indirectly Step 4 (`/profile`, which reads a logged-in user's row).

## Design

### Route table

| Route | Method(s) | Change |
|---|---|---|
| `/register` | `GET`, `POST` | was `GET`-only; add `methods=["GET", "POST"]` to the decorator |
| `/login` | `GET` | unchanged method; route body now reads a `registered` query param to show a success message — still no auth logic |

### Request/response behavior

- `GET /register` — unchanged: `render_template("register.html")`.
- `POST /register`:
  1. Read `name`, `email`, `password`, `confirm_password` from `request.form`.
  2. Validate (see Validation & Constraints). On any validation failure, re-render `register.html` with `error` set to a specific message — do not proceed to the insert.
  3. Hash the password with `generate_password_hash`.
  4. `INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)` via `get_db()`.
  5. On `sqlite3.IntegrityError` (duplicate `email`), re-render `register.html` with `error="An account with that email already exists."`.
  6. On success, `conn.commit()`, `conn.close()`, then `redirect(url_for("login", registered="1"))`.

  Validation order within step 2: required-fields check (now including `confirm_password`) → password length → password/confirm-password match → (DB layer) duplicate email. Each check short-circuits before the next runs.
- `GET /login`:
  - If the `registered` query param is present (`request.args.get("registered")`), render `login.html` with `success="Account created successfully. Please sign in."`.
  - Otherwise, unchanged: `render_template("login.html")`.

### Function skeleton

```python
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            return render_template("register.html", error="All fields are required.")

        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters.")

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match.")

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template("register.html", error="An account with that email already exists.")
        finally:
            conn.close()

        return redirect(url_for("login", registered="1"))

    return render_template("register.html")
```

```python
@app.route("/login")
def login():
    success = "Account created successfully. Please sign in." if request.args.get("registered") else None
    return render_template("login.html", success=success)
```

New imports needed at the top of `app.py`: `request`, `redirect`, `url_for` from `flask`; `sqlite3`; `generate_password_hash` from `werkzeug.security`; `get_db` from `database.db` (alongside the existing `init_db`, `seed_db` import).

### Template addition — `templates/register.html`

Add a `confirm_password` field between the existing `password` field and the submit button, matching the existing `.form-group` markup pattern exactly:

```html
<div class="form-group">
    <label for="confirm_password">Confirm password</label>
    <input type="password" id="confirm_password" name="confirm_password"
           class="form-input" placeholder="Re-enter your password"
           required>
</div>
```

### Template addition — `templates/login.html`

Add a `success` block mirroring the existing `error` block, immediately above it:

```html
{% if success %}
<div class="auth-success">{{ success }}</div>
{% endif %}

{% if error %}
<div class="auth-error">{{ error }}</div>
{% endif %}
```

### CSS addition — `static/css/style.css`

Add `.auth-success` next to the existing `.auth-error` rule (`style.css:459-467`), mirroring its structure (padding, border-radius, font-size, margin) but swapping the color pair to `--accent-light` / `--accent`. Note: `.auth-error`'s `border` uses a bare hex (`#f5c6c2`) not listed among `CLAUDE.md`'s two documented one-off colors — that's pre-existing, not something to copy. Use `var(--accent)` for the border here instead, staying within the variables-only rule:

```css
.auth-success {
    background: var(--accent-light);
    color: var(--accent);
    border: 1px solid var(--accent);
    border-radius: var(--radius-sm);
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    margin-bottom: 1.25rem;
}
```

## Validation & Constraints

- `name`, `email`, `password`, `confirm_password` are all required — empty or whitespace-only values (after `.strip()` for `name`/`email`) fail validation.
- `password` must be at least 8 characters — matches `register.html`'s existing placeholder text, enforced here for the first time.
- `password` and `confirm_password` must be equal (plain string equality — this is comparing two values the user just typed, not a secret against a stored hash, so no timing-safe comparison is warranted). Checked after the length check, before any DB access.
- `email` uniqueness is enforced at the DB layer only (the `UNIQUE` constraint from Step 1) — no separate pre-check query; the route catches the resulting `sqlite3.IntegrityError`.
- No format validation on `email` beyond the browser's native `type="email"` — the route does not re-validate email shape server-side, since there's no existing convention in this repo for it and inventing one isn't grounded in anything already here.

## Rules for implementation

- No ORM — raw `sqlite3` via `get_db()`, per `CLAUDE.md`.
- Parameterized queries only (`?` placeholders) — no string-built SQL, no exceptions.
- Hash passwords with `werkzeug.security.generate_password_hash`; never store or log plaintext.
- No new dependencies — everything needed (`werkzeug.security`, `sqlite3`) is already available per pinned `requirements.txt`.
- Keep the route in `app.py` — no blueprints, per `CLAUDE.md`'s single-file-app constraint.
- Double quotes for strings; no docstrings/type hints; match the existing plain style of `app.py`.
- Always `conn.close()` the connection opened in the route, including on the `IntegrityError` path (use `try`/`finally` as in the skeleton above).
- No `flask.flash` or session usage for the success message — `app.secret_key` is unset and setting it is explicitly deferred to the login-persistence spec; use a plain query parameter instead.
- All colors in the new `.auth-success` CSS rule come from existing `:root` variables (`--accent`, `--accent-light`, `--radius-sm`) — no new bare hex values, per `CLAUDE.md`'s CSS rule.

## Error handling expectations

- Missing `name`, `email`, `password`, or `confirm_password` → re-render `register.html` with `error="All fields are required."`; no DB write attempted.
- `password` shorter than 8 characters → re-render `register.html` with `error="Password must be at least 8 characters."`; no DB write attempted.
- `password` and `confirm_password` don't match → re-render `register.html` with `error="Passwords do not match."`; no DB write attempted.
- Duplicate `email` (DB-level `UNIQUE` violation) → catch `sqlite3.IntegrityError`, re-render `register.html` with `error="An account with that email already exists."`.
- Any other `sqlite3` error (e.g. malformed query) → let it propagate uncaught, per Step 1's precedent of not swallowing unexpected DB errors during development.

## Open questions — deliberately left out

- **Login persistence and session handling.** Deferred to a separate spec per this Step's explicit scoping decision — `POST /login` credential checking and `app.secret_key` are not addressed here. The `GET /login` change in this spec only reads a query parameter to show a success message; it adds no authentication behavior.
- **Query-param success message being re-triggerable by revisiting the URL.** Anyone can visit `/login?registered=1` directly and see the message — there's no one-time guarantee without session/flash support (out of scope, see above). Acceptable for a teaching project; a real flash mechanism can replace this once `app.secret_key` exists.
- **Case-insensitive email uniqueness.** The `users.email` column has a case-sensitive `UNIQUE` constraint (set in Step 1). `alice@x.com` and `Alice@x.com` would currently be treated as distinct accounts. Not changed here since it would mean revisiting the Step 1 schema; worth a follow-up if it becomes a real issue.
- **Server-side email format validation.** Left to the browser's `type="email"` for now — no existing pattern in this repo to extend for stricter server-side checks.
- **Rate limiting / CAPTCHA on registration.** No existing infrastructure for either; out of scope for a teaching project at this stage.

## Acceptance Criteria

- [ ] `GET /register` renders `register.html` with no `error`, unchanged from current behavior.
- [ ] `POST /register` with valid `name`, `email`, an 8+ character `password`, and a matching `confirm_password` inserts a new row into `users`.
- [ ] `POST /register` with a valid submission redirects to `/login?registered=1`.
- [ ] `GET /login?registered=1` renders `login.html` with `success="Account created successfully. Please sign in."` displayed via the new `.auth-success` block.
- [ ] `GET /login` without a `registered` query param renders `login.html` with no success message, unchanged from current behavior.
- [ ] The inserted row's `password_hash` is not equal to the plaintext `password` submitted.
- [ ] `POST /register` with an empty `name` re-renders `register.html` with `error="All fields are required."`.
- [ ] `POST /register` with an empty `email` re-renders `register.html` with `error="All fields are required."`.
- [ ] `POST /register` with an empty `password` re-renders `register.html` with `error="All fields are required."`.
- [ ] `POST /register` with a `password` shorter than 8 characters re-renders `register.html` with `error="Password must be at least 8 characters."`.
- [ ] `POST /register` with an empty `confirm_password` re-renders `register.html` with `error="All fields are required."`.
- [ ] `POST /register` with `password` and `confirm_password` that don't match re-renders `register.html` with `error="Passwords do not match."`, and no row is inserted.
- [ ] `POST /register` with an `email` that already exists in `users` re-renders `register.html` with `error="An account with that email already exists."` and does not create a duplicate row.
- [ ] No route in `app.py` other than `/register` and `/login` is modified by this Step, and `/login`'s only change is reading the `registered` query param for the success message — no auth logic added.
- [ ] All queries/inputs follow the Rules for implementation above, with no exceptions.
