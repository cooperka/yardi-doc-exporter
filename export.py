import os
import re
import json
import requests
import time
import sys
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load configs from .env file
load_dotenv()

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
MANIFEST_FILE = os.path.join(DOWNLOAD_DIR, "manifest.json")
ANTI_SPAM_DURATION_SEC = float(os.getenv("ANTI_SPAM_DURATION_SEC"))

session = requests.Session()
# Some headers are required by cloudflare
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
})

def sanitize_filename(name):
    """Make safe filenames for OS."""
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def load_manifest():
    """Load manifest JSON if it exists."""
    if os.path.exists(MANIFEST_FILE):
        print("Loaded previous manifest, will NOT re-download files")
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    # Otherwise, start fresh.
    manifest = {"file_urls": {}}
    save_manifest(manifest)
    return manifest

def save_manifest(manifest):
    """Save manifest to disk."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

def file_in_manifest(file_url, manifest):
    """Check if file exists in manifest."""
    return file_url in manifest["file_urls"]

def save_file(file_url, file_name, extension, folder_path, manifest):
    """Download and save file with metadata, unless it's already marked as downloaded."""
    os.makedirs(folder_path, exist_ok=True)

    if file_in_manifest(file_url, manifest):
        print(f"Skipping already-downloaded file: {file_name}")
        return

    r = session.get(file_url, allow_redirects=True)
    r.raise_for_status()

    full_path = os.path.join(folder_path, sanitize_filename(file_name) + extension)

    with open(full_path, "wb") as f:
        f.write(r.content)

    manifest["file_urls"][file_url] = folder_path

    print(f"Saved file: {full_path}")

    time.sleep(ANTI_SPAM_DURATION_SEC)

def parse_download_url(onclick):
    """Extract the document URL from the saved window.open JS."""
    match = re.search(r"window\.open\(\s*['\"]([^'\"]+)", onclick or "")
    if not match:
        raise ValueError("Document link does not contain a window.open URL")
    return match.group(1)

def export_saved_page(html_file, manifest):
    """Parse the exported HTML page and download its files."""
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    canonical = soup.select_one('link[rel="canonical"][href]')
    if not canonical:
        raise ValueError("Saved page is missing a canonical URL, cannot determine base_url")
    page_url = canonical["href"]
    base_url = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(page_url))
    # Some headers are required by cloudflare
    session.headers["Referer"] = page_url

    table = soup.select_one("#DivT")
    if not table:
        raise ValueError("Saved page is missing the documents table (#DivT)")

    rows = table.select("tr[data-tt-id]")
    folders = {}
    for row in rows:
        description = row.select_one('td[data-label="Description"]')
        if not description:
            continue
        folder = description.select_one(".folder")
        if folder:
            folder_name = folder.get_text(" ", strip=True)
            parent_id = row.get("data-tt-parent-id")
            parent_path = folders.get(parent_id, "")
            folders[row["data-tt-id"]] = (
                parent_path if folder_name == "Top" else os.path.join(parent_path, folder_name)
            )
            continue

        file_anchor = row.select_one('td[data-label="Open"] a, td[data-label="Open Document"] a')
        file_description = description.select_one(".file")
        if not file_anchor or not file_description:
            continue

        original_name = file_anchor.get_text(strip=True)
        extension = os.path.splitext(original_name)[1]
        file_name = file_description.get_text(" ", strip=True)
        download_url = urljoin(base_url, parse_download_url(file_anchor.get("onclick")))
        folder_path = os.path.join(DOWNLOAD_DIR, folders.get(row.get("data-tt-parent-id"), ""))
        save_file(download_url, file_name, extension, folder_path, manifest)

        save_manifest(manifest)

def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"Usage: {sys.argv[0]} saved-page.html")

    manifest = load_manifest()
    export_saved_page(sys.argv[1], manifest)

if __name__ == "__main__":
    main()
