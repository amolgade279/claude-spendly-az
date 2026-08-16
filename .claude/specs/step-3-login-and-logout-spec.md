# Step 3 — Login and Logout Spec (Spendly)

This spec defines the contract for `POST /login` (credential verification and session creation) and `GET /logout` (session teardown) — the two pieces of authentication `step-2-registration-spec.md` explicitly deferred. It is written against code already implemented and manually verified in this repo (branch `feature/login-and-logout`), so every decision below traces to what's actually in `app.py`, not a new proposal.

## Grounding

- `CLAUDE.md`'s Roadmap table lists Step 3 as `Logout ................... app.py:29 [placeholder]` only. `step-2-registration-spec.md`'s Open Questions section separately deferred login credential-checking and `app.secret_key` setup to "a separate, not-yet-numbered login-persistence spec." This spec deliberately merges both under Step 3 — see Scope below for why.
- `app.py` (current state) — `/login` was `GET`-only, rendering `login.html` with an optional `success` message from Step 2's `registered` query param; `/logout` was the literal placeholder `return "Logout — coming in Step 3"`.
- `templates/login.html` — the form already posts `email`, `password` to `/login` (`method="POST"`), and already has both `{% if success %}<div class="auth-success">` (added in Step 2) and `{% if error %}<div class="auth-error">` blocks — no template changes needed for this step.
- `database/db.py` (Step 1) — `users` table has `password_hash` (via `werkzeug.security.generate_password_hash`), looked up by `email`, which is `UNIQUE`.
- `step-1-database-spec.md`'s Open Questions flagged this exact gap: *"Flask session secret key. Not part of `db.py`... Flask sessions (needed for login/logout/profile to know who's signed in) won't work without one. One line to add in Step 2 — just don't want it to surprise you."* This step adds it (one step later than that note anticipated, since Step 2 was narrowed to registration only).
- `CLAUDE.md` Tech constraints — no new dependencies; `werkzeug.security` already provides `check_password_hash` (pinned `Werkzeug 3.1.6`); Flask's built-in `session` (signed cookie, no server-side store) needs nothing beyond `app.secret_key`.
- `app.py`'s `/profile` route is still the Step 4 placeholder (`"Profile page — coming in Step 4"`). **Amendment (2026-08-16):** manual testing surfaced that redirecting a successful login there shows the raw placeholder string, which reads as broken rather than "you're in." Redirecting to `/` (`landing`) instead gives a real page while `/profile` remains unbuilt — the spec below has been updated to match.
- `tests/conftest.py` — the session-scoped `app` fixture (backed by `pytest-flask`, already pinned) gives every test a `client` fixture for free; `tests/test_app.py` already exercises `/register` and the `registered` query param on `/login` this way.
- `templates/base.html` — the navbar's `.nav-links` block (`<a>Sign in</a>` / `<a class="nav-cta">Get started</a>`) is static HTML on every page, per `CLAUDE.md`'s note that this file is the shared shell for all templates. Flask's default Jinja context already injects `session` into every `render_template()` call (no explicit `session=...` needed in any route) — confirmed by testing `{% if session.user_id %}` directly in `base.html` without touching a single route.

## Scope

**In scope:**
- `POST /login` — verify `email`/`password` against the `users` table; on success, store the authenticated user's id in the session; on failure, re-render `login.html` with an error.
- `GET /logout` — clear the session and redirect to `/login`.
- Adding `app.secret_key` to `app.py` so Flask's `session` object works.
- **Amendment (2026-08-16):** `templates/base.html`'s navbar now reflects login state — "Profile" / "Log out" when `session.user_id` is set, "Sign in" / "Get started" otherwise. Originally deferred to Step 4 (see Open Questions history below), pulled forward after manual testing showed a logged-in user still seeing "Sign in" reads as broken, the same way the `/profile` redirect did.
- **Amendment (2026-08-16):** `GET`/`POST /login` and `GET`/`POST /register` now redirect an already-logged-in visitor (`session.user_id` set) straight to `/` (landing), instead of showing the login/register form again. This is the inverse of the deferred-to-Step-4 "protect private routes from anonymous visitors" item below — this one protects the public-only auth forms from an already-authenticated visitor, which is squarely part of what "login" means and isn't deferred.

