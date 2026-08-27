import base64
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from attachment_manager import calculate_sha256, save_attachment_file, safe_filename
from classifier import classify_email
from config import DOWNLOAD_DIR, MAX_EMAILS
from database import (
    attachment_exists,
    create_sync_run,
    email_exists,
    finish_sync_run,
    initialize_database,
    save_attachment,
    save_email,
)
from gmail_client import (
    authenticate,
    download_attachment,
    extract_attachments,
    get_body,
    get_email_date,
    get_header,
    get_message,
    list_messages,
)

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    emails_seen: int = 0
    emails_processed: int = 0
    attachments_saved: int = 0
    duplicates_skipped: int = 0
    errors: int = 0


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def process_email(service, message_id, dry_run=False):
    message = get_message(service, message_id)
    payload = message.get("payload", {})
    headers = payload.get("headers", [])
    sender = get_header(headers, "From")
    recipients = get_header(headers, "To")
    cc = get_header(headers, "Cc")
    subject = get_header(headers, "Subject")
    received_at = get_email_date(headers)
    body = get_body(payload)
    attachments = extract_attachments(payload)
    category = classify_email(sender, subject, body, [a.get("filename", "") for a in attachments])

    logger.info("Processing email gmail_id=%s category=%s attachments=%s", message_id, category, len(attachments))
    print("\n" + "=" * 70)
    print(f"From: {sender}")
    print(f"Subject: {subject}")
    print(f"Category: {category}")
    print(f"Attachments: {len(attachments)}")

    result = SyncResult(emails_seen=1)
    if dry_run:
        print("DRY RUN → no files will be changed")
        return result

    if email_exists(message_id):
        print("Email already processed.")
        return result

    processed_at = utc_now_iso()
    email_id = save_email(
        gmail_id=message_id,
        sender=sender,
        recipients=recipients,
        cc=cc,
        subject=subject,
        body=body,
        category=category,
        priority="normal",
        received_at=received_at,
        processed_at=processed_at,
    )
    result.emails_processed = 1

    for attachment in attachments:
        filename = safe_filename(attachment.get("filename", "attachment"))
        try:
            attachment_id = attachment.get("attachment_id")
            data = attachment.get("data")
            if attachment_id:
                data = download_attachment(service, message_id, attachment_id)
            elif data:
                data = base64.urlsafe_b64decode(data)
            else:
                logger.warning("Attachment missing data gmail_id=%s filename=%s", message_id, filename)
                print(f"Could not download: {filename}")
                continue

            file_hash = calculate_sha256(data)
            if attachment_exists(file_hash):
                result.duplicates_skipped += 1
                logger.info("Duplicate attachment skipped filename=%s sha256=%s", filename, file_hash)
                print(f"Duplicate skipped: {filename}")
                continue

            destination, file_hash = save_attachment_file(data, filename, DOWNLOAD_DIR, category)
            save_attachment(
                email_id=email_id,
                filename=filename,
                saved_path=str(destination),
                sha256=file_hash,
                mime_type=attachment.get("mime_type", ""),
                created_at=processed_at,
            )
            result.attachments_saved += 1
            logger.info("Attachment saved path=%s", destination)
            print(f"Saved: {destination}")
        except Exception as error:
            result.errors += 1
            logger.exception("Attachment error gmail_id=%s filename=%s", message_id, filename)
            print(f"Attachment error: {error}")
    return result


def run_sync(max_emails=MAX_EMAILS, dry_run=False):
    initialize_database()
    run_id = None if dry_run else create_sync_run("running", "Gmail sync started")
    result = SyncResult()
    try:
        logger.info("Gmail sync started dry_run=%s max_emails=%s", dry_run, max_emails)
        service = authenticate()
        messages = list_messages(service, max_emails)
        result.emails_seen = len(messages)
        print(f"\nFound {len(messages)} emails.")
        if dry_run:
            print("DRY RUN MODE ENABLED")
        for message in messages:
            try:
                email_result = process_email(service, message["id"], dry_run=dry_run)
                result.emails_processed += email_result.emails_processed
                result.attachments_saved += email_result.attachments_saved
                result.duplicates_skipped += email_result.duplicates_skipped
                result.errors += email_result.errors
            except Exception as error:
                result.errors += 1
                logger.exception("Error processing email id=%s", message.get("id"))
                print(f"Error processing email: {error}")
        status = "success" if result.errors == 0 else "completed_with_errors"
        if run_id:
            finish_sync_run(run_id, status, "Sync finished", result.emails_seen, result.emails_processed, result.attachments_saved, result.duplicates_skipped)
        logger.info("Sync finished status=%s", status)
        return result
    except Exception as error:
        logger.exception("Gmail sync failed")
        if run_id:
            finish_sync_run(run_id, "failed", str(error), result.emails_seen, result.emails_processed, result.attachments_saved, result.duplicates_skipped)
        raise
