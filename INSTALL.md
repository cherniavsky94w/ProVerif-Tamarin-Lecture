# Установка інструментів

Потрібні: **ProVerif 2.05** (ПР1), **Tamarin 1.12** разом із **Maude** (ПР2) і **Graphviz** (рисунки трас атак в обох інструментах). Установіть усе до першого заняття: збирання з вихідних кодів може тривати довше за пару.

Офіційні сторінки, з яких узято команди нижче:

- ProVerif: <https://bblanche.gitlabpages.inria.fr/proverif/> (розділ Install)
- Tamarin: <https://tamarin-prover.com/manual/master/book/002_installation.html>

## macOS

```bash
# Homebrew: https://brew.sh
brew install graphviz opam
brew install tamarin-prover/tap/tamarin-prover   # разом із Maude

opam init            # одноразово; погодьтеся оновити файл профілю оболонки
eval $(opam env)
opam install proverif
```

## Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install graphviz opam
opam init
eval $(opam env)
opam install proverif
```

Tamarin на Linux встановлюється одним зі способів, які наводить офіційна документація:

- через Homebrew для Linux: `brew install tamarin-prover/tap/tamarin-prover`;
- готовим бінарним файлом зі сторінки релізів <https://github.com/tamarin-prover/tamarin-prover/releases> (тоді Maude версії не нижче 2.7.1 потрібно встановити окремо й додати в `PATH`);
- Arch Linux: `pacman -S tamarin-prover`;
- Nix: `nix-env -i tamarin-prover`.

## Windows

Рекомендований шлях: WSL2 з Ubuntu, далі інструкція для Linux вище.

1. У PowerShell від імені адміністратора: `wsl --install`, перезавантажити комп'ютер.
2. Відкрити застосунок Ubuntu і виконати команди розділу «Linux».
3. Графічний інтерфейс Tamarin (`tamarin-prover interactive`) відкривати у браузері Windows за адресою <http://127.0.0.1:3001>.

Для ProVerif існує також бінарний пакет для Windows на офіційній сторінці (розділ Install), але на заняттях використовуємо WSL, щоб команди в усіх були однакові.

## Перевірка установки

```bash
proverif -help | head -1        # має вивести: Proverif 2.05. ...
tamarin-prover --version | head -2
maude --version
dot -V                          # Graphviz
tamarin-prover test             # самоперевірка; наприкінці: "All tests successful."
```

Далі перевірте, що обидва інструменти справді працюють на моделях курсу:

```bash
cd lab1-proverif-jwt/warmup
proverif nspk.pv | grep RESULT
# очікувано: два рядки RESULT ... is false.

cd ../../lab2-tamarin-oauth/warmup
tamarin-prover --prove nspk.spthy | tail -8
# очікувано: types і executable verified, nr_secrecy і
# responder_injective_agreement falsified
```

## Корисні режими

| Що | Команда |
|---|---|
| ProVerif: рисунок траси атаки (PDF) | `mkdir out && proverif -graph out model.pv` → `out/trace1.pdf`, … |
| ProVerif: звіт у HTML | `mkdir html && proverif -html html model.pv` → відкрити `html/index.html` |
| ProVerif: детальна траса | додати в модель рядок `set traceDisplay = long.` |
| Tamarin: довести всі леми | `tamarin-prover --prove model.spthy` |
| Tamarin: одна лема | `tamarin-prover --prove=session_integrity model.spthy` |
| Tamarin: графічний інтерфейс | `tamarin-prover interactive .` → <http://127.0.0.1:3001> |

## Типові проблеми

- `proverif: command not found` після `opam install`: не виконано `eval $(opam env)` у поточній оболонці.
- Tamarin повідомляє про відсутній або застарілий Maude: перевірте `maude --version` і `PATH`.
- `proverif -graph` не створює PDF: не встановлено Graphviz (`dot -V`).
- Tamarin довго «думає» над власною моделлю: перевіряйте леми по одній (`--prove=<лема>`), дивіться в графічному інтерфейсі, на якій цілі зациклився пошук; див. лекцію, слайд про часткові деконструкції та леми `[sources]`.
