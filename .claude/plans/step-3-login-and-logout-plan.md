# Implementation Plan — Step 3 Login and Logout (Spendly)

## Context

`.claude/specs/step-3-login-and-logout-spec.md` is the committed contract for `POST /login` (credential verification, session creation) and `GET /logout` (session teardown) — the authentication piece `step-2-registration-spec.md` deferred, now merged into `CLAUDE.md`'s Step 3 (originally labeled "Logout" only). This plan turns that spec into concrete file edits.

Verified current state (read directly, no drift from spec assumptions):
- `app.py` — the route logic in the spec's Design section is **already implemented and manually verified** (via ad hoc `test_client()` scripts, not pytest) on branch `feature/login-and-logout`: `app.secret_key` is set, `session` and `check_password_hash` are imported, `/login` accepts `GET`/`POST` with the exact branching the spec describes, `/logout` clears the session and redirects. `/logout` has already been moved out from under the "Placeholder routes" banner into the main "Routes" section, directly after `/login`.
- `templates/login.html` — already has both `{% if success %}` and `{% if error %}` blocks (from Step 2); no template change needed for this step, confirmed by re-reading the file.
- `tests/conftest.py` — the session-scoped `app` fixture (and the `client` fixture it gives every test via `pytest-flask`) already exists from Step 2; nothing to add here.
- `tests/test_app.py` — 13 tests exist, all for `/register` and the `registered` query param on `/login`. **No tests exist yet for `POST /login` credential checking or `GET /logout`** — this is the only gap between the spec and the repo's current state, and what this plan adds.
- `tests/test_db.py` — 6 tests, unrelated to this step, unaffected.

Every design decision below traces to the spec — no scope has been added or removed. The only work this plan actually schedules is the automated test suite proving the spec's Acceptance Criteria against the code that's already there.

**Amendment (2026-08-16):** manual testing on the dev server (`python app.py`) surfaced that a successful login redirected to `/profile`, which is still the raw Step 4 placeholder string (`"Profile page — coming in Step 4"`) — this reads as a broken page, not a successful login. The spec was updated first to change the redirect target to `/` (`landing`), and this plan/tests below are updated to match. Steps 1-3 below (originally covering `app.py`, the 8 new tests, and the full pytest run) were already carried out once against the old `/profile` target; this amendment redoes the `app.py` redirect line and the two tests that asserted on it.

## Step 1 — `app.py`: change the post-login redirect target

Everything else in the spec's Design section is already implemented and unaffected by this amendment (session, `check_password_hash`, `/logout`). The one line to change, per the amended spec:

```python
        session["user_id"] = user["id"]
        return redirect(url_for("landing"))
```

(was `return redirect(url_for("profile"))`)

## Step 2 — `tests/test_app.py`: add tests covering the spec's Acceptance Criteria

Add alongside the existing 13 tests (same file, same style — `client` fixture; reuse the seeded `demo@example.com` / `Password123` user already inserted by `seed_db()` for the valid-login cases, matching how the existing duplicate-email test already relies on that same seeded row):

1. `test_get_login_renders_without_error` — GET `/login` → 200, `b"auth-error"` not in body. (AC1)
2. `test_post_login_valid_credentials_sets_session_user_id` — POST `demo@example.com` / `Password123` → inspect `client.session_transaction()`, assert `session["user_id"]` is set and matches the demo user's `id` (looked up via `get_db()`). (AC2)
3. `test_post_login_valid_credentials_redirects_to_landing` — same POST, `follow_redirects=False` → 302, `resp.headers["Location"].endswith("/")`. **(AC3, amended — was `test_post_login_valid_credentials_redirects_to_profile` asserting `/profile`.)**
4. `test_post_login_nonexistent_email_shows_invalid_error` — POST with an email not in `users` → 200, `b"Invalid email or password."` in body; then `client.session_transaction()` confirms `session.get("user_id")` is `None`. (AC4, AC6)
5. `test_post_login_wrong_password_shows_invalid_error` — POST `demo@example.com` with a wrong password → 200, `b"Invalid email or password."` in body; session confirmed empty as in test 4. (AC5, AC6)
6. `test_get_logout_clears_session` — log in first (POST valid credentials), then GET `/logout`; `client.session_transaction()` confirms `session.get("user_id")` is `None` afterward. (AC7)
7. `test_get_logout_redirects_to_login` — GET `/logout`, `follow_redirects=False` → 302, `resp.headers["Location"].endswith("/login")`. (AC8)
8. `test_get_logout_without_active_session_succeeds` — GET `/logout` with no prior login on a fresh client → 302 to `/login`, no exception. (AC9)

