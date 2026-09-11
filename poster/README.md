# SENSEI poster (A0, portrait, CLiC-it 2026)

Two scripts regenerate `poster.svg` from the source PDFs/images in the
parent folder. Nothing is hand-drawn: text is native SVG (easy to edit),
the architecture diagram / screenshot / logos are embedded as base64 PNGs.

## Setup (once)

```bash
python3 -m venv .venv          # from the sensei-poster/ root
.venv/bin/pip install -r requirements.txt
```

Requires the DejaVu Sans font at `/usr/share/fonts/truetype/dejavu/`
(used both for on-page text and for measuring text to wrap it correctly;
pre-installed on most Debian/Ubuntu systems).

## Build

```bash
.venv/bin/python3 poster/prepare_assets.py   # rasterizes diagram PDF, crops logos, makes QR code
.venv/bin/python3 poster/generate_poster.py  # writes poster/poster.svg
```

Re-run `prepare_assets.py` only if you replace a source file (e.g. a new
`sensei-diagram.pdf`). Re-run `generate_poster.py` after any text/layout tweak.

## Editing

- **Copy/text**: edit the string literals in `generate_poster.py` (section
  bullets, stats, table rows, etc.) and re-run the script — wrapping is
  recomputed automatically against real font metrics.
- **Colors/layout**: constants near the top of `generate_poster.py`
  (`PALETTE`, `MARGIN`, `COL_W`, `HEADER_H`, `FOOTER_H`...).
- **Fine, one-off tweaks**: `poster.svg` is plain, readable SVG — open it
  directly in Inkscape and nudge things by hand; just don't re-run the
  generator afterwards or it will overwrite your edits.

## Print

`poster.svg` has `width="841mm" height="1189mm"` (A0 portrait) baked into
the viewBox, so any converter renders it at true size, e.g.:

```bash
# via a browser / headless Chrome, or:
.venv/bin/python3 -c "import cairosvg; cairosvg.svg2pdf(url='poster/poster.svg', write_to='poster/poster.pdf')"
```
