from pathlib import Path
import math

import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "08-writing" / "patent-package-v0.7-zju-format"
PDF = next(PACKAGE.glob("*.pdf"))
OUT = PACKAGE / "qa-pages"
OUT.mkdir(exist_ok=True)
pdf = pdfium.PdfDocument(str(PDF))
thumbs = []
for index in range(len(pdf)):
    page = pdf[index].render(scale=1.5).to_pil().convert("RGB")
    page.save(OUT / f"page-{index + 1:02d}.png")
    thumb = page.copy()
    thumb.thumbnail((300, 420))
    tile = Image.new("RGB", (320, 460), "white")
    tile.paste(thumb, ((320 - thumb.width) // 2, 28))
    ImageDraw.Draw(tile).text((10, 8), f"Page {index + 1}", fill="black")
    thumbs.append(ImageOps.expand(tile, border=1, fill="#777777"))
cols = 4
rows = math.ceil(len(thumbs) / cols)
sheet = Image.new("RGB", (cols * 322, rows * 462), "#dddddd")
for i, thumb in enumerate(thumbs):
    sheet.paste(thumb, ((i % cols) * 322, (i // cols) * 462))
sheet.save(OUT / "contact-sheet.png")
print(f"pages={len(pdf)}")
