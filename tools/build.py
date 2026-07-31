#!/usr/bin/env python3
"""Build The AI Founder's Handbook: content/*.md -> static HTML pages + index + search.

Authoring format on top of Markdown:
  ---frontmatter---              part, part_num, chapter_num, title, dek, slug,
                                 reading_time, prev_url/title, next_url/title
  ## Section                     auto-numbered  7.1, 7.2 ... with #anchors
  :::rule Title ... :::          callouts: rule | takeaways | warning | definition | exercise
  {sn: text}  {case: text}       margin sidenotes (inline markdown: ** * ` [](],)
  {figure: path | caption}       inlines an SVG file + <figcaption>
  ```lang ... ```                Pygments-highlighted code with a copy button
  [^id] / [^id]: ...             footnote citations
Everything renders offline (file://) and on GitHub Pages — relative paths, no CDN.
"""
import os, re, html, json, markdown
from pygments import highlight as pyg_highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTENT = os.path.join(ROOT, "content")
IMG = os.path.join(ROOT, "assets", "img")

BOOK_TITLE = "The AI Founder's Handbook"
BOOK_SUB = "Building an AI Startup in 2026"
SERIES = "Startup Bootcamp Series"

# ---------------------------------------------------------------- Table of contents
TOC = [
    ("I", "Foundations", [
        (1, "Introduction to AI Startups", "Why an AI startup is a different species."),
        (2, "AI Fundamentals I: Models, Modalities & Inference", "The technical bedrock, part one."),
        (3, "AI Fundamentals II: Prompting, RAG, Agents & Tooling", "The technical bedrock, part two."),
    ]),
    ("II", "Market & Validation", [
        (4, "Markets, Users & AI Product Strategy", "Where AI creates real value, not gimmicks."),
        (5, "Data Strategy & the Data Flywheel", "Turning usage into a compounding advantage."),
        (6, "Customer Validation for AI", "Evals as the new customer development."),
    ]),
    ("III", "The Stack", [
        (7, "Choosing Model Providers & Hugging Face", "Pick a model supplier without betting the company."),
        (8, "The Content & Data Stack", "Vector DBs, RAG infrastructure, pipelines."),
        (9, "Infrastructure, Observability & LLMOps", "Running models like a grown-up."),
        (10, "Production Evals & Monitoring", "Keeping quality from silently drifting."),
    ]),
    ("IV", "Go-to-Market & Moat", [
        (11, "Selling AI & Customer Success", "Trust, ROI proof, and security reviews."),
        (12, "Defensibility & the AI Moat", "Data, workflow, and distribution."),
    ]),
    ("V", "Company Building", [
        (13, "Finance & Unit Economics for AI", "Inference COGS and gross-margin reality."),
        (14, "Venture Funding for AI", "The 2026 investor landscape."),
        (15, "Pitfalls & Crises in AI", "Regressions, incidents, and provider risk."),
    ]),
    ("VI", "People", [
        (16, "Team, Culture & Leadership for AI", "Research, engineering, product — one org."),
    ]),
    ("VII", "Responsibility", [
        (17, "Responsible AI: Safety, Ethics & Regulation", "The EU AI Act and governance in 2026."),
    ]),
]
LIVE = {}   # {chapter_num: slug} — auto-populated from content/ at build time
CH_TITLE = {num: title for _, __, chs in TOC for num, title, _ in chs}


def nav_cards(chnum):
    live = sorted(LIVE)
    prevn = max([n for n in live if n < chnum], default=None)
    nextn = min([n for n in live if n > chnum], default=None)

    def card(n, cls, label):
        return (f'<a class="{cls}" href="{LIVE[n]}.html"><div class="dir">{label}</div>'
                f'<div class="t">Ch {n} · {html.escape(CH_TITLE.get(n,""))}</div></a>')
    prev = card(prevn, "prev", "← Previous") if prevn else \
        '<a class="prev" href="index.html"><div class="dir">←</div><div class="t">Contents</div></a>'
    nxt = card(nextn, "next", "Next →") if nextn else \
        '<a class="next" href="index.html"><div class="dir">→</div><div class="t">Back to Contents</div></a>'
    return prev + nxt

ICONS = {
    "rule": '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 21V4h11l-2 3.5L16 11H5"/><path d="M5 21v-4"/></svg>',
    "takeaways": '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l2.5 2.5L17 8"/><rect x="3.5" y="3.5" width="17" height="17" rx="3"/></svg>',
    "warning": '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3.5 21 19H3z"/><path d="M12 10v4M12 17h.01"/></svg>',
    "definition": '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5a2 2 0 0 1 2-2h13v15H6a2 2 0 0 0-2 2z"/><path d="M4 20h15"/></svg>',
    "exercise": '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>',
    "search": '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>',
    "theme": '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg>',
    "github": '<svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 012-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>',
}
DEFAULT_LABEL = {"rule": "Founder's Rule", "takeaways": "Key Takeaways",
                 "warning": "Warning", "definition": "Definition", "exercise": "Exercise"}


