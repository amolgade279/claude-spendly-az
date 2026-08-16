import sqlite3

import pytest
from werkzeug.security import check_password_hash

from database.db import get_db, init_db, seed_db


def test_init_db_creates_tables_and_indexes(isolated_db):
    init_db()
    conn = get_db()

    tables = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert "users" in tables
    assert "expenses" in tables

    indexes = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()}
    assert "idx_expenses_user_id" in indexes
    assert "idx_expenses_user_date" in indexes

    conn.close()


def test_category_check_constraint(isolated_db):
    init_db()
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User", "test@example.com", "hash"),
    )
    conn.commit()
    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("test@example.com",)
    ).fetchone()[0]

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
            (user_id, 10.0, "NotACategory", "2026-08-01"),
        )

    conn.close()


def test_seed_db_inserts_demo_user_and_expenses(isolated_db):
    init_db()
    seed_db()
    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", ("demo@example.com",)
    ).fetchone()
    assert user is not None
    assert user["password_hash"] != "Password123"
    assert check_password_hash(user["password_hash"], "Password123")

    expense_count = conn.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user["id"],)
    ).fetchone()[0]
    assert expense_count == 8

    conn.close()


def test_seed_db_is_idempotent(isolated_db):
    init_db()
    seed_db()
    seed_db()
    conn = get_db()

    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    expense_count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    assert user_count == 1
    assert expense_count == 8

    conn.close()


def test_duplicate_email_raises_integrity_error(isolated_db):
    init_db()
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("User One", "dup@example.com", "hash1"),
    )
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("User Two", "dup@example.com", "hash2"),
        )

    conn.close()


def test_bogus_user_id_raises_integrity_error(isolated_db):
    init_db()
    conn = get_db()

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
            (9999, 10.0, "Food", "2026-08-01"),
        )

    conn.close()
