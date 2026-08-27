import sqlite3

from attachment_manager import calculate_sha256, safe_filename
from classifier import classify_email
from database import initialize_database, get_connection
from app.repository import search_emails


def test_classification_uses_metadata_and_attachments():
    assert classify_email("GitHub <noreply@github.com>", "New pull request", "", []) == "github"
    assert classify_email("Teacher", "Weekly update", "assignment due", ["syllabus.pdf"]) == "education"
    assert classify_email("Unknown", "Hello", "", []) == "other"


def test_safe_filename_removes_paths_and_unsafe_chars():
    assert safe_filename("../invoice:2026?.pdf") == "invoice_2026_.pdf"
    assert safe_filename("   ") == "attachment"


def test_sha256_generation():
    assert calculate_sha256(b"nexora") == "6684bd7ca5b118220b0b7f9996bc71c75359fec3242a3c8ce8a53e889081bf55"


def test_database_operations_and_duplicate_detection(tmp_path):
    db = tmp_path / "test.db"
    initialize_database(db)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO emails (gmail_id, sender, subject, body, category, processed_at) VALUES (?, ?, ?, ?, ?, datetime('now'))", ("g1", "a@example.com", "Invoice", "body", "finance"))
    conn.execute("INSERT INTO attachments (email_id, filename, saved_path, sha256, created_at) VALUES (1, 'a.pdf', '/tmp/a.pdf', 'hash1', datetime('now'))")
    conn.commit()
    assert conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0] == 1
    assert conn.execute("SELECT id FROM attachments WHERE sha256 = ?", ("hash1",)).fetchone()[0] == 1
    conn.close()


def test_search_queries_are_parameterized(monkeypatch, tmp_path):
    import config
    import database
    import app.repository as repo

    db = tmp_path / "search.db"
    monkeypatch.setattr(config, "DATABASE_FILE", db)
    monkeypatch.setattr(database, "DATABASE_FILE", db)
    monkeypatch.setattr(repo, "DATABASE_FILE", db)
    initialize_database(db)
    conn = get_connection(db)
    conn.execute("INSERT INTO emails (gmail_id, sender, subject, body, category, processed_at) VALUES (?, ?, ?, ?, ?, datetime('now'))", ("g1", "school@example.com", "Class", "science notes", "education"))
    conn.commit()
    conn.close()
    results = search_emails("science")
    assert len(results) == 1
    assert results[0]["category"] == "education"