AC10 ("no route other than `/login`/`/logout` modified") and AC11 ("Rules for implementation followed") aren't independently testable — they're satisfied by this plan touching only `tests/test_app.py` (Step 1 needed no edit) and by the `app.py` code already using parameterized queries and `check_password_hash` per the spec's Design section.

## Step 3 — Run the full suite

`pytest` from repo root — expect 21 tests in `test_app.py` (13 existing + 8 new) + 6 in `test_db.py` = 27 total, all passing.

## Step 4 — Manual verification (dev server)

Re-confirm on the actual dev server after this amendment:
- `python app.py`, visit `/login`, sign in with `demo@example.com` / `Password123` → lands on `/` (landing page), not the `/profile` placeholder.
- Visit `/logout` → redirected to `/login`.
- Attempt login with a wrong password → "Invalid email or password." shown, form re-rendered.

## Step 5 — `templates/base.html`: reflect login state in the navbar (amendment)

Manual testing after the redirect-target fix showed the navbar still saying "Sign in" / "Get started" while logged in. Pulled forward from Step 4 into this Step's scope, per the amended spec. No route change needed — Flask injects `session` into every template automatically.

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

## Step 6 — `tests/test_app.py`: add 2 tests for the navbar

1. `test_navbar_shows_signin_when_logged_out` — GET `/` on a fresh client → `b"Sign in"` in body, `b"Log out"` not in body.
2. `test_navbar_shows_logout_when_logged_in` — log in first (POST valid credentials), then GET `/` → `b"Log out"` in body, `b"Sign in"` not in body.

## Step 7 — `app.py`: redirect an already-logged-in visitor away from `/login` and `/register` (amendment)

Manual testing showed that typing `/login` or `/register` in the URL bar while already logged in still displayed the form. Per the amended spec, add a guard clause as the first line of each route body:

```python
@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        ...  # unchanged
```

```python
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        ...  # unchanged
```

No new imports — `session`, `redirect`, `url_for` are already imported.

## Step 8 — `tests/test_app.py`: add 2 tests for the auth-form guard

1. `test_get_login_when_already_logged_in_redirects_to_landing` — log in first, then GET `/login`, `follow_redirects=False` → 302, `resp.headers["Location"].endswith("/")`.
2. `test_get_register_when_already_logged_in_redirects_to_landing` — log in first, then GET `/register`, `follow_redirects=False` → 302, `resp.headers["Location"].endswith("/")`.

## Execution order

1. `app.py` — redirect target fix (Step 1 amendment) + already-logged-in guard on `/login`/`/register` (Step 7 amendment).
2. `tests/test_app.py` (Steps 2, 6, 8) — login/logout tests, navbar tests, auth-guard tests.
3. `templates/base.html` (Step 5) — navbar login-state change.
4. `pytest` (Step 3) — confirm 31/31 pass.
5. Manual dev-server check (Step 4) — final sanity pass.

## Files touched

- `app.py`
- `templates/base.html`
- `tests/test_app.py`

(`templates/login.html`, `templates/register.html`, `tests/conftest.py` are unchanged by this plan — already done in the prior implementation pass.)

## Verification

- `pytest` from repo root — 31/31 tests pass (19 pre-existing + 8 login/logout + 2 navbar + 2 auth-guard).
- Manual dev-server walkthrough per Step 4.

## Status

**Implementation** (2026-08-16): `app.py` changes (session, `check_password_hash`, `/login` POST branch, `/logout`) implemented; 8 tests added to `tests/test_app.py` — `pytest` 27/27 passed.

**Amendment 1** (2026-08-16, redirect target): manual dev-server testing showed `/profile`'s placeholder string on login instead of a real page. Spec, `app.py`, and the two affected tests updated to redirect to `/` (landing) instead — `pytest` re-run, 27/27 passed.

**Amendment 2** (2026-08-16, navbar login state): manual testing after Amendment 1 showed the navbar still read "Sign in" / "Get started" while logged in. Pulled forward from Step 4 into this Step's scope per the amended spec — `templates/base.html` updated, 2 tests added.

**Amendment 3** (2026-08-16, auth-form guard): manual testing after Amendment 2 showed an already-logged-in visitor could still reach `/login` or `/register` and see the form. Guard clause added to both routes per the amended spec — `pytest` re-run, 31/31 passed.
