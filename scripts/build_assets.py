#!/usr/bin/env python3
"""Rebuild assets/ from the Ki app repo and the approved store creatives (D124).

Sources, all outside this repo:
  <kreatif>/logo/final/app-store-1024.png   the app icon ("k.")
  <kreatif>/v2/app-store/iphone-6.9/*.png   the eight store frames (round 2)
  <kreatif>/v2/foto/*.jpg                   the photos behind them (AI images made in Google Flow)
  <kreatif>/ham/_prep/android-phone/*.png   raw app captures, system bars stripped
  <app>/shared/.../font/*.ttf               Bricolage Grotesque and Manrope (docs/design/tokens.md §2)

Everything is served from this site, so the pages make no third-party requests.

Needs Pillow, fontTools and brotli:
    python3 -m venv .venv && .venv/bin/pip install pillow fonttools brotli
    .venv/bin/python scripts/build_assets.py [--app ../ki] [--kreatif <dir>]
    .venv/bin/python scripts/build_assets.py --check   # glyph coverage + links only
"""
from __future__ import annotations

import argparse
import html.parser
import re
import shutil
import sys
import tempfile
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
ASSETS = SITE / "assets"

DEFAULT_KREATIF = Path.home() / "Desktop/kip-aso/kreatif"
SHOTS = ["01-push-ladder", "02-easier", "04-set", "08-charts"]
SHOT_WIDTHS = {"": 320, "@2x": 640}
FRAMES = ["01", "02", "03", "04", "05", "06", "07", "08"]
FRAME_WIDTHS = {"": 360, "@2x": 720}
# photo -> (source name, output widths)
PHOTOS = {"wall-push-up": ("feature", (900, 1600, 2400)), "equipment": ("equipment", (560, 1120)), "rest": ("rest", (560, 1120))}
BASE_PATH = "/ki-website/"

# Theme A (docs/design/tokens.md §1)
BACKGROUND = (0x11, 0x13, 0x15)
TEXT = (0xF3, 0xF2, 0xEF)
TEXT_SECONDARY = (0xA9, 0xAE, 0xB5)
ACCENT = (0xC6, 0xF3, 0x6B)

# Basic Latin, Latin-1 and the punctuation the pages use.
UNICODES = (list(range(0x20, 0x7F)) + list(range(0xA0, 0x100))
            + [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026, 0x203A, 0x2192, 0x2022, 0x2212])


def _instance(src: Path, axes: dict):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    return instancer.instantiateVariableFont(TTFont(src), axes)


def _subset_woff2(font, out: Path) -> None:
    from fontTools import subset

    options = subset.Options()
    options.layout_features = ["*"]
    options.flavor = "woff2"
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=UNICODES)
    subsetter.subset(font)
    font.flavor = "woff2"
    font.save(out)
    print(f"{out.relative_to(SITE)}  {out.stat().st_size // 1024} KB")


def _webp(image, out: Path, width: int, quality: int) -> None:
    from PIL import Image

    height = round(image.height * width / image.width)
    image.resize((width, height), Image.LANCZOS).save(out, "WEBP", quality=quality, method=6)
    print(f"{out.relative_to(SITE)}  {width}x{height}  {out.stat().st_size // 1024} KB")


