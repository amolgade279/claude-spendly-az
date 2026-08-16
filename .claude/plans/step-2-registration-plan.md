# Implementation Plan — Step 2 Registration (Spendly)

## Context

`.claude/specs/step-2-registration-spec.md` is the committed contract for making `POST /register` actually persist a user, plus a small display-only success message on `/login` after a successful registration redirect. Right now `/register` and `/login` in `app.py` are both GET-only stubs that just render their templates — no validation, no DB write, no redirect. This plan turns that spec into concrete file edits, in the order they need to happen, plus an automated test suite (confirmed in scope with the user) exercising every behavioral Acceptance Criterion in the spec.

**Amendment (2026-08-16):** manual testing of the first implementation surfaced a missing `confirm_password` field on the registration form. The spec was updated first to add it (new field, required, must match `password`, new `"Passwords do not match."` error), and this plan is updated to match. The `app.py`, `templates/login.html`, `static/css/style.css`, `tests/conftest.py` changes below were already implemented and verified once; this amendment adds the `confirm_password` field/validation and its template change and tests on top of that work.

Every design decision below traces to the spec — no scope has been added or removed. The one implementation detail the spec doesn't spell out (how to safely test a Flask app whose module runs `init_db()`/`seed_db()` at import time) is worked out here.

Verified current state (read directly, no drift from spec assumptions):
- `app.py`: imports `Flask, redirect, render_template, request, url_for` (flask), `generate_password_hash` (werkzeug.security), `get_db, init_db, seed_db` (database.db). `/register` accepts `GET`/`POST` and validates `name`/`email`/`password`; `/login` reads the `registered` query param. Both already implemented per the original (pre-amendment) version of this plan.
- `templates/register.html`: has `name`, `email`, `password` fields and the `{% if error %}` block. No `confirm_password` field yet — this is what's missing and what this amendment adds.
- `templates/login.html`: already has the `{% if success %}` block added.
- `static/css/style.css`: `.auth-success` already added next to `.auth-error`.
- `database/db.py`: `get_db()` / `users` table (`id, name, email UNIQUE, password_hash, created_at`) already implemented per Step 1. No schema change needed for `confirm_password` — it's never persisted, only compared against `password` in the route.
- `tests/conftest.py`: session-scoped `app` fixture already added (works around `app.py`'s module-level `init_db()`/`seed_db()` call — see Step 5 below for why).
- `tests/test_app.py`: already exists with 11 tests from the original implementation; this amendment adds 2 more.

## Step 1 — `app.py`: add `confirm_password` to the `/register` route body

Update the `POST /register` branch to read `confirm_password` and validate it, per the amended spec (lines 70-82):

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

Only the body of `register()` changes — no new imports needed (nothing beyond what's already imported), and `/login` is untouched by this amendment.

## Step 2 — `templates/register.html`: add the `confirm_password` field

Insert between the existing `password` field's closing `</div>` and the submit button, matching the existing `.form-group` markup pattern exactly (spec lines 114-121):

```html
<div class="form-group">
    <label for="confirm_password">Confirm password</label>
    <input type="password" id="confirm_password" name="confirm_password"
           class="form-input" placeholder="Re-enter your password"
           required>
</div>
```

## Step 3 — `tests/test_app.py`: add 2 tests for the new field

Add alongside the existing 11 tests (same file, same style — `client` fixture, `_unique_email()` helper already defined):

1. `test_post_register_missing_confirm_password_shows_required_error` — POST with valid `name`/`email`/`password` but `confirm_password=""` → 200, `"All fields are required."` in body.
2. `test_post_register_mismatched_confirm_password_shows_error` — POST with valid `name`/`email`, `password="Password123"`, `confirm_password="Different123"` → 200, `"Passwords do not match."` in body; then `get_db()` confirms no row was inserted for that email.

## Step 4 — Manual verification (dev server)

After automated tests pass, re-run the Step 6 manual walkthrough from the original plan, adding two new checks on `/register`:
- Submit with `confirm_password` left blank → confirm "All fields are required."
- Submit with `password`/`confirm_password` that don't match → confirm "Passwords do not match."
- Then confirm the existing valid-submission path (matching password/confirm_password) still redirects to `/login?registered=1` and shows the success banner as before.

## Execution order

1. `app.py` (Step 1) — route logic first.
2. `templates/register.html` (Step 2) — the field the route now expects.
3. `tests/test_app.py` (Step 3) — run `pytest`, confirm all tests (13 in `test_app.py` + 6 in `test_db.py` = 19) pass together.
4. Manual dev-server check (Step 4) — final sanity pass.

## Files touched (this amendment)

- `app.py`
- `templates/register.html`
- `tests/test_app.py`

(`templates/login.html`, `static/css/style.css`, `tests/conftest.py`, and `database/db.py` are unchanged by this amendment — already done in the original pass.)

## Verification

- `pytest` from repo root — 19/19 tests pass (17 from the original implementation + 2 new).
- Manual dev-server walkthrough per Step 4.

## Status

**Original implementation** (2026-08-16): `app.py`, `templates/login.html`, `static/css/style.css`, `tests/conftest.py`, `tests/test_app.py` (11 tests) implemented and verified — `pytest` 17/17 passed, manual curl walkthrough confirmed all behaviors.

**Amendment** (2026-08-16, confirm-password): spec updated first, plan updated to match — implementation of Steps 1-4 above not yet done.
