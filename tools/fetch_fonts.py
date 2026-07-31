#!/usr/bin/env python3
"""Fetch self-hosted OFL fonts (woff2) from Google Fonts and emit a local fonts.css.

Downloads the variable woff2 files (all unicode-range subsets) for the book's
type pairing and rewrites the @font-face src to local relative paths, so the
site renders identically offline (file://) and on GitHub Pages with no CDN.
Standard library only.
"""
import os, re, urllib.request

FONTS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
CSS_OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "css", "fonts.css")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

FAMILIES = [
    ("Newsreader", "ital,opsz,wght@0,6..72,400..700;1,6..72,400..600", "newsreader"),
    ("Space Grotesk", "wght@400..700", "space-grotesk"),
    ("JetBrains Mono", "ital,wght@0,400..700;1,400..500", "jetbrains-mono"),
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main():
    os.makedirs(FONTS_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(CSS_OUT), exist_ok=True)
    all_css = ["/* Self-hosted OFL fonts (Newsreader, Space Grotesk, JetBrains Mono).",
               "   Fetched from Google Fonts; SIL Open Font License 1.1. */", ""]
    total = 0
    for family, axis, slug in FAMILIES:
        url = f"https://fonts.googleapis.com/css2?family={family.replace(' ', '+')}:{axis}&display=swap"
        css = fetch(url).decode("utf-8")
        urls = re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)", css)
        seen = {}
        idx = 0
        for u in urls:
            if u in seen:
                continue
            fn = f"{slug}-{idx}.woff2"
            data = fetch(u)
            assert data[:4] == b"wOF2", f"not a woff2: {u}"
            with open(os.path.join(FONTS_DIR, fn), "wb") as f:
                f.write(data)
            seen[u] = fn
            idx += 1
            total += 1
        for u, fn in seen.items():
            css = css.replace(u, f"../fonts/{fn}")
        all_css.append(f"/* ---- {family} ({idx} subset files) ---- */")
        all_css.append(css.strip())
        all_css.append("")
        print(f"{family}: {idx} woff2 files")
    with open(CSS_OUT, "w") as f:
        f.write("\n".join(all_css))
    print(f"Total {total} font files -> assets/fonts/  |  css -> assets/css/fonts.css")


if __name__ == "__main__":
    main()
