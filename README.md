# The AI Founder's Handbook

*Building an AI Startup in 2026* — Startup Bootcamp Series.

A static, offline-first web textbook. Open `index.html` in any browser (no server
needed) or host the folder on GitHub Pages as-is.

## Read it locally
Double-click **`index.html`**. Everything is self-contained — fonts, styles, search
index, and diagrams are all local, with no CDN or network calls.

## Host on GitHub Pages
1. Push this folder to a GitHub repo.
2. Settings → Pages → deploy from branch, root.
3. `.nojekyll` is already included so the asset folders serve verbatim.

## Rebuild after editing content
Chapters live in `content/*.md` and are compiled to HTML by the build script.

```bash
python3 -m venv build/venv
build/venv/bin/pip install markdown pygments
build/venv/bin/python tools/build.py      # regenerates *.html + search index
```

Fonts were fetched once into `assets/fonts/` via `tools/fetch_fonts.py` (self-hosted,
SIL Open Font License).

## Structure
```
index.html                     cover + table of contents
07-*.html                      compiled chapters
content/*.md                   chapter sources (authoring format: see tools/build.py)
assets/css/  js/  fonts/  img/ design system, behavior, fonts, diagrams
tools/build.py                 Markdown → themed HTML pipeline
```

## Status
Complete — all **17 chapters** (~58,000 words) written, researched against mid-2026
sources with footnote citations, and styled to a single system. Every chapter has a
bespoke theme-aware diagram, callouts, margin sidenotes, comparison tables, and an
end-of-chapter exercise, and follows one running example (Cortex, an AI support agent).
Open `index.html` to read.
