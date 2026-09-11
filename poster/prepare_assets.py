#!/usr/bin/env python3
"""
Prepare raster assets for the SENSEI poster.

Rasterizes the vector figures (architecture diagram) at high resolution,
trims surrounding whitespace, and copies/normalizes the screenshot and
logos into poster/assets/ so generate_poster.py can embed them.

Run once (or whenever a source file changes):
    .venv/bin/python3 poster/prepare_assets.py
"""
import os
import pymupdf  # PyMuPDF
import qrcode
from PIL import Image, ImageChops

GITHUB_REPOS = {
    "qr-sensei.png": "https://github.com/hlt-mt/sensei",
    "qr-subtitler.png": "https://github.com/hlt-mt/subtitler",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "poster", "assets")
os.makedirs(ASSETS, exist_ok=True)


def trim(img: Image.Image, pad: int = 0, bg=(255, 255, 255)) -> Image.Image:
    """Crop away uniform-background margins around the content."""
    rgb = img.convert("RGB") if img.mode != "RGB" else img
    bg_img = Image.new("RGB", rgb.size, bg)
    diff = ImageChops.difference(rgb, bg_img)
    bbox = diff.getbbox()
    if not bbox:
        return img
    l, t, r, b = bbox
    l = max(l - pad, 0)
    t = max(t - pad, 0)
    r = min(r + pad, img.width)
    b = min(b + pad, img.height)
    return img.crop((l, t, r, b))


def render_pdf_page(pdf_path: str, dpi: int) -> Image.Image:
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    mode = "RGB"
    img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
    doc.close()
    return img


def main():
    # --- Architecture diagram (Figure 1 of the paper) -------------------
    diagram = render_pdf_page(os.path.join(ROOT, "sensei-diagram.pdf"), dpi=600)
    diagram = trim(diagram, pad=8)
    diagram.save(os.path.join(ASSETS, "diagram.png"))
    print("diagram.png", diagram.size)

    # --- Interface screenshot --------------------------------------------
    screenshot = Image.open(os.path.join(ROOT, "sensei.png")).convert("RGBA")
    screenshot = trim(screenshot.convert("RGB"), pad=0).convert("RGBA")
    screenshot.save(os.path.join(ASSETS, "screenshot.png"))
    print("screenshot.png", screenshot.size)

    # --- Logos: normalize into assets/ (no re-encoding needed, just copy) -
    unitn = Image.open(os.path.join(ROOT, "marchio_unitrento_colore_it.png")).convert("RGBA")
    unitn.save(os.path.join(ASSETS, "marchio_unitrento_colore_it.png"))
    print("marchio_unitrento_colore_it.png", unitn.size)

    fbk = Image.open(os.path.join(ROOT, "fbk-logo.png")).convert("RGBA")
    fbk.save(os.path.join(ASSETS, "fbk-logo.png"))
    print("fbk-logo.png", fbk.size)

    # --- QR codes linking to the two GitHub repos (transparent background) -
    for filename, url in GITHUB_REPOS.items():
        qr = qrcode.make(url, border=1).convert("RGBA")
        pixels = qr.getdata()
        transparent = [
            (0, 0, 0, 0) if (r, g, b) > (200, 200, 200) else (0, 0, 0, 255)
            for r, g, b, a in pixels
        ]
        qr.putdata(transparent)
        qr.save(os.path.join(ASSETS, filename))
        print(filename, qr.size)


if __name__ == "__main__":
    main()
