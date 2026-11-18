#!/usr/bin/env python3
"""Regenerate RackMath's original, static barbell guide assets.

Optional authoring command; this is not a production build dependency:
    uv run --with reportlab==4.4.3 python tools/generate_barbell_guide_assets.py

SVGs use no external resources. The one-page US Letter PDF uses built-in fonts,
fixed ReportLab metadata, and no current timestamps for reproducible output.
"""

from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "guides"
CALCULATOR_URL = "https://rackmath.com/tools/barbell-calculator"
INK = "#101418"
MUTED = "#5d6673"
BLUE = "#0676b5"
BRIGHT_BLUE = "#28b9ff"
LINE = "#dfe4ea"

LB_ROWS = (
    (45, ()), (65, (10,)), (95, (25,)), (115, (35,)),
    (135, (45,)), (155, (45, 10)), (185, (45, 25)), (205, (45, 35)),
    (225, (45, 45)), (275, (45, 45, 25)),
    (315, (45, 45, 45)), (405, (45, 45, 45, 45)),
)
KG_ROWS = (
    (20, ()), (30, (5,)), (40, (10,)), (50, (15,)),
    (60, (20,)), (80, (20, 10)), (100, (20, 20)), (120, (20, 20, 10)),
    (140, (20, 20, 20)), (160, (20, 20, 20, 10)),
    (180, (20, 20, 20, 20)), (200, (20, 20, 20, 20, 10)),
)


def validate_reference_rows() -> None:
    for bar, rows in ((45, LB_ROWS), (20, KG_ROWS)):
        assert len(rows) == 12
        assert len({total for total, _ in rows}) == 12
        for total, plates in rows:
            assert bar + 2 * sum(plates) == total, (bar, total, plates)
            assert all(plate > 0 for plate in plates)


