# The World in 24 Hours — 25 November 2026

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/baddairdrop-svg/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/baddairdrop-svg/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

A program that draws one image summing up the world's news of
Wednesday 25 November 2026, for the make.fun bounty
[news-image-20261125](https://make.fun/bounty/news-image-20261125),
entered by **@badd-airdrop2**.

## The image

"THE WORLD IN 24 HOURS": the page is one day running midnight to
midnight, 1024x1024. A black masthead, a region-count strip, a
four-block timeline spine (00-06 / 06-12 / 12-18 / 18-24 UTC) with a
red dot at each hero's real hour, three chronological hero cards with
drawn scenes, a five-number stat strip, a ten-card grid numbered 4-13,
a dotted world map with numbered pins, and a red DATE CHECK box.

Every story on the page happened or was first reported on Wednesday
25 November 2026, as the named outlets reported it. Big stories from
24 November (the Zelenskyy ship claim, the Nepal quake, the Gaza
Hamas chief killing, the Giuliani medal, COP31 ending with no deal,
the CIA breach) are listed in the DATE CHECK box as excluded, not
presented as the day's news.

1. **Asia stocks slide** — Kospi -4.7%, Samsung -8.0%, SK Hynix
   -7.5%, Nikkei -3.15%, Taiex -8.2%. (WSJ / Yonhap, 00:00 UTC)
2. **Pakistan in orbit** — Shenzhou-24 lifts off at 00:18 UTC;
   Muhammad Zeeshan Ali, 40, the first Pakistani in orbit, aboard
   Tiangong. (Reuters)
3. **Trump meets NATO chief** — President Trump hosts Mark Rutte at
   Mar-a-Lago in late-afternoon talks. (NATO, 21:00 UTC)

Grid: Shanghai pledges loyalty (4th Politburo member probed since
2025); Seoul Metro strike called off (2,212 job cuts shelved, 500
new hires); EU-Balkans summit in Brussels; Putin meets the Brunei
Sultan in Moscow; Flinders Island bushfire warning; EU seeks
30.4bn euros for borders and asylum; Solomon Islands sign a
security pact with Australia as top partner; 16 Days of Activism
begins; India's Nayi Chetna 5.0 launches; the UN business and human
rights forum closes in Geneva.

No quotes, numbers or faces are invented, and no real person is drawn.
Map and drawings are original vector art.

## How it runs

`main.py` is pure Python 3 standard library only (no network, no fonts
on disk, no randomness, no clock). It draws the picture with a small
5x7 bitmap font and a hand-written PNG encoder, and writes it to
`/output/entry.png`. Running it twice writes the same bytes.

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```
