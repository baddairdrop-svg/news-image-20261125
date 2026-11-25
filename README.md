# World News in One Image — 25 November 2026

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/baddairdrop-svg/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/baddairdrop-svg/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

A program that draws one image summing up the world's news of
Wednesday 25 November 2026, for the make.fun bounty
[news-image-20261125](https://make.fun/bounty/news-image-20261125),
entered by **@badd-airdrop2**.

## The image

A newspaper front page, 1024x1024: a header naming the day, six panels
(one per main story, each with a drawn scene, a headline, one big figure
and one short sub-line), and a footer strip with three smaller stories.

1. **Space** — Pakistan's first astronaut reaches orbit aboard
   Shenzhou-24 to the Tiangong station.
2. **Ukraine** — Zelenskyy confirms Ukraine struck Russian ships: a
   cargo ship hit in the Gulf of Finland, a warship sunk off Benghazi.
3. **Markets** — AI stocks tumble on tariff fears: Nvidia -6%, Micron
   -11%, Nasdaq -1.5%.
4. **Gaza** — an Israeli strike kills Hamas security chief Naeem Abu
   Nahel in Gaza City.
5. **Yemen** — airstrikes kill dozens: 17 in Hodeida, 26 in Lahj.
6. **Nepal** — a magnitude 5.6 earthquake in Koshi province, near the
   Tibet border, at 07:17.

Footer: Malaysia to return 6,500+ Rohingya refugees to Myanmar; AIDS
deaths at 570,000, the lowest in 20+ years; Trump awards the Medal of
Freedom to Giuliani. Sources: Reuters, AP, Euronews.

No quotes, numbers or faces are invented, and no real person is drawn.

## How it runs

`main.py` is pure Python 3 standard library only (no network, no fonts
on disk, no randomness, no clock). It draws the picture with a small
5x7 bitmap font and a hand-written PNG encoder, and writes it to
`/output/entry.png`. Running it twice writes the same bytes.

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```
