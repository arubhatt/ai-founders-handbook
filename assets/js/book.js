/* The AI Founder's Handbook — reader behavior. Vanilla JS, works on file://. */
(function () {
  "use strict";
  var root = document.documentElement;
  var body = document.body;

  /* ---------- Theme ---------- */
  var stored = null;
  try { stored = localStorage.getItem("aifh-theme"); } catch (e) {}
  if (stored) root.setAttribute("data-theme", stored);
  function currentTheme() {
    return root.getAttribute("data-theme") ||
      (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  }
  function setTheme(t) {
    root.setAttribute("data-theme", t);
    try { localStorage.setItem("aifh-theme", t); } catch (e) {}
    var b = document.getElementById("theme-btn");
    if (b) b.setAttribute("aria-label", "Switch to " + (t === "dark" ? "light" : "dark") + " theme");
  }
  var themeBtn = document.getElementById("theme-btn");
  if (themeBtn) themeBtn.addEventListener("click", function () {
    setTheme(currentTheme() === "dark" ? "light" : "dark");
  });

  /* ---------- Mobile nav ---------- */
  var menuBtn = document.getElementById("menu-btn");
  if (menuBtn) menuBtn.addEventListener("click", function () { body.classList.toggle("nav-open"); });
  document.addEventListener("click", function (e) {
    if (body.classList.contains("nav-open") && !e.target.closest(".sidebar") && !e.target.closest("#menu-btn"))
      body.classList.remove("nav-open");
  });

  /* ---------- Reading progress ---------- */
  var bar = document.querySelector(".progress");
  var article = document.querySelector(".chapter") || document.querySelector(".content");
  function onScroll() {
    if (!bar || !article) return;
    var top = article.offsetTop;
    var h = article.offsetHeight - window.innerHeight;
    var p = h > 0 ? (window.scrollY - top) / h : 0;
    bar.style.width = Math.max(0, Math.min(1, p)) * 100 + "%";
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Copy code ---------- */
  document.querySelectorAll(".codeblock").forEach(function (block) {
    var btn = block.querySelector(".copy");
    var pre = block.querySelector("pre");
    if (!btn || !pre) return;
    btn.addEventListener("click", function () {
      var text = pre.innerText;
      navigator.clipboard && navigator.clipboard.writeText(text).then(function () {
        var old = btn.textContent; btn.textContent = "Copied";
        setTimeout(function () { btn.textContent = old; }, 1400);
      });
    });
  });

  /* ---------- Scrollspy (on-this-page) ---------- */
  var subLinks = {};
  document.querySelectorAll(".subnav a").forEach(function (a) {
    var id = a.getAttribute("href").split("#")[1];
    if (id) subLinks[id] = a;
  });
  var heads = Array.prototype.slice.call(document.querySelectorAll(".prose h2[id], .prose h3[id]"));
  if (heads.length && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var a = subLinks[en.target.id];
        if (!a) return;
        if (en.isIntersecting) {
          Object.keys(subLinks).forEach(function (k) { subLinks[k].classList.remove("active"); });
          a.classList.add("active");
        }
      });
    }, { rootMargin: "-10% 0px -75% 0px" });
    heads.forEach(function (h) { io.observe(h); });
  }

  /* ---------- Keyboard nav ---------- */
  function go(rel) {
    var a = document.querySelector(".prevnext a." + rel);
    if (a) window.location.href = a.getAttribute("href");
  }
  document.addEventListener("keydown", function (e) {
    if (e.target.matches("input, textarea")) {
      if (e.key === "Escape") closeSearch();
      return;
    }
    if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || e.key === "/") { e.preventDefault(); openSearch(); }
    else if (e.key === "Escape") closeSearch();
    else if (e.key === "ArrowLeft") go("prev");
    else if (e.key === "ArrowRight") go("next");
    else if (e.key === "j") window.scrollBy({ top: window.innerHeight * 0.5, behavior: "smooth" });
    else if (e.key === "k") window.scrollBy({ top: -window.innerHeight * 0.5, behavior: "smooth" });
  });

  /* ---------- Search ---------- */
  var modal = document.getElementById("search-modal");
  var input = document.getElementById("search-input");
  var results = document.getElementById("search-results");
  var sel = -1;
  document.querySelectorAll("[data-search-open]").forEach(function (b) {
    b.addEventListener("click", openSearch);
  });
  function openSearch() { if (!modal) return; modal.classList.add("open"); input.value = ""; render(""); setTimeout(function () { input.focus(); }, 20); }
  function closeSearch() { if (modal) modal.classList.remove("open"); }
  if (modal) modal.querySelector(".scrim").addEventListener("click", closeSearch);

  function esc(s) { return s.replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); }
  function highlight(text, q) {
    if (!q) return esc(text);
    var i = text.toLowerCase().indexOf(q.toLowerCase());
    if (i < 0) return esc(text);
    var start = Math.max(0, i - 40);
    var snippet = (start > 0 ? "…" : "") + text.slice(start, i + q.length + 90);
    return esc(snippet.slice(0, i - start)) + "<mark>" + esc(snippet.substr(i - start, q.length)) + "</mark>" + esc(snippet.slice(i - start + q.length));
  }
  function render(q) {
    if (!results) return;
    var idx = window.SEARCH_INDEX || [];
    var items = [];
    if (q.trim()) {
      var ql = q.toLowerCase();
      idx.forEach(function (e) {
        var hay = (e.title + " " + e.section + " " + e.text).toLowerCase();
        var pos = hay.indexOf(ql);
        if (pos >= 0) items.push({ e: e, score: (e.title.toLowerCase().indexOf(ql) >= 0 ? 0 : 1) + pos / 5000 });
      });
      items.sort(function (a, b) { return a.score - b.score; });
      items = items.slice(0, 20);
    }
    if (!q.trim()) { results.innerHTML = '<div class="search-empty">Type to search the book · <kbd>esc</kbd> to close</div>'; return; }
    if (!items.length) { results.innerHTML = '<div class="search-empty">No matches for “' + esc(q) + '”</div>'; return; }
    results.innerHTML = items.map(function (it, n) {
      var e = it.e;
      return '<a href="' + e.url + '" class="' + (n === 0 ? "sel" : "") + '">' +
        '<div class="r-ch">' + esc(e.chapter) + (e.section ? " · " + esc(e.section) : "") + "</div>" +
        '<div class="r-t">' + esc(e.title) + "</div>" +
        '<div class="r-x">' + highlight(e.text, q) + "</div></a>";
    }).join("");
    sel = 0;
  }
  if (input) input.addEventListener("input", function () { render(input.value); });
  if (input) input.addEventListener("keydown", function (e) {
    var links = results.querySelectorAll("a");
    if (!links.length) return;
    if (e.key === "ArrowDown") { e.preventDefault(); sel = Math.min(links.length - 1, sel + 1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); sel = Math.max(0, sel - 1); }
    else if (e.key === "Enter") { if (links[sel]) window.location.href = links[sel].getAttribute("href"); return; }
    else return;
    links.forEach(function (l) { l.classList.remove("sel"); });
    links[sel].classList.add("sel");
    links[sel].scrollIntoView({ block: "nearest" });
  });
})();