def build(app: Path, kreatif: Path) -> None:
    from fontTools.ttLib import TTFont
    from PIL import Image, ImageDraw, ImageFont

    fonts = app / "shared/src/commonMain/composeResources/font"
    licenses = app / "shared/src/commonMain/composeResources/files/licenses"
    img = ASSETS / "img"

    for folder in ("shots", "store", "photos"):  # rebuilt from scratch, so a dropped image does not linger
        shutil.rmtree(img / folder, ignore_errors=True)
        (img / folder).mkdir(parents=True)

    for name in SHOTS:
        src = Image.open(kreatif / "ham/_prep/android-phone" / f"{name}.png").convert("RGB")
        for suffix, width in SHOT_WIDTHS.items():
            _webp(src, img / "shots" / f"{name}{suffix}.webp", width, 84)

    for name in FRAMES:
        src = Image.open(kreatif / "v2/app-store/iphone-6.9" / f"{name}.png").convert("RGB")
        for suffix, width in FRAME_WIDTHS.items():
            _webp(src, img / "store" / f"{name}{suffix}.webp", width, 82)

    for name, (source, widths) in PHOTOS.items():
        src = Image.open(kreatif / "v2/foto" / f"{source}.jpg").convert("RGB")
        for width in widths:
            _webp(src, img / "photos" / f"{name}-{width}.webp", width, 78)

    icon = Image.open(kreatif / "logo/final/app-store-1024.png").convert("RGB")
    for name, size in {"icon-192.png": 192, "apple-touch-icon.png": 180, "favicon-32.png": 32}.items():
        icon.resize((size, size), Image.LANCZOS).save(img / name, optimize=True)

    out_fonts = ASSETS / "fonts"
    out_fonts.mkdir(parents=True, exist_ok=True)
    # Headings are always 800 at normal width; the optical-size axis stays so large type keeps its shapes.
    _subset_woff2(_instance(fonts / "bricolage_grotesque.ttf", {"wght": 800, "wdth": 100}), out_fonts / "bricolage-800.woff2")
    _subset_woff2(TTFont(fonts / "manrope.ttf"), out_fonts / "manrope.woff2")  # variable, 200–800
    shutil.copyfile(licenses / "ofl_bricolage_grotesque.txt", out_fonts / "OFL-bricolage-grotesque.txt")
    shutil.copyfile(licenses / "ofl_manrope.txt", out_fonts / "OFL-manrope.txt")

    # Social card: the wall push-up photo on the right, wordmark and the store headline on the left.
    with tempfile.TemporaryDirectory() as tmp:
        bricolage = Path(tmp) / "bricolage-800.ttf"
        manrope = Path(tmp) / "manrope-600.ttf"
        _instance(fonts / "bricolage_grotesque.ttf", {"wght": 800, "wdth": 100, "opsz": 96}).save(bricolage)
        _instance(fonts / "manrope.ttf", {"wght": 600}).save(manrope)

        width, height = 1200, 630
        photo = Image.open(kreatif / "v2/foto/feature.jpg").convert("RGB")
        photo = photo.resize((round(photo.width * height / photo.height), height), Image.LANCZOS)
        og = Image.new("RGB", (width, height), BACKGROUND)
        left = width - photo.width + 80  # the wall at the far right can lose a little
        og.paste(photo, (left, 0))
        fade = Image.new("L", (width, 1))
        fade.putdata([255 if x < left + 40 else max(0, round(255 * (1 - (x - left - 40) / 420))) for x in range(width)])
        og.paste(Image.new("RGB", (width, height), BACKGROUND), (0, 0), fade.resize((width, height)))
        draw = ImageDraw.Draw(og)
        word = ImageFont.truetype(str(bricolage), 56)
        head = ImageFont.truetype(str(bricolage), 58)
        body = ImageFont.truetype(str(manrope), 28)
        draw.text((72, 96), "ki", font=word, fill=TEXT)
        dot = 72 + draw.textlength("ki", font=word) + 4
        draw.ellipse((dot, 96 + 41, dot + 12, 96 + 53), fill=ACCENT)
        draw.text((72, 250), "From wall push-ups", font=head, fill=TEXT)
        draw.text((72, 318), "to ", font=head, fill=TEXT)
        draw.text((72 + draw.textlength("to ", font=head), 318), "your first push-up", font=head, fill=ACCENT)
        draw.text((72, 420), "Bodyweight strength at home,", font=body, fill=TEXT_SECONDARY)
        draw.text((72, 458), "step by step.", font=body, fill=TEXT_SECONDARY)
        og.save(img / "og.jpg", "JPEG", quality=86, optimize=True, progressive=True)
        (img / "og.png").unlink(missing_ok=True)
        print(f"assets/img/og.jpg  {(img / 'og.jpg').stat().st_size // 1024} KB")


class _Collector(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.refs: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        for key, value in attrs:
            if key in ("href", "src", "srcset") and value:
                self.refs += [part.strip().split(" ")[0] for part in value.split(",")]
            if key in ("alt", "aria-label", "title") and value:
                self.text.append(value)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.text.append(data)


def check() -> int:
    from fontTools.ttLib import TTFont

    problems = 0
    cmaps = {name: set(TTFont(ASSETS / "fonts" / f"{name}.woff2").getBestCmap()) for name in ("bricolage-800", "manrope")}
    for page in sorted(SITE.glob("*.html")):
        collector = _Collector()
        collector.feed(page.read_text(encoding="utf-8"))
        chars = {c for c in "".join(collector.text) if not c.isspace()}
        for name, cmap in cmaps.items():
            missing = sorted(c for c in chars if ord(c) not in cmap)
            if missing:
                problems += 1
                print(f"{page.name}: {name} lacks {''.join(missing)!r}")
        for ref in collector.refs:
            if re.match(r"^(https?:|mailto:|#|data:)", ref):
                continue
            path = ref.split("#")[0].split("?")[0]
            if path.startswith(BASE_PATH):  # 404.html links absolutely (served for any path)
                path = path[len(BASE_PATH):]
            target = (page.parent / path).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                problems += 1
                print(f"{page.name}: broken link {ref}")
    print("ok" if problems == 0 else f"{problems} problem(s)")
    return 1 if problems else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=Path, default=SITE.parent / "ki")
    parser.add_argument("--kreatif", type=Path, default=DEFAULT_KREATIF)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        build(args.app.resolve(), args.kreatif.resolve())
    sys.exit(check())


if __name__ == "__main__":
    main()
