import json
import os

# একাধিক JSON ফাইলের নাম
JSON_FILES = [
    "static_movies.json",
    "static_movies(ctgfun).json",
    "static_movies(cinehub24).json"
]

OUTPUT_FILE = "combined.m3u"
m3u = "#EXTM3U\n"

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        print(f"⚠️ Warning: {filename} not found, skipping.")
        return {}

# প্রতিটি JSON থেকে ডেটা পড়া
for file in JSON_FILES:
    data = load_json(file)
    for title, info in data.items():
        logo = info.get("tvg_logo", "")
        links = info.get("links", [])

        for link in links:
            url = link.get("url")
            language = link.get("language", "").strip()

            # group-title নির্ধারণ
            if language.lower() in ["bangla", "bengali", "বাংলা"]:
                group = "Movie Bangla"
            elif language.lower() in ["english", "ইংরেজি"]:
                group = "Movie English"
            else:
                group = f"Movie {language}" if language else "Movie Unknown"

            # শুধু valid link নিলে
            if url and any(ext in url for ext in [".m3u8", ".mp4", ".mkd"]):
                m3u += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {title} ({language})\n{url}\n'

# ফাইনাল ফাইল লেখা
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(m3u)

print(f"✅ Combined playlist saved as {OUTPUT_FILE}")
