import itertools

from database.db import get_db

_email_counter = itertools.count()


def _unique_email():
    return "test-user-{}@example.com".format(next(_email_counter))


def test_get_register_renders_without_error(client):
    resp = client.get("/register")
    assert resp.status_code == 200
    assert b"auth-error" not in resp.data


def test_post_register_valid_inserts_new_user(client):
    email = _unique_email()
    client.post("/register", data={
        "name": "New User",
        "email": email,
        "password": "Password123",
        "confirm_password": "Password123",
    })

    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    assert row is not None


def test_post_register_valid_redirects_to_login_with_registered_param(client):
    resp = client.post("/register", data={
        "name": "New User",
        "email": _unique_email(),
        "password": "Password123",
        "confirm_password": "Password123",
    })

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login?registered=1")


def test_get_login_with_registered_param_shows_success_message(client):
    resp = client.get("/login?registered=1")
    assert resp.status_code == 200
    assert b"Account created successfully. Please sign in." in resp.data
    assert b"auth-success" in resp.data


def test_get_login_without_registered_param_shows_no_success_message(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"auth-success" not in resp.data


def test_post_register_stores_hashed_password_not_plaintext(client):
    email = _unique_email()
    password = "Password123"
    client.post("/register", data={
        "name": "New User",
        "email": email,
        "password": password,
        "confirm_password": password,
    })

    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    assert row["password_hash"] != password


def test_post_register_missing_name_shows_required_error(client):
    resp = client.post("/register", data={
        "name": "",
        "email": _unique_email(),
        "password": "Password123",
        "confirm_password": "Password123",
    })

    assert resp.status_code == 200
    assert b"All fields are required." in resp.data


def test_post_register_missing_email_shows_required_error(client):
    resp = client.post("/register", data={
        "name": "New User",
        "email": "",
        "password": "Password123",
        "confirm_password": "Password123",
    })

    assert resp.status_code == 200
    assert b"All fields are required." in resp.data


def test_post_register_missing_password_shows_required_error(client):
    resp = client.post("/register", data={
        "name": "New User",
        "email": _unique_email(),
        "password": "",
        "confirm_password": "Password123",
    })

    assert resp.status_code == 200
    assert b"All fields are required." in resp.data


def test_post_register_missing_confirm_password_shows_required_error(client):
    resp = client.post("/register", data={
        "name": "New User",
        "email": _unique_email(),
        "password": "Password123",
        "confirm_password": "",
    })

    assert resp.status_code == 200
    assert b"All fields are required." in resp.data


def test_post_register_short_password_shows_length_error(client):
    resp = client.post("/register", data={
        "name": "New User",
        "email": _unique_email(),
        "password": "short1",
        "confirm_password": "short1",
    })

    assert resp.status_code == 200
    assert b"Password must be at least 8 characters." in resp.data


def test_post_register_mismatched_confirm_password_shows_error(client):
    email = _unique_email()
    resp = client.post("/register", data={
        "name": "New User",
        "email": email,
        "password": "Password123",
        "confirm_password": "Different123",
    })

    assert resp.status_code == 200
    assert b"Passwords do not match." in resp.data

    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    assert row is None


def test_post_register_duplicate_email_shows_exists_error_without_duplicate_row(client):
    resp = client.post("/register", data={
        "name": "Another User",
        "email": "demo@example.com",
        "password": "Password123",
        "confirm_password": "Password123",
    })

    assert resp.status_code == 200
    assert b"An account with that email already exists." in resp.data

    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM users WHERE email = ?", ("demo@example.com",)
    ).fetchone()[0]
    conn.close()

    assert count == 1
