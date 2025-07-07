# === IMPORTS ===
import requests  # to send HTTP requests
from bs4 import BeautifulSoup  # to parse HTML pages
from urllib.parse import urljoin  # to resolve relative URLs
import time  # to track crawl duration

# === CONFIGURATION SECTION ===

# The base URL where crawling starts
BASE_URL = "https://docs.chaicode.com/"

# How deep the crawler should go — 2 means:
#   - Start page → internal links → sub-pages of those links
MAX_DEPTH = 2

# Where the final list of collected URLs will be saved
OUTPUT_FILE = "chaiaurdocs_links.txt"

# Custom user-agent header to avoid being blocked by websites
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ChaiCrawler/1.0; +https://chaicode.com/)"
}

# === URL FILTER FUNCTION ===
def is_valid_url(url):
    """
    Filters out links that are not relevant or are external/social/anchors.

    Example:
    - Skips mailto:, tel:, social links, and internal page anchors (#section)
    """
    invalid_parts = ["#", "mailto:", "tel:", "linkedin", "github", "twitter", "facebook"]
    return not any(part in url for part in invalid_parts)


# === MAIN RECURSIVE CRAWLER FUNCTION ===
def get_all_links(url, visited=None, depth=0, max_depth=2):
    """
    Recursively visits internal pages starting from the given URL,
    and collects all unique and valid page URLs up to the given depth.
    """
    if visited is None:
        visited = set()  # Keep track of already visited URLs to avoid cycles

    # Stop if max depth reached or URL already visited
    if depth > max_depth or url in visited:
        return visited

    print(f"{'  ' * depth}🔗 Visiting: {url}")
    visited.add(url)

    try:
        # Request the current URL
        response = requests.get(url, timeout=10, headers=HEADERS)
        response.raise_for_status()
    except Exception as e:
        # If any error (e.g., timeout, 404), skip the page
        print(f"{'  ' * depth}⚠️ Skipping due to error: {e}")
        return visited

    # Parse the page content using BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract all <a href="..."> links
    for link in soup.find_all("a", href=True):
        href = link["href"]  # Relative or absolute link
        full_url = urljoin(url, href)  # Convert to full absolute URL

        # Conditions to include the link:
        # 1. Starts with the base site URL
        # 2. Passes our validity filter
        # 3. Hasn’t already been visited
        if (
            full_url.startswith(BASE_URL)
            and is_valid_url(full_url)
            and full_url not in visited
        ):
            # Recursive call to crawl this new page
            visited.update(get_all_links(full_url, visited, depth + 1, max_depth))

    return visited  # Return the full set of visited links


# === MAIN PROGRAM ENTRY POINT ===
if __name__ == "__main__":
    print("🚀 Crawling ChaiAurDocs...\n")
    start_time = time.time()

    # Start crawling from BASE_URL and collect all links
    all_links = get_all_links(BASE_URL, max_depth=MAX_DEPTH)

    # Sort links alphabetically (for consistency)
    sorted_links = sorted(all_links)

    # Save collected links to file
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(sorted_links))

    # Print summary
    print(f"\n✅ Done! {len(sorted_links)} pages saved to `{OUTPUT_FILE}`")
    print(f"⏱️ Took {round(time.time() - start_time, 2)} seconds")