def loading_diagram(total: int, bar: int, plates: tuple[int, int], unit: str) -> str:
    """Show a complete, symmetric bar; larger plates sit nearest the center."""
    per_side = sum(plates)
    assert bar + 2 * per_side == total
    inner, outer = plates
    plate_text = f"{inner} + {outer} {unit}"
    title = f"{total} {unit} barbell loading diagram"
    description = (
        f"A {bar} {unit} bar with a {inner} {unit} plate and a {outer} {unit} plate "
        f"on each side. Each side holds {per_side} {unit} in plates, giving "
        f"{total} {unit} total. The bar is included; collars are not included."
    )
    plate_shapes = []
    for x, value, height in (
        (154, outer, 104 if outer < inner else 144),
        (220, inner, 144),
        (440, inner, 144),
        (506, outer, 104 if outer < inner else 144),
    ):
        y = 224 - height / 2
        plate_shapes.append(
            f'<rect x="{x}" y="{y:g}" width="60" height="{height}" rx="10" '
            f'fill="white" stroke="{INK}" stroke-width="3"/>'
            f'<rect x="{x + 4}" y="{y + 10:g}" width="5" height="{height - 20}" '
            f'rx="2.5" fill="{BRIGHT_BLUE}"/>'
            f'<text x="{x + 31}" y="224" class="plate">{value}</text>'
            f'<text x="{x + 31}" y="249" class="unit">{unit}</text>'
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 440" role="img" aria-labelledby="title desc">
  <title id="title">{escape(title)}</title>
  <desc id="desc">{escape(description)}</desc>
  <style>
    text {{ font-family: Arial, Helvetica, sans-serif; fill: {INK}; }}
    .plate {{ font-size: 30px; font-weight: 700; text-anchor: middle; }}
    .unit {{ font-size: 22px; text-anchor: middle; }}
    .label {{ font-size: 24px; font-weight: 700; text-anchor: middle; }}
    .detail {{ font-size: 24px; text-anchor: middle; }}
  </style>
  <rect x="1.5" y="1.5" width="717" height="437" rx="20" fill="white" stroke="{LINE}" stroke-width="3"/>
  <text x="32" y="43" font-size="22" font-weight="700" fill="{BLUE}" style="fill:{BLUE}">RackMath</text>
  <text x="32" y="89" font-size="38" font-weight="700">{total} {unit} total</text>
  <text x="688" y="86" font-size="24" text-anchor="end">Bar included</text>
  <path d="M32 111H688" stroke="{LINE}" stroke-width="2"/>
  <text x="360" y="155" class="label">{bar} {unit} bar</text>
  <path d="M360 166V205" stroke="{MUTED}" stroke-width="2"/>
  <rect x="70" y="215" width="580" height="18" rx="5" fill="#edf2f6" stroke="{INK}" stroke-width="3"/>
  <path d="M286 219V229M295 219V229M304 219V229M313 219V229M322 219V229M331 219V229M389 219V229M398 219V229M407 219V229M416 219V229M425 219V229M434 219V229" stroke="#a5afb9" stroke-width="2"/>
  {''.join(plate_shapes)}
  <text x="216" y="333" class="label">{per_side} {unit} per side</text>
  <text x="504" y="333" class="label">{per_side} {unit} per side</text>
  <text x="216" y="362" class="detail">{plate_text}</text>
  <text x="504" y="362" class="detail">{plate_text}</text>
  <path d="M32 382H688" stroke="{LINE}" stroke-width="2"/>
  <text x="360" y="416" class="detail">{bar} + ({per_side} × 2) = {total} {unit}</text>
</svg>
'''


def create_pdf(path: Path) -> None:
    try:
        from reportlab.lib.colors import HexColor
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen.canvas import Canvas
    except ImportError as error:
        raise SystemExit(
            "PDF generation needs ReportLab. Run: "
            "uv run --with reportlab==4.4.3 python tools/generate_barbell_guide_assets.py"
        ) from error

    canvas = Canvas(str(path), pagesize=letter, invariant=1, pageCompression=1)
    canvas.setTitle("RackMath Barbell Plate Reference - Pounds and Kilograms")
    canvas.setAuthor("RackMath")
    canvas.setSubject("Plates per side for a 45 lb bar and a 20 kg bar")
    canvas.setCreator("RackMath deterministic guide asset generator")

    def text(x: float, y: float, value: str, size: float = 10, bold: bool = False, color: str = INK) -> None:
        canvas.setFillColor(HexColor(color))
        canvas.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        canvas.drawString(x, y, value)

    def line(x1: float, y: float, x2: float, color: str = LINE, width: float = 0.6) -> None:
        canvas.setStrokeColor(HexColor(color))
        canvas.setLineWidth(width)
        canvas.line(x1, y, x2, y)

    text(42, 750, "RackMath", 18, True, BLUE)
    text(423, 752, "GYM REFERENCE  /  LB + KG", 9, True, MUTED)
    text(42, 714, "Barbell plate reference", 26, True)
    text(42, 693, "Plates listed for one side. Load the same plates on both sides.", 11)
    line(42, 676, 570)
    text(42, 655, "Plate weight per side = (target total - bar weight) / 2", 12, True)
    text(42, 637, "Example: 225 lb total - 45 lb bar = 180 lb of plates, or 90 lb per side.", 10, color=MUTED)

    def table(x: float, heading: str, bar: int, unit: str, rows: tuple) -> None:
        width = 252
        text(x, 605, heading, 14, True, BLUE)
        text(x, 588, f"{bar} {unit} bar  |  All values below are in {unit}", 9.5, color=MUTED)
        line(x, 574, x + width, INK, 0.8)
        text(x + 8, 558, "Total", 10, True)
        text(x + 76, 558, "Plates on EACH SIDE", 10, True)
        line(x, 549, x + width, INK, 0.6)
        for index, (total, plates) in enumerate(rows):
            y = 532 - index * 23
            text(x + 8, y, str(total), 11, True)
            plate_label = " + ".join(map(str, plates)) if plates else "None (empty bar)"
            text(x + 76, y, plate_label, 10.5)
            line(x, y - 8, x + width)

    table(42, "POUNDS", 45, "lb", LB_ROWS)
    table(318, "KILOGRAMS", 20, "kg", KG_ROWS)

    text(42, 242, "Before you load", 12, True)
    for y, sentence in (
        (222, "Totals include the stated bar. Use the known weight of your own bar."),
        (205, "Mirror every plate on both sides. Collar weight is not included."),
        (188, "Assumes enough of each listed plate. Other combinations may also work."),
    ):
        text(42, y, sentence, 10)

    line(42, 166, 570)
    text(42, 141, "Need a different weight?", 14, True)
    text(42, 121, "rackmath.com/tools/barbell-calculator", 12, True, BLUE)
    canvas.linkURL(CALCULATOR_URL, (42, 118, 332, 133), relative=0, thickness=0)
    text(42, 100, "Free calculator  |  Pounds and kilograms  |  Custom bar weight", 10, color=MUTED)
    text(42, 51, "Keep this reference by your rack.", 9, color=MUTED)
    text(530, 51, "1 / 1", 9, color=MUTED)
    canvas.showPage()
    canvas.save()


def main() -> None:
    validate_reference_rows()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "barbell-185lb.svg").write_text(loading_diagram(185, 45, (45, 25), "lb"), encoding="utf-8")
    (OUTPUT / "barbell-100kg.svg").write_text(loading_diagram(100, 20, (20, 20), "kg"), encoding="utf-8")
    create_pdf(OUTPUT / "barbell-plate-reference.pdf")
    print("Generated 2 accessible SVG diagrams and 1 US Letter PDF; all 24 reference rows verified.")


if __name__ == "__main__":
    main()
