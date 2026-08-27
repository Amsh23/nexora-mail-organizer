import base64
import os
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import (
    SCOPES,
    TOKEN_FILE,
    CREDENTIALS_FILE
)


def authenticate():

    credentials = None

    if os.path.exists(TOKEN_FILE):

        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    if not credentials or not credentials.valid:

        if (
            credentials
            and credentials.expired
            and credentials.refresh_token
        ):

            credentials.refresh(
                Request()
            )

        else:

            flow = (
                InstalledAppFlow
                .from_client_secrets_file(
                    CREDENTIALS_FILE,
                    SCOPES
                )
            )

            credentials = flow.run_local_server(
                port=0
            )

        with open(
            TOKEN_FILE,
            "w"
        ) as token:

            token.write(
                credentials.to_json()
            )

    service = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    return service


def get_header(headers, name):

    for header in headers:

        if (
            header["name"].lower()
            == name.lower()
        ):

            return header["value"]

    return ""


def get_email_date(headers):

    date_string = get_header(
        headers,
        "Date"
    )

    if not date_string:
        return ""

    try:

        date = parsedate_to_datetime(
            date_string
        )

        return date.isoformat()

    except Exception:

        return date_string


def get_body(payload):

    if "parts" not in payload:

        body = payload.get(
            "body",
            {}
        )

        data = body.get("data")

        if not data:
            return ""

        try:

            return base64.urlsafe_b64decode(
                data
            ).decode(
                "utf-8",
                errors="ignore"
            )

        except Exception:

            return ""

    text_parts = []

    for part in payload["parts"]:

        mime_type = part.get(
            "mimeType",
            ""
        )

        if mime_type == "text/plain":

            data = part.get(
                "body",
                {}
            ).get("data")

            if data:

                try:

                    text_parts.append(
                        base64.urlsafe_b64decode(
                            data
                        ).decode(
                            "utf-8",
                            errors="ignore"
                        )
                    )

                except Exception:
                    pass

        elif "parts" in part:

            text_parts.append(
                get_body(part)
            )

    return "\n".join(text_parts)


def extract_attachments(payload):

    attachments = []

    def walk(part):

        filename = part.get(
            "filename",
            ""
        )

        body = part.get(
            "body",
            {}
        )

        if filename:

            attachments.append({
                "filename": filename,
                "attachment_id": body.get(
                    "attachmentId"
                ),
                "data": body.get(
                    "data"
                ),
                "mime_type": part.get(
                    "mimeType",
                    ""
                )
            })

        for child in part.get(
            "parts",
            []
        ):

            walk(child)

    walk(payload)

    return attachments


def list_messages(
    service,
    max_results=100
):

    response = service.users().messages().list(
        userId="me",
        maxResults=max_results
    ).execute()

    return response.get(
        "messages",
        []
    )


def get_message(
    service,
    message_id
):

    return service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()


def download_attachment(
    service,
    message_id,
    attachment_id
):

    response = (
        service.users()
        .messages()
        .attachments()
        .get(
            userId="me",
            messageId=message_id,
            id=attachment_id
        )
        .execute()
    )

    data = response.get(
        "data",
        ""
    )

    return base64.urlsafe_b64decode(
        data
    )