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
