"""Create the web-sized images in site/assets/img and site/static from site/source-images.

Run once after changing a source image:  python scripts/make_images.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "site" / "source-images"
IMG = ROOT / "site" / "assets" / "img"
STATIC = ROOT / "site" / "static"
IMG.mkdir(parents=True, exist_ok=True)
STATIC.mkdir(parents=True, exist_ok=True)


def cover_crop(im: Image.Image, width: int, height: int) -> Image.Image:
    """Scale and centre-crop to exactly width x height."""
    scale = max(width / im.width, height / im.height)
    resized = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


cover = Image.open(SRC / "optimizer-step-cover.webp").convert("RGB")
cover_crop(cover, 1200, 630).save(IMG / "og-image.jpg", quality=86, optimize=True, progressive=True)

emblem = Image.open(SRC / "optimizer-step-emblem.webp").convert("RGB")
emblem.resize((72, 72), Image.LANCZOS).save(IMG / "emblem-72.webp", quality=90, method=6)
emblem.resize((144, 144), Image.LANCZOS).save(IMG / "emblem-144.webp", quality=88, method=6)
def small_png(im: Image.Image, size: int, path: Path) -> None:
    """PNG icons with a 256-colour palette: a fraction of the size, no visible loss."""
    im.resize((size, size), Image.LANCZOS).quantize(colors=256, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG).save(path, optimize=True)


small_png(emblem, 192, IMG / "icon-192.png")
small_png(emblem, 512, IMG / "icon-512.png")
small_png(emblem, 180, STATIC / "apple-touch-icon.png")
emblem.save(STATIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

photo = Image.open(SRC / "venkatesh.webp").convert("RGB")
photo.resize((480, 600), Image.LANCZOS).save(IMG / "venkatesh-480.webp", quality=84, method=6)
# Square face crop for the small avatar next to the hero buttons.
face = photo.crop((100, 30, 620, 550)).resize((96, 96), Image.LANCZOS)
face.save(IMG / "venkatesh-96.webp", quality=86, method=6)

for path in sorted(list(IMG.iterdir()) + list(STATIC.iterdir())):
    print(f"{path.relative_to(ROOT)}  {path.stat().st_size // 1024} KB")
