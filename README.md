# Yardi document exporter

Export all your documents from Yardi community portals (like RentCafe, CondoCafe, securecafe.com, etc.) to your local computer. Downloads PDFs and files while preserving folder structure.

Useful for Yardi backups & data migration. Easy to use and does not require coding.

Created by a community member (not endorsed by Yardi).

## Usage

### Setup

1. Install [Python 3](https://www.python.org/) if you don't already have it.
1. Install required packages: `pip install python-dotenv`

### Download your files

1. Clone this repository onto your computer.
1. Optionally edit the `.env` file by following the instructions inside.
1. Visit your Yardi portal and click on the Documents page; after it loads, right click and "Save Page as HTML".
1. Run the program: `python export.py your-saved-page.html`

The script will automatically download the documents from each folder onto your local computer, preserving folder structure.

### Notes

Files will be named according to the user-facing name specified in Yardi, which may be different from the original filename using the "download" button online. For example, if a user uploaded `DCIM_01.jpg` and named it `Rainbow`, the file saved by this program will be `Rainbow.jpg`.

Yardi does not show file metadata, so the original created/modified date of the file cannot be determined.
