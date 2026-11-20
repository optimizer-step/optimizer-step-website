"""Tell Bing (and the other IndexNow search engines) that the site's pages changed.

    python scripts/indexnow.py

Run it after a change is live (about a minute after `git push`). It sends every URL in
docs/sitemap.xml to https://api.indexnow.org, which shares it with Bing, Yandex, Seznam,
Naver and Yep. Bing also powers DuckDuckGo, Yahoo and Ecosia results. The key file
site/static/<key>.txt is published at the site root, which proves we own the site.
Google does not use IndexNow: it reads the sitemap submitted in Google Search Console.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = "www.optimizerstep.com"


def main() -> int:
    keys = [p for p in (ROOT / "site" / "static").glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}\.txt", p.name)]
    if len(keys) != 1:
        print("Expected exactly one IndexNow key file (32 hex characters + .txt) in site/static/.")
        return 1
    key = keys[0].stem
    urls = re.findall(r"<loc>([^<]+)</loc>", (ROOT / "docs" / "sitemap.xml").read_text(encoding="utf-8"))
    if not urls:
        print("No URLs in docs/sitemap.xml. Run `python scripts/build_pages.py` first.")
        return 1
    payload = {"host": HOST, "key": key, "keyLocation": f"https://{HOST}/{key}.txt", "urlList": urls}
    request = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            print(f"IndexNow accepted {len(urls)} URLs (HTTP {response.status}).")
            return 0
    except urllib.error.HTTPError as error:
        meaning = {400: "bad request", 403: "key file not found or wrong", 422: "URLs don't match the host", 429: "too many requests"}
        print(f"IndexNow refused the request: HTTP {error.code} ({meaning.get(error.code, 'see indexnow.org')}).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
