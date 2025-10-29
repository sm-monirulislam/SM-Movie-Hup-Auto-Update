import json
import os

# Output file
output_file = "combined_movies.m3u"

# Header
with open(output_file, "w", encoding="utf-8") as out:
    out.write("#EXTM3U\n")

# Loop all JSON files
for filename in os.listdir():
    if filename.endswith(".json"):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                continue

            for movie in data:
                name = movie.get("name", "Unknown Movie")
                link = movie.get("url") or movie.get("link")
                lang = movie.get("language", "").lower()

                # Group title based on language
                if "bangla" in lang:
                    group = "Movie Bangla"
                elif "english" in lang:
                    group = "Movie English"
                else:
                    group = f"Movie {lang.capitalize()}" if lang else "Movie Others"

                if link:
                    out.write(f'#EXTINF:-1 group-title="{group}",{name}\n{link}\n')

print("✅ combined_movies.m3u file created successfully!")
