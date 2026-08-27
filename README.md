# Nexora Mail

A local-first Gmail email intelligence and attachment organization system built with Python.

## Project overview

Nexora Mail connects to Gmail with OAuth, reads messages through the Gmail API, classifies email locally with deterministic rules, downloads attachments, stores metadata in SQLite, and exposes a FastAPI dashboard for browsing the local archive.

## Main features

- Gmail OAuth authentication with the Gmail API read-only scope.
- Message ingestion for sender, recipients, CC, subject, received date, and plain-text body.
- Rule-based classification into `finance`, `orders`, `github`, `work`, `education`, `newsletter`, and `other`.
- Attachment download into category folders under `downloads/`.
- Filename sanitization and SHA-256 duplicate detection before writing duplicate files.
- SQLite storage for emails, attachments, and sync run history.
- CLI dry-run mode with `python main.py --dry-run`.
- FastAPI dashboard with email, attachment, search, statistics, and sync pages.

## Architecture

```text
FastAPI routes / CLI
        ↓
sync_service.py
        ↓
gmail_client.py → classifier.py → attachment_manager.py → database.py
        ↓
SQLite database and local downloads folder
```

The dashboard reads real values from SQLite; it does not use sample statistics.

## Project structure

```text
app/                    FastAPI application, templates, and static assets
attachment_manager.py   Filename sanitization, SHA-256 hashing, attachment writes
classifier.py           Local rule-based email classifier
config.py               Paths, Gmail scopes, and sync limits
database.py             SQLite schema initialization and persistence helpers
gmail_client.py         Gmail OAuth/API helpers and message parsing
main.py                 Existing CLI entry point with dry-run support
sync_service.py         Reusable Gmail synchronization service
requirements.txt        Python dependencies
tests/                  Unit tests
```

## Technology stack

- Python
- FastAPI
- Jinja2 templates
- SQLite
- HTML/CSS
- Google Gmail API client libraries
- Pytest

## Gmail OAuth setup

1. Create a Google Cloud OAuth client for a desktop application.
2. Download the OAuth client JSON file.
3. Save it as `credentials.json` in the project root.
4. Run either `python main.py --dry-run` or `uvicorn app.main:app --reload` and trigger sync.
5. Complete the browser-based OAuth consent flow.
6. Nexora Mail writes `token.json` locally for future runs.

`credentials.json` and `token.json` contain sensitive OAuth material and **must not be committed**.

## Google Cloud setup

1. Open Google Cloud Console.
2. Create or select a project.
3. Enable the Gmail API.
4. Configure the OAuth consent screen.
5. Create OAuth client credentials for a desktop application.
6. Download the credentials and place them at `credentials.json` in this repository.

## Test user configuration

If the OAuth consent screen is in testing mode, add your Gmail address as a test user in Google Cloud. Only configured test users can complete OAuth while the app is unpublished.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Configuration is currently defined in `config.py`:

- `DATA_DIR`: local data directory.
- `DOWNLOAD_DIR`: category-organized attachment directory.
- `TOKEN_FILE`: local OAuth token path.
- `CREDENTIALS_FILE`: OAuth client JSON path.
- `DATABASE_FILE`: SQLite database path.
- `SCOPES`: Gmail API scopes.
- `MAX_EMAILS`: maximum messages listed per sync run.

## Running the application

Start the dashboard in development mode:

```bash
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000`.

## Dry-run mode

```bash
python main.py --dry-run
```

Dry-run authenticates with Gmail, reads and classifies messages, prints what would happen, and avoids database writes and attachment downloads.

## Database behavior

Nexora Mail stores data in `data/nexora.db`. Schema initialization is additive and preserves existing data. Existing installations are upgraded with missing columns for body, recipients, CC, priority, MIME type, duplicate flags, and sync run history.

## Attachment organization

Attachments are saved under `downloads/<category>/`. Filenames are sanitized, SHA-256 hashes are calculated, and attachments with hashes already present in SQLite are skipped to prevent uncontrolled duplicate downloads.

## Security considerations

- Never commit `credentials.json` or `token.json`.
- Do not hardcode Gmail credentials.
- Gmail access uses OAuth and the read-only scope.
- SQL queries use parameterized values for user input.
- Email body rendering uses escaped plain text in templates.
- Attachment downloads are served only from the configured `downloads/` directory.
- Filenames and category folders are sanitized before writing files.

## Gmail scopes used

```python
https://www.googleapis.com/auth/gmail.readonly
```

This read-only scope is sufficient for message and attachment ingestion. The app does not modify Gmail messages.

## Dashboard usage

- `/` shows overview cards, category counts, recent emails, recent attachments, and last sync status.
- `/emails` browses stored messages with search, category filtering, pagination, and sortable-ready query parameters.
- `/emails/{id}` shows message metadata, escaped body text, attachments, and Gmail ID.
- `/attachments` filters stored attachments by category, filename, and extension.
- `/statistics` summarizes stored processing statistics.
- `/search?q=school` searches sender, subject, body, and category.
- `POST /sync` starts a real Gmail synchronization in a FastAPI background task.

## API endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | Dashboard overview |
| GET | `/emails` | Email list |
| GET | `/emails/{id}` | Email detail |
| GET | `/attachments` | Attachment browser |
| GET | `/attachments/{id}/download` | Safe local attachment download |
| GET | `/statistics` | Statistics page |
| GET | `/search` | Search interface |
| POST | `/sync` | Trigger Gmail sync |

## Screenshots

> Placeholder: Dashboard overview screenshot.

> Placeholder: Email detail screenshot.

> Placeholder: Attachment browser screenshot.

## Future roadmap

- Configurable classification rules from a local YAML or JSON file.
- Optional SQLite FTS5 search indexing.
- Sync progress polling in the dashboard.
- More granular priority detection.
- Export tools for local archives.
- Additional attachment analytics.

## Contributing

Contributions are welcome. Please keep the application local-first, avoid committing secrets, add tests for new behavior, and preserve dry-run safety.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
