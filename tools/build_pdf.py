#!/usr/bin/env python3
"""Render the whole book to a single downloadable PDF (headless Chrome + pypdf merge).

Usage: build_pdf.py   (run after tools/build.py). Output: dist/The-AI-Founders-Handbook.pdf
Uses each page's print stylesheet, so nav/sidebar/footer are dropped automatically.
"""
import os, re, subprocess
from pypdf import PdfWriter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TMP = "/tmp/aifh_pdf"


def main():
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    pages = ["index.html"] + sorted(f for f in os.listdir(ROOT) if re.match(r"\d\d-.*\.html$", f))
    writer = PdfWriter()
    for i, page in enumerate(pages):
        out = os.path.join(TMP, f"{i:02d}.pdf")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", f"file://{ROOT}/{page}"],
                       check=True, capture_output=True, timeout=180)
        writer.append(out)
        print(f"  + {page}")
    dest = os.path.join(ROOT, "dist", "The-AI-Founders-Handbook.pdf")
    with open(dest, "wb") as f:
        writer.write(f)
    print(f"PDF: {dest}  ({len(writer.pages)} pages, {os.path.getsize(dest)//1024} KB)")


if __name__ == "__main__":
    main()
