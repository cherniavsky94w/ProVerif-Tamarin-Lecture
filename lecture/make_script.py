#!/usr/bin/env python3
"""Build lecture/script.md from the speaker notes of the slides.

The slides live in lecture/slides/project/ (deck.json + one HTML file per
slide, the source of the published Slides artifact). Each slide's <aside>
holds its speaker notes. Run after any change to the slides:

    python3 lecture/make_script.py
"""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE / "slides" / "project"
WORDS_PER_MINUTE = 110

DEMOS = {
    "pvdemo": "Демонстрація наживо (1–2 хв): у теці `lab1-proverif-jwt/warmup` виконати `proverif nspk.pv | grep RESULT`.",
    "pvtrace": "Демонстрація наживо (1 хв): `mkdir out && proverif -graph out nspk.pv`, відкрити `out/trace1.pdf`.",
    "tamdemo": "Демонстрація наживо (2 хв): у теці `lab2-tamarin-oauth/warmup` виконати `tamarin-prover --prove nspk.spthy`, потім `tamarin-prover interactive .`, відкрити http://127.0.0.1:3001, лема `nr_secrecy` → autoprove.",
}


def main() -> None:
    deck = json.loads((PROJECT / "deck.json").read_text())
    starts = {s["start"]: s["description"] for s in deck["sections"].values()}
    total = sum(
        len(re.search(r"<aside>(.*?)</aside>", (PROJECT / "slides" / f"{sid}.html").read_text(), re.S)
            .group(1).split())
        for sid in deck["order"])
    speech = round(total / WORDS_PER_MINUTE)
    out = [
        "# Лекція «Формальна верифікація криптографічних протоколів: ProVerif і Tamarin». Текст доповіді",
        "",
        f"Текст збігається з нотатками доповідача у слайдах. Орієнтовно {speech} хв мовлення та 4–5 хв демонстрацій, разом {speech + 4}–{speech + 5} хв. Час біля кожного слайда наростаючим підсумком, з розрахунку {WORDS_PER_MINUTE} слів за хвилину.",
        "",
        "Перед лекцією: перевірити, що на ноутбуці працюють `proverif` і `tamarin-prover`, відкрити термінал у корені модуля.",
        "",
    ]
    words = 0
    for i, sid in enumerate(deck["order"], 1):
        src = (PROJECT / "slides" / f"{sid}.html").read_text()
        title = re.search(r"<h[12][^>]*>(.*?)</h[12]>", src, re.S).group(1)
        title = html.unescape(re.sub(r"<[^>]+>", "", title)).strip()
        note = html.unescape(re.search(r"<aside>(.*?)</aside>", src, re.S).group(1)).strip()
        if sid in starts:
            out += [f"## {starts[sid]}", ""]
        start = words / WORDS_PER_MINUTE
        words += len(note.split())
        out += [f"### Слайд {i}. {title} ({start:.0f}–{words / WORDS_PER_MINUTE:.0f} хв)", "", note, ""]
        if sid in DEMOS:
            out += [f"> {DEMOS[sid]}", ""]
    (HERE / "script.md").write_text("\n".join(out))
    print(f"wrote {HERE / 'script.md'}: {len(deck['order'])} slides, {words} words")


if __name__ == "__main__":
    main()
