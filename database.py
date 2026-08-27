import sqlite3

from config import DATABASE_FILE


def get_connection():

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gmail_id TEXT UNIQUE,
            sender TEXT,
            subject TEXT,
            category TEXT,
            received_at TEXT,
            processed_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER,
            filename TEXT,
            saved_path TEXT,
            sha256 TEXT UNIQUE,
            created_at TEXT,
            FOREIGN KEY(email_id)
                REFERENCES emails(id)
        )
    """)

    connection.commit()
    connection.close()


def email_exists(gmail_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM emails WHERE gmail_id = ?",
        (gmail_id,)
    )

    result = cursor.fetchone()

    connection.close()

    return result


def save_email(
    gmail_id,
    sender,
    subject,
    category,
    received_at,
    processed_at
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO emails
        (
            gmail_id,
            sender,
            subject,
            category,
            received_at,
            processed_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        gmail_id,
        sender,
        subject,
        category,
        received_at,
        processed_at
    ))

    connection.commit()

    email_id = cursor.lastrowid

    connection.close()

    return email_id


def attachment_exists(sha256):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM attachments
        WHERE sha256 = ?
        """,
        (sha256,)
    )

    result = cursor.fetchone()

    connection.close()

    return result


def save_attachment(
    email_id,
    filename,
    saved_path,
    sha256,
    created_at
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO attachments
        (
            email_id,
            filename,
            saved_path,
            sha256,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        email_id,
        filename,
        saved_path,
        sha256,
        created_at
    ))

    connection.commit()

    connection.close()