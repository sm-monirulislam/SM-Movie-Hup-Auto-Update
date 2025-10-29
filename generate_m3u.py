import json
import os

# 🔧 ইনপুট ফাইলের নাম
JSON_FILES = [
    "static_movies.json",
    "static_movies(ctgfun).json",
    "static_movies(cinehub24).json"
]

M3U_FILES = [
    "movie.m3u"
]

OUTPUT_FILE = "combined.m3u"

# 🧩 Helper Function — SR সরানো
def clean_group_title(title: str):
    if not title:
        return ""
    title = title.replace("SR", "").strip()
    return " ".join(title.split())  # Extra space clean


# 🧩 M3U ফাইলগুলো থেকে ডেটা পড়া
def read_m3u_files():
    entries = []
    for file in M3U_FILES:
        if not os.path.exists(file):
            print(f"⚠️ Missing M3U file: {file}")
            continue
        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for i in range(0, len(lines) - 1, 2):
                if lines[i].startswith("#EXTINF"):
                    info_line = lines[i].strip()
                    url_line = lines[i + 1].strip()
                    # group-title থেকে SR মুছে ফেলা
                    if 'group-title="' in info_line:
                        before, after = info_line.split('group-title="', 1)
                        title, rest = after.split('"', 1)
                        cleaned_title = clean_group_title(title)
                        info_line = f'{before}group-title="{cleaned_title}"{rest}'
                    entries.append(f"{info_line}\n{url_line}")
    return entries


# 🧩 JSON ফাইলগুলো থেকে ডেটা পড়া
def read_json_files():
    entries = []
    for file in JSON_FILES:
        if not os.path.exists(file):
            print(f"⚠️ Missing JSON file: {file}")
            continue

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for movie_name, details in data.items():
            logo = details.get("tvg_logo", "")
            year = details.get("year", "")
            links = details.get("links", [])

            for link in links:
                url = link.get("url")
                language = link.get("language", "").lower()

                # Language অনুযায়ী Group Title
                if "bangla" in language:
                    group_title = "Movie Bangla"
                elif "english" in language:
                    group_title = "Movie English"
                else:
                    group_title = "Movies"

                entry = (
                    f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group_title}" , {movie_name} ({year})\n'
                    f'{url}'
                )
                entries.append(entry)
    return entries


# 🧩 সবকিছু একত্র করে combined.m3u বানানো
def main():
    all_entries = ["#EXTM3U"]

    # M3U অংশ
    all_entries.extend(read_m3u_files())

    # JSON অংশ
    all_entries.extend(read_json_files())

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_entries))

    print(f"✅ Combined playlist created: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
