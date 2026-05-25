import cloudscraper
from bs4 import BeautifulSoup
import re
from datetime import datetime
import concurrent.futures

BASE_URL = "https://fibwatch.art"
MAX_PAGES_TO_SCAN = 2500
MAX_WORKERS = 70

# =========================
# Movie Link Extractor
# =========================
def process_movie(base_name, watch_link, quality, scraper, group_name):
    try:
        res = scraper.get(watch_link, timeout=15)
        watch_soup = BeautifulSoup(res.text, 'html.parser')

        actual_link = None

        for a in watch_soup.find_all('a', href=True):
            href = a['href']

            if 'urlshortlink.top' in href and 'url=' in href:
                match = re.search(r'url=(.*)', href)

                if match:
                    decoded = (
                        match.group(1)
                        .replace('%3A', ':')
                        .replace('%2F', '/')
                    )

                    if '.mkv' in decoded or '.mp4' in decoded:
                        actual_link = decoded
                        break

            elif (
                ('.mkv' in href or '.mp4' in href)
                and 'urlshortlink.top' not in href
            ):
                actual_link = href

                if actual_link.startswith('/'):
                    actual_link = f"{BASE_URL}{actual_link}"

                break

        if not actual_link:
            return None

        poster_tag = watch_soup.find('meta', property='og:image')
        poster = poster_tag['content'] if poster_tag else ""

        file_name = actual_link.split('/')[-1]

        file_name = re.sub(
            r'\[Fibwatch\.Com\]',
            '',
            file_name,
            flags=re.IGNORECASE
        )

        file_name = re.sub(
            r'\.mkv|\.mp4',
            '',
            file_name,
            flags=re.IGNORECASE
        )

        file_name = file_name.replace('.', ' ').strip()

        m3u_entry = (
            f'#EXTINF:-1 tvg-logo="{poster}" '
            f'group-title="{group_name}", {file_name}\n'
            f'{actual_link}\n'
        )

        return m3u_entry

    except Exception:
        return None


# =========================
# Latest Page Scanner
# =========================
def scan_single_page_latest(page_num, scraper):

    url = f"{BASE_URL}/videos/latest?page_id={page_num}"

    found_movies = []

    try:
        response = scraper.get(url, timeout=15)

        soup = BeautifulSoup(response.text, 'html.parser')

        links = soup.find_all('a', href=True)

        watch_links = [
            link['href']
            for link in links
            if '/watch/' in link['href']
            and link['href'].endswith('.html')
        ]

        if not watch_links:
            return []

        for link in set(watch_links):

            full_link = (
                link
                if link.startswith('http')
                else f"{BASE_URL}{link}"
            )

            base_name_match = re.search(
                r'/watch/(.*?)(?:-\d{3,4}p_|_)',
                full_link
            )

            base_name = (
                base_name_match.group(1)
                if base_name_match
                else full_link.split('/')[-1]
            )

            quality_match = re.search(r'(\d{3,4})p', full_link)

            quality = (
                int(quality_match.group(1))
                if quality_match
                else 0
            )

            # page_num সহ save করছি
            found_movies.append(
                (page_num, base_name, full_link, quality)
            )

        return found_movies

    except Exception:
        return []


# =========================
# Main Scraper
# =========================
def run_latest_scraper(file_name, group_name):

    print(
        f"\n🚀 Starting ULTRA-FAST Scraper "
        f"({MAX_WORKERS} Threads) for {group_name}..."
    )

    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )

    best_qualities = {}
    best_links = {}
    best_pages = {}

    print(
        f"⏳ Scanning up to "
        f"{MAX_PAGES_TO_SCAN} pages CONCURRENTLY..."
    )

    # =========================
    # Stage 1: Scan Pages
    # =========================
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        future_to_page = {
            executor.submit(
                scan_single_page_latest,
                p,
                scraper
            ): p
            for p in range(1, MAX_PAGES_TO_SCAN + 1)
        }

        for count, future in enumerate(
            concurrent.futures.as_completed(future_to_page),
            1
        ):

            movies = future.result()

            for page_num, base_name, full_link, quality in movies:

                current_best = best_qualities.get(base_name, 0)

                if quality > current_best:

                    best_qualities[base_name] = quality
                    best_links[base_name] = full_link
                    best_pages[base_name] = page_num

            if count % 100 == 0:
                print(
                    f"   [+] Scanned "
                    f"{count}/{MAX_PAGES_TO_SCAN} pages..."
                )

    print(
        f"✅ Page scanning complete! "
        f"Found {len(best_links)} UNIQUE movies."
    )

    print(
        f"🎬 Starting extraction "
        f"with {MAX_WORKERS} THREADS..."
    )

    results = []

    # =========================
    # Sort Movies by Page Order
    # =========================
    sorted_movies = sorted(
        best_links.items(),
        key=lambda x: best_pages[x[0]]
    )

    # =========================
    # Stage 2: Extract Links
    # =========================
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        future_to_movie = {

            executor.submit(
                process_movie,
                b_name,
                w_link,
                best_qualities[b_name],
                scraper,
                group_name
            ): (b_name, best_pages[b_name])

            for b_name, w_link in sorted_movies
        }

        ordered_results = []

        for future in concurrent.futures.as_completed(
            future_to_movie
        ):

            b_name, page_num = future_to_movie[future]

            try:
                data = future.result()

                if data:
                    ordered_results.append((page_num, data))

                    print(
                        f"   ⚡ Pure Link Extracted: "
                        f"{b_name[:40]}..."
                    )

            except Exception:
                pass

    # =========================
    # Final Order Fix
    # =========================
    ordered_results.sort(key=lambda x: x[0])

    for _, entry in ordered_results:
        results.append(entry)

    # =========================
    # Write Playlist
    # =========================
    print(f"\n💾 Writing clean data to {file_name}...")

    with open(file_name, "w", encoding="utf-8") as f:

        f.write('#EXTM3U x-tvg-url=""\n')
        f.write(
            '# Playlist Generated Automatically\n'
        )

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        f.write(f'# Last Updated: {now}\n\n')

        for entry in results:
            f.write(entry)

    print(
        f"🎉 Done! Ordered M3U Playlist "
        f"generated successfully."
    )


# =========================
# Main
# =========================
def main():

    run_latest_scraper(
        file_name="Movie_sm.m3u",
        group_name="Latest Movie"
    )


if __name__ == "__main__":
    main()
