from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(r"C:\Users\hp\OneDrive\Desktop\Starline Technologies\Business Card")
OUT.mkdir(parents=True, exist_ok=True)

PDF_PATH = OUT / "starline-technologies-business-card-print.pdf"
LOCKUP_DARK = ROOT / "assets" / "images" / "starline-lockup-dark.png"
MARK_LIGHT = ROOT / "assets" / "images" / "starline-mark-light.png"

INK = HexColor("#1D1D1B")
GRAPHITE = HexColor("#2D2D2A")
SILVER = HexColor("#D5D4D1")
PAPER = HexColor("#F4F3F1")
RED = HexColor("#E32219")

BLEED = 0.125 * inch
TRIM_W = 3.5 * inch
TRIM_H = 2.0 * inch
PAGE_W = TRIM_W + 2 * BLEED
PAGE_H = TRIM_H + 2 * BLEED
SAFE = BLEED + 0.19 * inch


def register_fonts() -> None:
    fonts = ROOT / "assets" / "fonts"
    pdfmetrics.registerFont(TTFont("LeagueSpartan", str(fonts / "LeagueSpartan-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("LibreBaskerville", str(fonts / "LibreBaskerville-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("LibreBaskervilleItalic", str(fonts / "LibreBaskerville-Italic.ttf")))


def tracked_text(c, text, x, y, font, size, color, tracking=1.0):
    c.setFont(font, size)
    c.setFillColor(color)
    cursor = x
    for char in text:
        c.drawString(cursor, y, char)
        cursor += pdfmetrics.stringWidth(char, font, size) + tracking
    return cursor


def draw_front(c) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(RED)
    c.rect(0, 0, 5, PAGE_H, fill=1, stroke=0)

    logo_w = 190
    logo_h = 112
    c.drawImage(
        ImageReader(str(LOCKUP_DARK)),
        (PAGE_W - logo_w) / 2,
        (PAGE_H - logo_h) / 2 + 6,
        width=logo_w,
        height=logo_h,
        preserveAspectRatio=True,
        anchor="c",
        mask="auto",
    )
    tracked_text(c, "PVT LTD  /  ESTD 2024", SAFE, SAFE - 2, "LeagueSpartan", 5.2, INK, 0.65)
    tracked_text(c, "INDIA", PAGE_W - SAFE - 26, SAFE - 2, "LeagueSpartan", 5.2, RED, 0.75)


def draw_back(c) -> None:
    c.setFillColor(INK)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Oversized textured semicircle anchors the reverse without competing with contact details.
    c.saveState()
    c.setFillAlpha(0.12)
    c.drawImage(
        ImageReader(str(MARK_LIGHT)),
        PAGE_W - 112,
        PAGE_H - 79,
        width=124,
        height=78,
        preserveAspectRatio=True,
        mask="auto",
    )
    c.restoreState()

    c.setFillColor(RED)
    c.rect(SAFE, PAGE_H - SAFE - 3, 24, 3, fill=1, stroke=0)
    tracked_text(c, "STARLINE TECHNOLOGIES", SAFE + 31, PAGE_H - SAFE - 5, "LeagueSpartan", 6.1, SILVER, 0.85)

    c.setFillColor(PAPER)
    c.setFont("LibreBaskerville", 14.2)
    c.drawString(SAFE, PAGE_H - SAFE - 37, "AI does the work.")
    c.setFillColor(RED)
    c.setFont("LibreBaskervilleItalic", 13.4)
    c.drawString(SAFE, PAGE_H - SAFE - 56, "You take the credit.")

    c.setStrokeColor(GRAPHITE)
    c.setLineWidth(0.65)
    c.line(SAFE, SAFE + 29, PAGE_W - SAFE, SAFE + 29)

    tracked_text(c, "CALL / WHATSAPP", SAFE, SAFE + 16, "LeagueSpartan", 5.1, RED, 0.65)
    c.setFillColor(PAPER)
    c.setFont("LibreBaskerville", 7.7)
    c.drawString(SAFE, SAFE + 3, "+91 9559553271")

    tracked_text(c, "CUSTOM AI SYSTEMS", PAGE_W - SAFE - 78, SAFE + 16, "LeagueSpartan", 5.1, SILVER, 0.65)
    tracked_text(c, "AUTOMATION  /  DIGITAL PRODUCTS", PAGE_W - SAFE - 117, SAFE + 3, "LeagueSpartan", 4.6, SILVER, 0.45)


def main() -> None:
    register_fonts()
    c = canvas.Canvas(str(PDF_PATH), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle("Starline Technologies Business Card")
    c.setAuthor("Starline Technologies Pvt Ltd")
    c.setSubject("Two-sided business card with 0.125 inch bleed")
    draw_front(c)
    c.showPage()
    draw_back(c)
    c.showPage()
    c.save()
    print(PDF_PATH)


if __name__ == "__main__":
    main()
