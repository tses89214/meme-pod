# Fonts

`fonts/` is gitignored (large binaries, not committed). To set up a fresh checkout,
download these and place them at the exact path `design_generator.py`'s `F` dict
expects (paths below are relative to `fonts/`).

| Key | Expected filename | Font | Source |
|---|---|---|---|
| anton | `Anton-Regular.ttf` | Anton | [Google Fonts](https://fonts.google.com/specimen/Anton) |
| bebas | `BebasNeue-Regular.ttf` | Bebas Neue | [Google Fonts](https://fonts.google.com/specimen/Bebas+Neue) |
| abril | `AbrilFatface-Regular.ttf` | Abril Fatface | [Google Fonts](https://fonts.google.com/specimen/Abril+Fatface) |
| oswald | `Oswald.ttf` | Oswald | [Google Fonts](https://fonts.google.com/specimen/Oswald) |
| unifont | `UnifontJP.otf` | GNU Unifont (JP variant) | [unifoundry.com](https://unifoundry.com/unifont/) |
| fredoka | `FredokaOne-Regular.ttf` | Fredoka One | [Google Fonts](https://fonts.google.com/specimen/Fredoka+One) |
| dancing | `DancingScript.ttf` | Dancing Script | [Google Fonts](https://fonts.google.com/specimen/Dancing+Script) |
| pacifico | `Pacifico-Regular.ttf` | Pacifico | [Google Fonts](https://fonts.google.com/specimen/Pacifico) |
| caveat | `Caveat.ttf` | Caveat | [Google Fonts](https://fonts.google.com/specimen/Caveat) |
| huninn | `jf-openhuninn.ttf` | 芫荽 open-huninn | [justfont/open-huninn-font](https://github.com/justfont/open-huninn-font) |
| genyomin | `GenYoMin2TW-R.otf` | 源樣明體 GenYoMin TW | [ButTaiwan GenYo font family](https://github.com/ButTaiwan) |
| genyogot | `GenYoGothic2TW-R.otf` | 源樣黑體 GenYoGothic TW | [ButTaiwan GenYo font family](https://github.com/ButTaiwan) |
| notoserif | `NotoSerifCJKtc-Regular.otf` | Noto Serif CJK TC | [notofonts/noto-cjk](https://github.com/notofonts/noto-cjk) |
| notosans | `NotoSansTC.ttf` | Noto Sans TC | [Google Fonts](https://fonts.google.com/noto/specimen/Noto+Sans+TC) |
| cubic11 | `Cubic11.ttf` | Cubic 11 (點陣體) | [ArdenDio/Cubic-11](https://github.com/ArdenDio/Cubic-11) |
| trainone | `TrainOne.ttf` | Train One | [Google Fonts](https://fonts.google.com/specimen/Train+One) |

`fallback` in the `F` dict points at the system DejaVu Sans Bold
(`/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`), already present on
Debian/Raspberry Pi OS via the `fonts-dejavu` package.
