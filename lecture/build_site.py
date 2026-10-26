#!/usr/bin/env python3
"""Build a self-contained web presentation from the lecture slides.

Reads lecture/slides/project/ (deck.json + one HTML file per slide) and
writes docs/index.html plus docs/assets/, ready for GitHub Pages
(Settings > Pages > Deploy from a branch > main, folder /docs).

    python3 lecture/build_site.py

Keys in the browser: arrows / Space / PageUp / PageDown to move, Home and
End, N toggles the speaker notes, F toggles full screen. Printing the page
(Ctrl/Cmd+P) gives one slide per page, i.e. a PDF of the deck.
"""
import html
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROJECT = HERE / "slides" / "project"
ASSETS = HERE / "slides" / "assets"
OUT = ROOT / "docs"

# Images uploaded to the Slides artifact, by their artifact URL.
BLOBS = {
    "/_blob/3123beb8f833dbb24a8d6f0e9300e042": "assets/nspk_trace.png",
}

X_ARROW = re.compile(
    r'<x-shape kind="arrow-(right|down)" style="background:\s*(#[0-9A-Fa-f]{3,8});\s*'
    r'width:\s*(\d+)px;\s*height:\s*(\d+)px;?"></x-shape>')


def arrow_svg(match: re.Match) -> str:
    kind, color = match.group(1), match.group(2)
    w, h = int(match.group(3)), int(match.group(4))
    if kind == "right":
        head = w * 0.6
        points = (f"0,{h * 0.3} {head},{h * 0.3} {head},0 {w},{h / 2} "
                  f"{head},{h} {head},{h * 0.7} 0,{h * 0.7}")
    else:
        head = h * 0.6
        points = (f"{w * 0.3},0 {w * 0.7},0 {w * 0.7},{head} {w},{head} "
                  f"{w / 2},{h} 0,{head} {w * 0.3},{head}")
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="flex:none" '
            f'aria-hidden="true"><polygon points="{points}" fill="{color}"/></svg>')


def convert(slide: str, sid: str) -> str:
    slide = X_ARROW.sub(arrow_svg, slide)
    for blob, path in BLOBS.items():
        slide = slide.replace(blob, path)
    leftover = re.findall(r"<x-[a-z]+|/_blob/", slide)
    if leftover:
        raise SystemExit(f"{sid}: unsupported element or image left: {leftover}")
    return slide


