from pathlib import Path

from config import DATABASE_FILE, DOWNLOAD_DIR
from database import get_connection, initialize_database


def query_all(sql, params=()):
    initialize_database()
    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def query_one(sql, params=()):
    initialize_database()
    conn = get_connection()
    row = conn.execute(sql, params).fetchone()
    conn.close()
    return row


def dashboard_stats():
    return {
        "total_emails": query_one("SELECT COUNT(*) c FROM emails")["c"],
        "emails_today": query_one("SELECT COUNT(*) c FROM emails WHERE date(processed_at) = date('now')")["c"],
        "total_attachments": query_one("SELECT COUNT(*) c FROM attachments")["c"],
        "duplicate_attachments": query_one("SELECT COALESCE(SUM(duplicates_skipped), 0) c FROM sync_runs")["c"],
        "categories": query_all("SELECT COALESCE(category, 'other') category, COUNT(*) count FROM emails GROUP BY category ORDER BY count DESC"),
        "recent_emails": query_all("""
            SELECT e.*, COUNT(a.id) attachment_count FROM emails e
            LEFT JOIN attachments a ON a.email_id = e.id
            GROUP BY e.id ORDER BY COALESCE(e.received_at, e.processed_at) DESC LIMIT 8
        """),
        "recent_attachments": query_all("""
            SELECT a.*, e.subject, e.sender, e.category FROM attachments a
            LEFT JOIN emails e ON e.id = a.email_id
            ORDER BY a.created_at DESC LIMIT 8
        """),
        "last_sync": query_one("SELECT * FROM sync_runs ORDER BY started_at DESC LIMIT 1"),
    }


def list_emails(q="", category="", page=1, per_page=25, sort="received_at", direction="desc"):
    allowed_sort = {"sender", "subject", "category", "received_at", "processed_at"}
    sort = sort if sort in allowed_sort else "received_at"
    direction = "ASC" if direction.lower() == "asc" else "DESC"
    clauses, params = [], []
    if q:
        like = f"%{q}%"
        clauses.append("(e.subject LIKE ? OR e.sender LIKE ? OR e.body LIKE ? OR e.category LIKE ?)")
        params.extend([like, like, like, like])
    if category:
        clauses.append("e.category = ?")
        params.append(category)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    total = query_one(f"SELECT COUNT(*) c FROM emails e {where}", params)["c"]
    offset = max(page - 1, 0) * per_page
    rows = query_all(f"""
        SELECT e.*, COUNT(a.id) attachment_count FROM emails e
        LEFT JOIN attachments a ON a.email_id = e.id
        {where}
        GROUP BY e.id ORDER BY e.{sort} {direction} LIMIT ? OFFSET ?
    """, params + [per_page, offset])
    return rows, total


def get_email(email_id):
    return query_one("SELECT * FROM emails WHERE id = ?", (email_id,))


def email_attachments(email_id):
    return query_all("SELECT * FROM attachments WHERE email_id = ? ORDER BY created_at DESC", (email_id,))


def list_attachments(category="", filename="", extension=""):
    clauses, params = [], []
    if category:
        clauses.append("e.category = ?")
        params.append(category)
    if filename:
        clauses.append("a.filename LIKE ?")
        params.append(f"%{filename}%")
    if extension:
        ext = extension if extension.startswith(".") else f".{extension}"
        clauses.append("LOWER(a.filename) LIKE ?")
        params.append(f"%{ext.lower()}")
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return query_all(f"""
        SELECT a.*, e.subject, e.sender, e.category FROM attachments a
        LEFT JOIN emails e ON e.id = a.email_id
        {where} ORDER BY a.created_at DESC
    """, params)


def search_emails(q):
    if not q:
        return []
    like = f"%{q}%"
    return query_all("""
        SELECT e.*, COUNT(a.id) attachment_count FROM emails e
        LEFT JOIN attachments a ON a.email_id = e.id
        WHERE e.subject LIKE ? OR e.sender LIKE ? OR e.body LIKE ? OR e.category LIKE ?
        GROUP BY e.id ORDER BY COALESCE(e.received_at, e.processed_at) DESC LIMIT 100
    """, (like, like, like, like))


def categories():
    return [row["category"] for row in query_all("SELECT DISTINCT category FROM emails WHERE category IS NOT NULL ORDER BY category")]


def attachment_download_path(attachment_id):
    row = query_one("SELECT saved_path FROM attachments WHERE id = ?", (attachment_id,))
    if not row or not row["saved_path"]:
        return None
    path = Path(row["saved_path"]).resolve()
    base = DOWNLOAD_DIR.resolve()
    if base not in path.parents and path != base:
        return None
    return path if path.exists() and path.is_file() else None
