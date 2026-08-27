import hashlib
import re
from pathlib import Path


def safe_filename(filename):
    filename = Path(filename or "attachment").name.strip()
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename)
    filename = re.sub(r"\s+", " ", filename).strip(" .")
    return filename or "attachment"


def calculate_sha256(data: bytes):
    return hashlib.sha256(data).hexdigest()


def get_category_folder(base_directory, category):
    safe_category = safe_filename(category or "other").lower()
    folder = Path(base_directory) / safe_category
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_attachment_file(data: bytes, filename: str, base_directory, category):
    filename = safe_filename(filename)
    folder = get_category_folder(base_directory, category)
    file_hash = calculate_sha256(data)
    destination = folder / filename
    if destination.exists():
        stem = destination.stem
        suffix = destination.suffix
        destination = folder / f"{stem}_{file_hash[:8]}{suffix}"
    with open(destination, "wb") as file:
        file.write(data)
    return destination, file_hash