def slugify(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&[a-z]+;", "", text)
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_]+", "-", text).strip("-")


def strip_tags(t):
    return re.sub(r"<[^>]+>", "", t)


def clean_text(t):
    """Post-markdown heading text -> display-safe (resolve smart-punct entities, re-escape)."""
    return html.escape(html.unescape(strip_tags(t)), quote=False)


def inline_fmt(s):
    """Tiny inline-Markdown for sidenotes and captions."""
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def parse_frontmatter(raw):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    meta, body = {}, raw
    if m:
        body = m.group(2)
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                v = v.strip()
                if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
                    v = v[1:-1]          # strip surrounding quotes some agents add
                meta[k.strip()] = v
    return meta, body


def highlight_code(code, lang):
    try:
        lexer = get_lexer_by_name(lang, stripnl=False)
        inner = pyg_highlight(code, lexer, HtmlFormatter(nowrap=True)).rstrip("\n")
        plain = ""
        label = lang
    except ClassNotFound:
        inner = html.escape(code)
        plain = " plain"
        label = lang or "text"
    return (f'<div class="codeblock{plain}"><div class="codehead">'
            f'<span class="lang">{html.escape(label)}</span>'
            f'<button class="copy" type="button">Copy</button></div>'
            f'<pre><code>{inner}</code></pre></div>')


def transform(body, chnum):
    store = {}
    n = [0]

    def stash(htmlfrag, kind):
        n[0] += 1
        tok = f"ZZ{kind}{n[0]}ZZ"
        store[tok] = htmlfrag
        return tok

    # 1) code fences -> highlighted, block placeholder
    def code_repl(m):
        return "\n\n" + stash(highlight_code(m.group(2), m.group(1).strip()), "CODE") + "\n\n"
    body = re.sub(r"```([^\n`]*)\n(.*?)\n```", code_repl, body, flags=re.S)

    # 2) sidenotes / cases -> inline placeholder (numbered in document order)
    snnum = [0]
    def sn_repl(m):
        kind, text = m.group(1), m.group(2).strip()
        snnum[0] += 1
        inner = inline_fmt(text)
        if kind == "case":
            note = (f'<span class="sidenote case"><span class="sn-num">{snnum[0]}</span>'
                    f'<span class="sn-label">In the wild</span>{inner}</span>')
        else:
            note = f'<span class="sidenote"><span class="sn-num">{snnum[0]}</span>{inner}</span>'
        ref = f'<span class="sidenote-ref">{snnum[0]}</span>'
        return stash(ref + note, "SN")
    body = re.sub(r"\{(sn|case):\s*(.*?)\}", sn_repl, body, flags=re.S)

    # 3) figures -> inline SVG + caption, block placeholder
    def fig_repl(m):
        path, cap = m.group(1).strip(), m.group(2).strip()
        svg_path = os.path.join(IMG, path)
        if os.path.exists(svg_path):
            with open(svg_path) as f:
                svg = f.read()
        else:
            svg = '<div class="diagram-todo">◇ diagram pending</div>'
        frag = (f'<figure class="diagram">{svg}'
                f'<figcaption>{inline_fmt(cap)}</figcaption></figure>')
        return "\n\n" + stash(frag, "FIG") + "\n\n"
    body = re.sub(r"\{figure:\s*(.*?)\s*\|\s*(.*?)\}", fig_repl, body, flags=re.S)

    # 4) callouts -> md_in_html div (stays in text so inner markdown is processed)
    def callout_repl(m):
        typ, title, inner = m.group(1), m.group(2).strip(), m.group(3)
        label = title or DEFAULT_LABEL.get(typ, typ.title())
        icon = ICONS.get(typ, "")
        cls = "exercise" if typ == "exercise" else f"callout {typ}"
        head = f'<p class="co-label">{icon}{html.escape(label)}</p>'
        return f'<div class="{cls}" markdown="1">\n{head}\n\n{inner}\n\n</div>'
    body = re.sub(r"^:{3,}[ \t]*(\w+)[ \t]*(.*?)\n(.*?)\n:{3,}[ \t]*$", callout_repl, body, flags=re.M | re.S)

    # 5) Markdown -> HTML
    md = markdown.Markdown(extensions=["tables", "footnotes", "attr_list",
                                       "def_list", "sane_lists", "smarty", "md_in_html"],
                           extension_configs={"smarty": {"smart_dashes": True}})
    out = md.convert(body)

    # 6) restore placeholders
    for tok, frag in store.items():
        out = out.replace(f"<p>{tok}</p>", frag).replace(tok, frag)

    # 7) number sections, add ids + anchors, collect subnav (document order)
    subnav = []
    counter = [0]
    def head_repl(m):
        level, text = m.group(1), m.group(2)
        sid = slugify(text)
        anchor = f'<a class="anchor" href="#{sid}" aria-label="Link to this section">#</a>'
        if level == "2":
            counter[0] += 1
            num = f"{chnum}.{counter[0]}"
            subnav.append((num, clean_text(text), sid))
            return f'<h2 id="{sid}"><span class="secnum">{num}</span>{text}{anchor}</h2>'
        subnav.append(("", clean_text(text), sid))
        return f'<h3 id="{sid}">{text}{anchor}</h3>'
    out = re.sub(r"<h([23])>(.*?)</h\1>", head_repl, out, flags=re.S)

    # 8) polish: lede drop-cap, table wrappers, cell coloring, footnote classes
    out = re.sub(r"<p>", '<p class="lede">', out, count=1)
    out = out.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    out = out.replace("✓", '<span class="cell-yes">✓</span>')
    out = out.replace("✗", '<span class="cell-no">✗</span>')
    out = out.replace('<div class="footnote">', '<div class="footnotes">')
    out = out.replace('<sup id="fnref', '<sup class="footnote-ref" id="fnref')
    return out, subnav


