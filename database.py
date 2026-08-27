import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import DATABASE_FILE


def get_connection(db_path=None):
    connection = sqlite3.connect(db_path or DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def _columns(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def _add_column(cursor, table, name, definition):
    if name not in _columns(cursor, table):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def initialize_database(db_path=None):
    connection = get_connection(db_path)
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gmail_id TEXT UNIQUE,
            sender TEXT,
            recipients TEXT,
            cc TEXT,
            subject TEXT,
            body TEXT,
            category TEXT,
            priority TEXT,
            received_at TEXT,
            processed_at TEXT
        )
    """)
    for name, definition in {
        "recipients": "TEXT",
        "cc": "TEXT",
        "body": "TEXT",
        "priority": "TEXT",
    }.items():
        _add_column(cursor, "emails", name, definition)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER,
            filename TEXT,
            saved_path TEXT,
            sha256 TEXT UNIQUE,
            mime_type TEXT,
            is_duplicate INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY(email_id) REFERENCES emails(id)
        )
    """)
    for name, definition in {
        "mime_type": "TEXT",
        "is_duplicate": "INTEGER DEFAULT 0",
    }.items():
        _add_column(cursor, "attachments", name, definition)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            message TEXT,
            emails_seen INTEGER DEFAULT 0,
            emails_processed INTEGER DEFAULT 0,
            attachments_saved INTEGER DEFAULT 0,
            duplicates_skipped INTEGER DEFAULT 0,
            started_at TEXT NOT NULL,
            finished_at TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attachments_email_id ON attachments(email_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attachments_filename ON attachments(filename)")
    connection.commit()
    connection.close()


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def email_exists(gmail_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM emails WHERE gmail_id = ?", (gmail_id,))
    result = cursor.fetchone()
    connection.close()
    return result


def save_email(gmail_id, sender, subject, category, received_at, processed_at,
               recipients="", cc="", body="", priority="normal"):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO emails
        (gmail_id, sender, recipients, cc, subject, body, category, priority, received_at, processed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (gmail_id, sender, recipients, cc, subject, body, category, priority, received_at, processed_at))
    connection.commit()
    email_id = cursor.lastrowid
    if not email_id:
        cursor.execute("SELECT id FROM emails WHERE gmail_id = ?", (gmail_id,))
        row = cursor.fetchone()
        email_id = row["id"] if row else None
    connection.close()
    return email_id


def attachment_exists(sha256):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM attachments WHERE sha256 = ?", (sha256,))
    result = cursor.fetchone()
    connection.close()
    return result


def save_attachment(email_id, filename, saved_path, sha256, created_at, mime_type="", is_duplicate=False):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO attachments
        (email_id, filename, saved_path, sha256, mime_type, is_duplicate, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (email_id, filename, saved_path, sha256, mime_type, int(is_duplicate), created_at))
    connection.commit()
    attachment_id = cursor.lastrowid
    connection.close()
    return attachment_id


def create_sync_run(status="running", message=""):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO sync_runs (status, message, started_at)
        VALUES (?, ?, ?)
    """, (status, message, utc_now_iso()))
    connection.commit()
    run_id = cursor.lastrowid
    connection.close()
    return run_id


def finish_sync_run(run_id, status, message="", emails_seen=0, emails_processed=0, attachments_saved=0, duplicates_skipped=0):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE sync_runs
        SET status = ?, message = ?, emails_seen = ?, emails_processed = ?,
            attachments_saved = ?, duplicates_skipped = ?, finished_at = ?
        WHERE id = ?
    """, (status, message, emails_seen, emails_processed, attachments_saved, duplicates_skipped, utc_now_iso(), run_id))
    connection.commit()
    connection.close()


def get_attachment_path(attachment_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT saved_path FROM attachments WHERE id = ?", (attachment_id,))
    row = cursor.fetchone()
    connection.close()
    return Path(row["saved_path"]) if row and row["saved_path"] else None
