import zipfile
import os
import sys

ZIP_FILE = "movie_main.zip"
EXTRACT_DIR = "main"

password = os.environ.get("ZIP_PASSWORD")

if not password:
    print("ZIP_PASSWORD missing")
    sys.exit(1)

with zipfile.ZipFile(ZIP_FILE, "r") as z:
    z.extractall(EXTRACT_DIR, pwd=password.encode())

print("ZIP extracted successfully")