# ---------------------------------------------------------------- rendering
def sidebar_html(current_num, subnav):
    rows = [f'<a class="toc-book" href="index.html">{html.escape(BOOK_TITLE)}</a>']
    for roman, ptitle, chapters in TOC:
        rows.append(f'<div class="toc-part"><span class="pnum">{roman}</span> {html.escape(ptitle)}</div>')
        for num, title, _ in chapters:
            live = num in LIVE
            href = f"{LIVE[num]}.html" if live else "#"
            cls = "current" if num == current_num else ("" if live else "muted")
            rows.append(f'<a class="{cls}" href="{href}"><span class="cnum">{num:02d}</span>{html.escape(title)}</a>')
            if num == current_num and subnav:
                sub = "".join(
                    f'<a href="#{sid}">{(numlbl + "  ") if numlbl else ""}{t}</a>'
                    for numlbl, t, sid in subnav)
                rows.append(f'<div class="subnav">{sub}</div>')
    return "\n".join(rows)


def page_head(title, depth_ok=True):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="assets/css/fonts.css">
<link rel="stylesheet" href="assets/css/book.css">
<link rel="stylesheet" href="assets/css/code.css">
</head>
<body>
<div class="progress"></div>
<header class="topbar">
  <button class="iconbtn menu-toggle" id="menu-btn" aria-label="Menu">{ICONS['menu']}</button>
  <a class="brand" href="index.html">The AI Founder's <b>Handbook</b></a>
  <span class="spacer"></span>
  <span class="byline-top hide-sm">Curated by <a href="https://github.com/arubhatt" target="_blank" rel="noopener">Arunabh Bhattacharjee</a></span>
  <button class="iconbtn" data-search-open aria-label="Search">{ICONS['search']}<span class="hide-sm">Search</span> <kbd>/</kbd></button>
  <a class="iconbtn" href="https://github.com/arubhatt" target="_blank" rel="noopener" aria-label="GitHub — arubhatt">{ICONS['github']}</a>
  <button class="iconbtn" id="theme-btn" aria-label="Toggle theme">{ICONS['theme']}</button>
</header>"""


def page_foot():
    return f"""
<footer class="site-footer">
  <div class="foot-inner">
    <span class="foot-curated">Curated by <a href="https://github.com/arubhatt" target="_blank" rel="noopener">Arunabh Bhattacharjee</a></span>
    <a class="foot-gh" href="https://github.com/arubhatt" target="_blank" rel="noopener">{ICONS['github']} github.com/arubhatt</a>
  </div>
</footer>
<div class="search-modal" id="search-modal">
  <div class="scrim"></div>
  <div class="search-box">
    <input id="search-input" type="text" placeholder="Search the book…" autocomplete="off" spellcheck="false">
    <div class="search-results" id="search-results"></div>
  </div>
</div>
<script src="assets/js/search-index.js"></script>
<script src="assets/js/book.js"></script>
</body>
</html>"""


def render_chapter(meta, content_html, subnav):
    chnum = int(meta["chapter_num"])
    navhtml = nav_cards(chnum)
    meta_bits = []
    if meta.get("reading_time"):
        meta_bits.append(html.escape(meta["reading_time"]))
    meta_bits.append(html.escape(meta.get("part", "")))
    head = f"""{page_head(f'{meta["title"]} · {BOOK_TITLE}')}