**Out of scope:**
- Enforcing login on `/profile` or any `/expenses/*` route (i.e. redirecting anonymous visitors away) — belongs to Step 4, where `/profile` first needs `session["user_id"]` to render anything real. Named here so it reads as a deferred decision, not a missed one.
- Loading `app.secret_key` from an environment variable / `.env` — `.env` is reserved but unused (`CLAUDE.md`), and no dependency-free mechanism exists yet to read it (`python-dotenv` isn't pinned). See Open Questions.
- "Remember me" / persistent sessions, password reset, account lockout after failed attempts — no existing infrastructure or roadmap mention for any of these.

## Dependencies

**Depends on:** Step 1 (`database/db.py` — `get_db()`, the `users` table and its `password_hash` column), Step 2 (`/register` — a user must exist to log in; `login.html`'s existing `success`/`error` blocks).

**Blocks:** Step 4 (`/profile` needs `session["user_id"]` to know which user to load), and indirectly Steps 7–9 (expense CRUD needs to know the current user).

## Design

### Route table

| Route | Method(s) | Change |
|---|---|---|
| `/login` | `GET`, `POST` | was `GET`-only; guard clause added for an already-logged-in visitor; `POST` branch added for credential verification |
| `/register` | `GET`, `POST` | unchanged methods; guard clause added for an already-logged-in visitor |
| `/logout` | `GET` | was a placeholder string; now clears session and redirects |

### Request/response behavior

- `GET`/`POST /login` and `GET`/`POST /register` — **first**, before any other logic: if `session.get("user_id")` is truthy, `redirect(url_for("landing"))` immediately. An already-authenticated visitor never sees either form, regardless of method.
- `POST /login` (only reached if not already logged in):
  1. Read `email`, `password` from `request.form` (`email` stripped, matching `/register`'s convention; `password` read as-is since whitespace could be a real character in a password).
  2. `SELECT * FROM users WHERE email = ?` via `get_db()`; close the connection immediately after the fetch (no writes on this path).
  3. If no row matches, or `check_password_hash(user["password_hash"], password)` is `False`, re-render `login.html` with `error="Invalid email or password."`. Deliberately one generic message for both "no such email" and "wrong password" — see Validation & Constraints.
  4. On success, set `session["user_id"] = user["id"]`, then `redirect(url_for("landing"))`.
- `GET /logout`:
  1. `session.pop("user_id", None)` — safe to call even if no session exists.
  2. `redirect(url_for("login"))`.
- `GET /login` (only reached if not already logged in; unchanged from Step 2): still reads the `registered` query param for the post-registration success message.

### Function skeleton

```python
app.secret_key = "spendly-dev-secret-key"
```

```python
@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        ...  # unchanged validation/insert logic from step-2-registration-spec.md

    return render_template("register.html")
```

```python
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if not user or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = user["id"]
        return redirect(url_for("landing"))

    success = "Account created successfully. Please sign in." if request.args.get("registered") else None
    return render_template("login.html", success=success)
```

```python
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))
```

New imports needed at the top of `app.py`: `session` from `flask` (alongside the existing `redirect`, `render_template`, `request`, `url_for`); `check_password_hash` from `werkzeug.security` (alongside the existing `generate_password_hash`).

Placement: both routes stay in the existing "Routes" banner section, directly after `/register` — not under "Placeholder routes," since neither is a stub once this step lands. `/logout` moves out from under the placeholder banner it currently sits under.

### Template change — `templates/base.html` (amendment)

Flask injects `session` into every template's context automatically (no route change needed) — `{% if session.user_id %}` works in `base.html` as-is. Replace the nav-links block:

```html
<div class="nav-links">
    {% if session.user_id %}
    <a href="{{ url_for('profile') }}">Profile</a>
    <a href="{{ url_for('logout') }}" class="nav-cta">Log out</a>
    {% else %}
    <a href="{{ url_for('login') }}">Sign in</a>
    <a href="{{ url_for('register') }}" class="nav-cta">Get started</a>
    {% endif %}
</div>
```

Reuses the existing `.nav-links a` / `.nav-cta` classes as-is — no new CSS needed, since the logged-in state is just a different pair of links in the same two visual slots (plain link + CTA-styled button).

## Validation & Constraints

- `email` and `password` are read from the form but not individually validated for presence before the DB lookup — an empty `email` simply won't match any row, and an empty `password` simply won't verify against any real hash, so both naturally fall into the same "Invalid email or password." path without a separate required-fields check. This differs from `/register`'s explicit required-fields check because there's no separate message to show either way.
- The failure message is intentionally the same whether the email doesn't exist or the password is wrong — revealing "no account with that email" would let an attacker enumerate registered addresses. Not stated elsewhere in this repo, but consistent with `password_hash` never being logged or exposed.
- Password comparison uses `werkzeug.security.check_password_hash`, which is a timing-safe comparison against the stored hash — unlike `/register`'s `password == confirm_password` check (comparing two values the user just typed, not a secret).
- `session["user_id"]` stores only the integer id — never the row, the email, or the password hash.

## Rules for implementation

- No ORM — raw `sqlite3` via `get_db()`, per `CLAUDE.md`.
- Parameterized queries only (`?` placeholders) — no string-built SQL, no exceptions.
- Verify passwords with `werkzeug.security.check_password_hash` exclusively — never compare `password` to `password_hash` directly, never re-hash-and-compare manually.
- No new dependencies — `werkzeug.security` and Flask's `session` are both already available per pinned `requirements.txt`.
- Keep both routes in `app.py` — no blueprints, per `CLAUDE.md`'s single-file-app constraint.
- Double quotes for strings; no docstrings/type hints; match the existing plain style of `app.py`.
- Always `conn.close()` the connection opened in `/login`, on every path (there's no write/`IntegrityError` branch here, so a plain `conn.close()` after the fetch is enough — no `try`/`finally` needed, unlike `/register`'s insert path).
- `app.secret_key` is a hardcoded string for now, not read from `.env` — see Open Questions for why, and don't treat this as license to hardcode other credentials elsewhere in the app.

## Error handling expectations

- No user with the submitted `email` → re-render `login.html` with `error="Invalid email or password."`; no session set.
- User exists but `password` doesn't verify against `password_hash` → same message, same non-branching behavior.
- Any other `sqlite3` error (e.g. malformed query) → let it propagate uncaught, per Step 1's precedent of not swallowing unexpected DB errors during development.
- `GET /logout` when no one is logged in (no `session["user_id"]`) → still succeeds (`session.pop(..., None)` is a no-op) and redirects to `/login`; not an error case.

## Open questions — deliberately left out

- **`app.secret_key` is a hardcoded literal, not loaded from `.env`.** `CLAUDE.md` reserves `.env` for future secrets but no dependency-free way exists yet to load it (`python-dotenv` isn't pinned, and Flask only auto-loads `.env` when that package is present). Acceptable for a dev-only teaching project (`debug=True`, per `CLAUDE.md`'s Tech constraints); revisit if this app is ever deployed anywhere the cookie-signing key needs to be a real secret.
- **No route protection yet.** `/profile` and every `/expenses/*` route are reachable by anyone regardless of `session["user_id"]` — this step makes the session exist and the navbar reflect it, but doesn't gate any route on it. Deferred to Step 4, where a shared "must be logged in" check naturally belongs since that's the first route that needs to read the current user's data.
- **No "remember me," lockout, or rate limiting on failed logins.** No existing infrastructure for any of these; out of scope for a teaching project at this stage.
- **Successful login redirects to `/` (landing), not `/profile`.** Originally specced as `/profile` (the semantically correct "you're in" destination), but amended after manual testing showed the raw `/profile` placeholder string reads as broken. Revisit once Step 4 builds a real `/profile` page — redirecting there will then be the better choice again.

## Acceptance Criteria

- [ ] `GET /login` renders `login.html` with no `error`, unchanged from current behavior.
- [ ] `POST /login` with an email that exists and the correct password sets `session["user_id"]` to that user's id.
- [ ] `POST /login` with an email that exists and the correct password redirects to `/`.
- [ ] `POST /login` with an email that does not exist in `users` re-renders `login.html` with `error="Invalid email or password."`.
- [ ] `POST /login` with an existing email and an incorrect password re-renders `login.html` with `error="Invalid email or password."`.
- [ ] `POST /login` never sets `session["user_id"]` on a failed attempt.
- [ ] `GET /logout` clears `session["user_id"]` when a session exists.
- [ ] `GET /logout` redirects to `/login`.
- [ ] `GET /logout` succeeds (no error) when called with no active session.
- [ ] With no active session, any page's navbar shows "Sign in" and "Get started," not "Profile" or "Log out."
- [ ] After a successful login, any page's navbar shows "Profile" and "Log out," not "Sign in" or "Get started."
- [ ] `GET /login` with an active session redirects to `/`, without rendering `login.html`.
- [ ] `GET /register` with an active session redirects to `/`, without rendering `register.html`.
- [ ] No route in `app.py` other than `/login`, `/register`, and `/logout` is modified by this Step.
- [ ] All queries/inputs follow the Rules for implementation above, with no exceptions.