PAGE = """<!doctype html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{fonts}
<style>
html, body {{ margin: 0; height: 100%; background: #0B1118; overflow: hidden; }}
#stage {{ position: fixed; left: 0; right: 0; top: 0; bottom: 0; display: flex;
  align-items: center; justify-content: center; }}
body.notes #stage {{ bottom: 38vh; }}
#deck {{ width: 1920px; height: 1080px; position: relative; flex: none; }}
#deck > section {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px;
  box-sizing: border-box; overflow: hidden; visibility: hidden; }}
#deck > section.active {{ visibility: visible; }}
#deck section * {{ margin: 0; box-sizing: border-box; }}
#deck h1 {{ font-size: 96px; font-weight: 600; line-height: 1.1; }}
#deck h2 {{ font-size: 64px; font-weight: 600; line-height: 1.15; }}
#deck h3 {{ font-size: 44px; font-weight: 600; line-height: 1.2; }}
#deck p {{ font-size: 32px; line-height: 1.4; }}
#deck ul, #deck ol {{ padding-left: 1.3em; }}
#deck li + li {{ margin-top: 0.2em; }}
#deck table {{ border-collapse: collapse; width: 100%; }}
#deck th, #deck td {{ padding: 0.35em 0.6em; text-align: left; vertical-align: top;
  border-bottom: 1px solid rgba(21, 32, 43, 0.18); }}
#deck th {{ font-weight: 600; border-bottom: 2px solid rgba(21, 32, 43, 0.6); }}
#deck aside {{ display: none; }}
#deck [style*="JetBrains"] {{ font-variant-ligatures: none; }}
#notes {{ display: none; position: fixed; left: 0; right: 0; bottom: 0; height: 38vh;
  overflow: auto; box-sizing: border-box; padding: 16px 28px; background: #F5F3EE;
  color: #15202B; font: 18px/1.55 'IBM Plex Sans', Arial, sans-serif; }}
body.notes #notes {{ display: block; }}
#bar {{ position: fixed; right: 16px; bottom: 12px; display: flex; gap: 6px; align-items: center;
  font: 14px 'IBM Plex Sans', Arial, sans-serif; color: #B8C2CC; opacity: 0.35;
  transition: opacity 0.2s; z-index: 2; }}
#bar:hover {{ opacity: 1; }}
body.notes #bar {{ bottom: calc(38vh + 12px); }}
#bar button {{ font: inherit; color: #F5F3EE; background: #22303E; border: 0;
  border-radius: 6px; padding: 6px 10px; cursor: pointer; }}
@media print {{
  @page {{ size: 1920px 1080px; margin: 0; }}
  html, body {{ height: auto; overflow: visible; background: none; }}
  #stage {{ position: static; display: block; }}
  #deck {{ transform: none !important; width: 1920px; height: auto; }}
  #deck > section {{ position: relative; visibility: visible; break-after: page; }}
  #bar, #notes {{ display: none !important; }}
}}
</style>
</head>
<body>
<div id="stage"><div id="deck">
{slides}
</div></div>
<div id="notes" aria-live="polite"></div>
<div id="bar">
<button id="prev" aria-label="Попередній слайд">←</button>
<span id="count"></span>
<button id="next" aria-label="Наступний слайд">→</button>
<button id="toggle-notes" title="Нотатки доповідача (N)">Нотатки</button>
<button id="toggle-full" title="На весь екран (F)">⛶</button>
</div>
<script>
(function () {{
  var slides = Array.prototype.slice.call(document.querySelectorAll('#deck > section'));
  var deck = document.getElementById('deck'), stage = document.getElementById('stage');
  var notes = document.getElementById('notes'), count = document.getElementById('count');
  var i = 0;
  function fit() {{
    var s = Math.min(stage.clientWidth / 1920, stage.clientHeight / 1080);
    deck.style.transform = 'scale(' + s + ')';
  }}
  function show(n) {{
    i = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach(function (el, k) {{ el.classList.toggle('active', k === i); }});
    var aside = slides[i].querySelector('aside');
    notes.textContent = aside ? aside.textContent.trim() : '';
    count.textContent = (i + 1) + ' / ' + slides.length;
    if (location.hash !== '#' + (i + 1)) history.replaceState(null, '', '#' + (i + 1));
  }}
  function fromHash() {{
    var n = parseInt(location.hash.slice(1), 10);
    show(isNaN(n) ? 0 : n - 1);
  }}
  function toggleNotes() {{ document.body.classList.toggle('notes'); fit(); }}
  function toggleFull() {{
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen();
  }}
  document.addEventListener('keydown', function (e) {{
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var k = e.key;
    if (k === 'ArrowRight' || k === 'PageDown' || k === ' ') {{ show(i + 1); e.preventDefault(); }}
    else if (k === 'ArrowLeft' || k === 'PageUp') {{ show(i - 1); e.preventDefault(); }}
    else if (k === 'Home') show(0);
    else if (k === 'End') show(slides.length - 1);
    else if (k === 'n' || k === 'N') toggleNotes();
    else if (k === 'f' || k === 'F') toggleFull();
  }});
  document.getElementById('prev').onclick = function () {{ show(i - 1); }};
  document.getElementById('next').onclick = function () {{ show(i + 1); }};
  document.getElementById('toggle-notes').onclick = toggleNotes;
  document.getElementById('toggle-full').onclick = toggleFull;
  var x0 = null;
  stage.addEventListener('touchstart', function (e) {{ x0 = e.touches[0].clientX; }}, {{ passive: true }});
  stage.addEventListener('touchend', function (e) {{
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0; x0 = null;
    if (Math.abs(dx) > 40) show(i + (dx < 0 ? 1 : -1));
  }});
  window.addEventListener('resize', fit);
  window.addEventListener('hashchange', fromHash);
  fit(); fromHash();
}})();
</script>
</body>
</html>
"""


def main() -> None:
    deck = json.loads((PROJECT / "deck.json").read_text())
    fonts = "\n".join(
        f'<link rel="stylesheet" href="{html.escape(face["href"])}">'
        for face in deck["faces"].values() if "href" in face)
    slides = "\n".join(
        convert((PROJECT / "slides" / f"{sid}.html").read_text().strip(), sid)
        for sid in deck["order"])
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(
        PAGE.format(title=html.escape(deck["title"]), fonts=fonts, slides=slides))
    shutil.copytree(ASSETS, OUT / "assets", dirs_exist_ok=True)
    (OUT / ".nojekyll").write_text("")
    print(f"wrote {OUT / 'index.html'}: {len(deck['order'])} slides")


if __name__ == "__main__":
    main()