<div class="layout">
  <aside class="sidebar"><nav class="toc">{sidebar_html(chnum, subnav)}</nav></aside>
  <main class="content">
    <article class="chapter">
      <header class="chapter-head reading">
        <div class="kicker">{html.escape(meta.get("part",""))} · Chapter {chnum}</div>
        <div class="chapter-num">{chnum:02d}</div>
        <h1 class="chapter-title">{html.escape(meta["title"])}</h1>
        <p class="chapter-dek">{html.escape(meta.get("dek",""))}</p>
        <div class="chapter-meta">{" · ".join(b for b in meta_bits if b)}</div>
      </header>
      <div class="reading"><div class="prose">
{content_html}
      </div>
      <nav class="prevnext">{navhtml}</nav>
      </div>
    </article>
  </main>
</div>
{page_foot()}"""
    return head


def render_index():
    parts = []
    for roman, ptitle, chapters in TOC:
        rows = []
        for num, title, blurb in chapters:
            live = num in LIVE
            href = f"{LIVE[num]}.html" if live else "#"
            badge = "" if live else ' <span class="cx">· in the full build</span>'
            rows.append(f'<a href="{href}"><span class="n">{num:02d}</span>'
                        f'<span><span class="ct">{html.escape(title)}</span> '
                        f'<span class="cx">{html.escape(blurb)}</span>{badge}</span></a>')
        parts.append(f'<div class="part-block"><div class="p-h"><span class="pn">Part {roman}</span> {html.escape(ptitle)}</div>'
                     f'<div class="toc-grid">{"".join(rows)}</div></div>')
    body = f"""{page_head(f'{BOOK_TITLE} — {BOOK_SUB}')}
<div class="layout">
  <aside class="sidebar"><nav class="toc">{sidebar_html(0, None)}</nav></aside>
  <main class="content">
    <div class="cover">
      <div class="series">{html.escape(SERIES)}</div>
      <h1>{html.escape(BOOK_TITLE)}</h1>
      <div class="sub">{html.escape(BOOK_SUB)}</div>
      <div class="tagline">A field guide for founders building at the frontier</div>
      <div class="byline">Curated by <a href="https://github.com/arubhatt" target="_blank" rel="noopener">Arunabh Bhattacharjee</a> · github.com/arubhatt</div>
      <div class="cover-rule"></div>
      {"".join(parts)}
    </div>
  </main>
</div>
{page_foot()}"""
    return body


def build():
    global LIVE
    LIVE = {}
    for fn in os.listdir(CONTENT):
        if fn.endswith(".md"):
            with open(os.path.join(CONTENT, fn)) as f:
                m, _ = parse_frontmatter(f.read())
            if m.get("chapter_num") and m.get("slug"):
                LIVE[int(m["chapter_num"])] = m["slug"]
    search = []
    for fn in sorted(os.listdir(CONTENT)):
        if not fn.endswith(".md"):
            continue
        with open(os.path.join(CONTENT, fn)) as f:
            meta, body = parse_frontmatter(f.read())
        chnum = int(meta["chapter_num"])
        content_html, subnav = transform(body, chnum)
        out_name = meta["slug"] + ".html"
        with open(os.path.join(ROOT, out_name), "w") as f:
            f.write(render_chapter(meta, content_html, subnav))
        # search entries per section
        plain = re.sub(r"<[^>]+>", " ", content_html)
        sections = re.split(r'(?=<h2 id=")', content_html)
        for sec in sections:
            hm = re.search(r'<h2 id="([^"]+)"><span class="secnum">([^<]+)</span>(.*?)<a', sec)
            if not hm:
                continue
            sid, secnum, sectitle = hm.group(1), hm.group(2), html.unescape(strip_tags(hm.group(3)))
            txt = html.unescape(re.sub(r"\s+", " ", strip_tags(sec))).strip()
            search.append({"url": f"{out_name}#{sid}", "chapter": f"Ch {chnum} · {meta['title']}",
                           "section": f"{secnum} {sectitle}".strip(), "title": sectitle.strip(),
                           "text": txt[:260]})
        print(f"built {out_name}  ({len(subnav)} sections)")
    with open(os.path.join(ROOT, "index.html"), "w") as f:
        f.write(render_index())
    print("built index.html")
    with open(os.path.join(ROOT, "assets", "js", "search-index.js"), "w") as f:
        f.write("window.SEARCH_INDEX = " + json.dumps(search, ensure_ascii=False) + ";")
    print(f"built search-index.js  ({len(search)} entries)")


if __name__ == "__main__":
    build()
