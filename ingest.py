"""Milestone 3 — Ingestion.

Downloads each source in sources.py, strips the HTML down to readable article
text, and saves a clean .txt file under documents/.

What this does NOT keep: nav bars, footers, scripts, styles, ads, "share this
article" widgets, and comment sections. We want the body text only, because that
is what we will chunk and embed.

Run:  python ingest.py
Any source that the server blocks (403/timeout/login wall) is reported at the
end so it can be collected manually instead.
"""

import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from sources import SOURCES

DOCS_DIR = Path(__file__).parent / "documents"

# A normal browser User-Agent. Some sites reject the default python-requests UA.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Tags whose contents are never article text — removed before extraction.
JUNK_TAGS = ["script", "style", "nav", "footer", "header", "aside", "form",
             "noscript", "iframe", "button", "svg"]

# Class/id substrings that mark boilerplate blocks. Kept NARROW on purpose:
# broad tokens like "tag", "header", or "nav" also match the WordPress content
# wrappers on these sites (post-tags, entry-header), which would delete the
# article itself. The structural nav/header/footer tags are already removed via
# JUNK_TAGS, so this only needs to catch in-body widgets.
JUNK_PATTERNS = re.compile(
    r"(share|social|related|sidebar|comment|newsletter|subscribe|cookie|"
    r"breadcrumb|author|advert|promo|widget|masthead|menu|header|footer|"
    r"navigation|navbar|td-header|td-footer|td-a-rec|toolbar|site-info|"
    r"copyright|cover-stories|our-publications)",
    re.IGNORECASE,
)


def fetch(url: str) -> str:
    """Download raw HTML. Raises on any non-200 response."""
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


# Exact short lines that are widget/footer remnants or review-card metadata
# (star rating, class year, timestamp) with no actual content. Matched against
# each extracted block, case-insensitive, whole-line.
JUNK_LINE_RE = re.compile(
    r"^("
    # site chrome / footer
    r"login|register|registration is closed\.?|follow us|our publications|"
    r"company info.*|advertising.*|copyright ©.*|calculate for all schools|"
    r"click here to see the entire guide\.?|cover stories|terms of service|"
    r"privacy policy|find college scholarships|"
    # Niche review-card metadata with no review text attached
    r"rating \d+(\.\d+)? out of \d+|"
    r"(freshman|sophomore|junior|senior|alum|alumni|alumnus|graduate student|"
    r"grad student|transfer student|parent)|"
    r"(a|\d+) (second|minute|hour|day|week|month|year)s? ago|"
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.? \d{1,2},? \d{4}|"
    # dead poll options (0% = nobody picked it = no signal)
    r".{1,80} 0%"
    r")$",
    re.IGNORECASE,
)

# Class substrings marking review BODY text that lives in <span>/<div>, not <p>
# (e.g. Niche wraps each student review in <span class="review__text">). These
# are pulled in addition to the normal paragraph blocks.
REVIEW_TEXT_RE = re.compile(r"review__text|review-text|review__body|review-body",
                            re.IGNORECASE)


def _p_text_len(el) -> int:
    """Total characters of <p> text inside an element (a proxy for 'is this
    real article content vs. a widget?')."""
    return sum(len(p.get_text(strip=True)) for p in el.find_all("p"))


def clean_html(html: str) -> str:
    """Turn raw HTML into clean, paragraph-separated plain text."""
    soup = BeautifulSoup(html, "lxml")

    # 1. Drop tags that never contain article text.
    for tag in soup(JUNK_TAGS):
        tag.decompose()

    # 2. Drop boilerplate blocks matched by class/id — but ONLY if they hold
    #    little paragraph text. This guards against content wrappers that
    #    incidentally carry a junk token in their class list (e.g. CoHP wraps
    #    the whole post in a div classed "blog-style-single-share"; matching
    #    "share" there and deleting it would nuke the entire article).
    for attr in ("class", "id"):
        for el in soup.find_all(attrs={attr: JUNK_PATTERNS}):
            if _p_text_len(el) < 200:
                el.decompose()

    # 3. Pull text block-by-block from the whole cleaned page so paragraph
    #    breaks survive as \n\n. We deliberately do NOT restrict to the first
    #    <article>: on these WordPress themes that element is often a "related
    #    post" teaser, not the main body. The nav/footer/header tags are already
    #    gone (step 1), so scanning the whole page is safe and more robust.
    root = soup.body or soup
    blocks = []
    seen = set()
    for el in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote"]):
        text = el.get_text(" ", strip=True)
        # Skip empties, very short nav-ish fragments, and exact duplicates.
        if not text or len(text) < 3:
            continue
        if text in seen:
            continue
        if JUNK_LINE_RE.match(text):  # drop chrome + review-card metadata
            continue
        seen.add(text)
        blocks.append(text)

    # Also pull review BODY text that sits in <span>/<div> (not <p>), e.g. Niche
    # review cards. Without this we'd keep only the rating/date chips and lose
    # the actual student reviews.
    for el in root.find_all(attrs={"class": REVIEW_TEXT_RE}):
        text = el.get_text(" ", strip=True)
        if text and len(text) >= 20 and text not in seen:
            seen.add(text)
            blocks.append(text)

    # Fallback: if block extraction found almost nothing (some pages render
    # text only in divs), take all the text at once.
    if len(" ".join(blocks)) < 200:
        blocks = [root.get_text("\n", strip=True)]

    text = "\n\n".join(blocks)

    # 5. Normalize whitespace: collapse spaces/tabs, cap blank-line runs at one.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> int:
    DOCS_DIR.mkdir(exist_ok=True)
    failed = []

    for src in SOURCES:
        out_path = DOCS_DIR / src["filename"]
        try:
            html = fetch(src["url"])
            text = clean_html(html)

            if len(text) < 200:
                raise ValueError(f"extracted only {len(text)} chars (likely blocked)")

            out_path.write_text(text, encoding="utf-8")
            print(f"  OK   {src['filename']:<40} {len(text):>6} chars")
        except Exception as exc:  # noqa: BLE001 — report, don't crash the batch
            failed.append((src, exc))
            print(f"  FAIL {src['filename']:<40} {exc}")
        time.sleep(1)  # be polite; avoid hammering the servers

    print(f"\nSaved {len(SOURCES) - len(failed)}/{len(SOURCES)} documents to {DOCS_DIR}/")
    if failed:
        print("\nThese need manual collection (open the URL, copy the article text,")
        print("paste into the named file under documents/):")
        for src, exc in failed:
            print(f"  - {src['filename']}  <-  {src['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
