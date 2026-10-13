#!/usr/bin/env python3
"""Rebuild assets/ from the Kip app repo and the store-screenshot captures.

Screenshots come from the raw app captures behind the store set (system bars already stripped), fonts from the
app's own Bricolage Grotesque and Manrope (docs/design/tokens.md §2). The app has no icon yet, so the site mark is
drawn from the wordmark. Everything is served from this site, so the pages make no third-party requests.

Needs Pillow, fontTools and brotli:
    python3 -m venv .venv && .venv/bin/pip install pillow fonttools brotli
    .venv/bin/python scripts/build_assets.py [--app ../ki] [--shots <dir>]
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

SHOTS = ["01-push-ladder", "02-easier", "03-pull-detail", "04-paths", "04-set", "05-rest", "06-home", "07-end", "08-charts"]
SHOT_WIDTHS = {"": 320, "@2x": 640}
DEFAULT_SHOTS = Path.home() / "Desktop/kip-aso/kreatif/ham/_prep/android-phone"
BASE_PATH = "/ki-website/"

# Theme A (docs/design/tokens.md §1)
BACKGROUND = (0x11, 0x13, 0x15)
SURFACE = (0x1A, 0x1D, 0x21)
BORDER = (0x2C, 0x30, 0x36)
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


def _rounded(image, radius: int):
    from PIL import Image, ImageDraw

    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width - 1, image.height - 1), radius=radius, fill=255)
    return mask


def _capture(shots_dir: Path, name: str):
    """A prepared capture, or a raw one from the sibling folder with the Android system bars stripped the way the
    store renderer does it (status bar cropped, gesture handle painted over; heights in bars.json)."""
    import json

    from PIL import Image

    prepared = shots_dir / f"{name}.png"
    if prepared.exists():
        return Image.open(prepared).convert("RGB")
    raw_dir = shots_dir.parent.parent / shots_dir.name
    bars = json.loads((raw_dir / "bars.json").read_text())
    image = Image.open(raw_dir / f"{name}.png").convert("RGB")
    width, height = image.size
    fill = image.crop((0, height - bars["nav"] - 2, width, height - bars["nav"] - 1)).resize((width, bars["nav"]))
    image.paste(fill, (0, height - bars["nav"]))
    return image.crop((0, bars["status"], width, height))


def _mark(size: int, bricolage: Path):
    """The site mark: "k" and the accent dot of the "kip." wordmark on the app background."""
    from PIL import Image, ImageDraw, ImageFont

    scale = 4
    side = size * scale
    image = Image.new("RGB", (side, side), BACKGROUND)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(bricolage), round(side * 0.74))
    left, top, right, bottom = draw.textbbox((0, 0), "k", font=font)
    dot = round(side * 0.085)
    gap = round(side * 0.035)
    width = (right - left) + gap + dot * 2
    x = (side - width) // 2 - left
    y = (side - (bottom - top)) // 2 - top
    draw.text((x, y), "k", font=font, fill=TEXT)
    cx = x + right + gap + dot
    cy = y + bottom - dot
    draw.ellipse((cx - dot, cy - dot, cx + dot, cy + dot), fill=ACCENT)
    return image.resize((size, size), Image.LANCZOS)


def build(app: Path, shots_dir: Path) -> None:
    from fontTools.ttLib import TTFont
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    fonts = app / "shared/src/commonMain/composeResources/font"
    licenses = app / "shared/src/commonMain/composeResources/files/licenses"

    shots = ASSETS / "img/shots"
    shots.mkdir(parents=True, exist_ok=True)
    for name in SHOTS:
        src = _capture(shots_dir, name)
        for suffix, width in SHOT_WIDTHS.items():
            height = round(src.height * width / src.width)
            out = shots / f"{name}{suffix}.webp"
            src.resize((width, height), Image.LANCZOS).save(out, "WEBP", quality=84, method=6)
            print(f"{out.relative_to(SITE)}  {width}x{height}  {out.stat().st_size // 1024} KB")

    out_fonts = ASSETS / "fonts"
    out_fonts.mkdir(parents=True, exist_ok=True)
    # Headings are always 800 at normal width; the optical-size axis stays so large type keeps its shapes.
    _subset_woff2(_instance(fonts / "bricolage_grotesque.ttf", {"wght": 800, "wdth": 100}), out_fonts / "bricolage-800.woff2")
    _subset_woff2(TTFont(fonts / "manrope.ttf"), out_fonts / "manrope.woff2")  # variable, 200–800
    shutil.copyfile(licenses / "ofl_bricolage_grotesque.txt", out_fonts / "OFL-bricolage-grotesque.txt")
    shutil.copyfile(licenses / "ofl_manrope.txt", out_fonts / "OFL-manrope.txt")

    img = ASSETS / "img"
    with tempfile.TemporaryDirectory() as tmp:
        bricolage = Path(tmp) / "bricolage-800.ttf"
        manrope = Path(tmp) / "manrope-600.ttf"
        _instance(fonts / "bricolage_grotesque.ttf", {"wght": 800, "wdth": 100, "opsz": 96}).save(bricolage)
        _instance(fonts / "manrope.ttf", {"wght": 600}).save(manrope)

        for name, size in {"icon-192.png": 192, "apple-touch-icon.png": 180, "favicon-32.png": 32}.items():
            _mark(size, bricolage).save(img / name, optimize=True)

        # Social card: wordmark, the store headline and the home screen.
        og = Image.new("RGB", (1200, 630), BACKGROUND)
        glow = Image.new("RGB", og.size, BACKGROUND)
        ImageDraw.Draw(glow).ellipse((700, -260, 1400, 360), fill=(0x2A, 0x33, 0x1C))
        og = Image.blend(og, glow.filter(ImageFilter.GaussianBlur(140)), 0.9)
        draw = ImageDraw.Draw(og)
        word = ImageFont.truetype(str(bricolage), 56)
        head = ImageFont.truetype(str(bricolage), 66)
        body = ImageFont.truetype(str(manrope), 30)
        draw.text((80, 84), "kip", font=word, fill=TEXT)
        draw.ellipse((80 + draw.textlength("kip", font=word) + 4, 84 + 41, 80 + draw.textlength("kip", font=word) + 16, 84 + 53), fill=ACCENT)
        draw.text((80, 236), "From wall push-ups", font=head, fill=TEXT)
        draw.text((80, 312), "to ", font=head, fill=TEXT)
        draw.text((80 + draw.textlength("to ", font=head), 312), "your first push-up", font=head, fill=ACCENT)
        draw.text((80, 424), "Bodyweight strength at home,", font=body, fill=TEXT_SECONDARY)
        draw.text((80, 466), "step by step.", font=body, fill=TEXT_SECONDARY)
        phone = _capture(shots_dir, "06-home")
        phone = phone.resize((300, round(phone.height * 300 / phone.width)), Image.LANCZOS)
        frame = Image.new("RGB", (phone.width + 20, phone.height + 20), (0x0B, 0x0C, 0x0D))
        ImageDraw.Draw(frame).rounded_rectangle((0, 0, frame.width - 1, frame.height - 1), radius=44, outline=BORDER, width=2)
        frame.paste(phone, (10, 10), _rounded(phone, 34))
        og.paste(frame, (820, 70), _rounded(frame, 44))
        og.save(img / "og.png", optimize=True)
        print(f"assets/img/og.png  {(img / 'og.png').stat().st_size // 1024} KB")


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
    parser.add_argument("--shots", type=Path, default=DEFAULT_SHOTS)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        build(args.app.resolve(), args.shots.resolve())
    sys.exit(check())


if __name__ == "__main__":
    main()
