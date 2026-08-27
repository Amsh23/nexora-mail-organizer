from datetime import datetime

from config import (
    DOWNLOAD_DIR,
    MAX_EMAILS
)

from gmail_client import (
    authenticate,
    list_messages,
    get_message,
    get_header,
    get_email_date,
    get_body,
    extract_attachments,
    download_attachment
)

from classifier import classify_email

from attachment_manager import (
    save_attachment_file
)

from database import (
    initialize_database,
    email_exists,
    save_email,
    attachment_exists,
    save_attachment
)


def process_email(
    service,
    message_id,
    dry_run=False
):

    message = get_message(
        service,
        message_id
    )

    payload = message.get(
        "payload",
        {}
    )

    headers = payload.get(
        "headers",
        []
    )

    sender = get_header(
        headers,
        "From"
    )

    subject = get_header(
        headers,
        "Subject"
    )

    received_at = get_email_date(
        headers
    )

    body = get_body(
        payload
    )

    category = classify_email(
        sender,
        subject,
        body
    )

    attachments = extract_attachments(
        payload
    )

    print()
    print("=" * 70)

    print(
        f"From: {sender}"
    )

    print(
        f"Subject: {subject}"
    )

    print(
        f"Category: {category}"
    )

    print(
        f"Attachments: {len(attachments)}"
    )

    if dry_run:

        print(
            "DRY RUN → no files will be changed"
        )

        return

    processed_at = datetime.now().isoformat()

    email_id = save_email(
        gmail_id=message_id,
        sender=sender,
        subject=subject,
        category=category,
        received_at=received_at,
        processed_at=processed_at
    )

    if not email_id:

        print(
            "Email already processed."
        )

        return

    for attachment in attachments:

        filename = attachment[
            "filename"
        ]

        attachment_id = attachment[
            "attachment_id"
        ]

        data = attachment[
            "data"
        ]

        try:

            if attachment_id:

                data = download_attachment(
                    service,
                    message_id,
                    attachment_id
                )

            elif data:

                import base64

                data = base64.urlsafe_b64decode(
                    data
                )

            else:

                print(
                    f"Could not download: {filename}"
                )

                continue

            destination, file_hash = (
                save_attachment_file(
                    data=data,
                    filename=filename,
                    base_directory=DOWNLOAD_DIR,
                    category=category
                )
            )

            existing = attachment_exists(
                file_hash
            )

            if existing:

                print(
                    f"Duplicate skipped: {filename}"
                )

                continue

            save_attachment(
                email_id=email_id,
                filename=filename,
                saved_path=str(destination),
                sha256=file_hash,
                created_at=processed_at
            )

            print(
                f"Saved: {destination}"
            )

        except Exception as error:

            print(
                f"Attachment error: {error}"
            )


def main(dry_run=False):

    print()
    print(
        "======================================"
    )

    print(
        "       NEXORA MAIL ORGANIZER"
    )

    print(
        "======================================"
    )

    initialize_database()

    service = authenticate()

    messages = list_messages(
        service,
        MAX_EMAILS
    )

    print(
        f"\nFound {len(messages)} emails."
    )

    if dry_run:

        print(
            "DRY RUN MODE ENABLED"
        )

    for message in messages:

        try:

            process_email(
                service,
                message["id"],
                dry_run=dry_run
            )

        except Exception as error:

            print(
                f"Error processing email: {error}"
            )

    print()
    print(
        "Finished."
    )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without saving anything"
    )

    args = parser.parse_args()

    main(
        dry_run=args.dry_run
    )