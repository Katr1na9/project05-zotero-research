from pathlib import Path
import math

import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).parent


for pdf_path in sorted(ROOT.glob("reference-*.pdf")):
    out = ROOT / f"{pdf_path.stem}-pages"
    out.mkdir(exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_path))
    thumbs = []
    for index in range(len(pdf)):
        page = pdf[index].render(scale=1.45).to_pil().convert("RGB")
        page.save(out / f"page-{index + 1:02d}.png")
        thumb = page.copy()
        thumb.thumbnail((250, 350))
        tile = Image.new("RGB", (270, 390), "white")
        tile.paste(thumb, ((270 - thumb.width) // 2, 28))
        ImageDraw.Draw(tile).text((10, 8), f"Page {index + 1}", fill="black")
        thumbs.append(ImageOps.expand(tile, border=1, fill="#777777"))
    cols = 5
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 272, rows * 392), "#dddddd")
    for i, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((i % cols) * 272, (i // cols) * 392))
    sheet.save(ROOT / f"{pdf_path.stem}-contact-sheet.png")
    print(pdf_path.name, len(pdf))
