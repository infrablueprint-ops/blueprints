"""Generate the fictional sample documents used by the demos.

Every company, person, address, bank account and identifier below is invented. The samples are
rendered with PyMuPDF only (no browser), so `uv run python make_samples.py` rebuilds them anywhere.

Six layouts, like a real accounts-payable inbox: modern SaaS invoice, classic corporate invoice,
law-firm letterhead, utility bill with a consumption chart, hotel folio, thermal till receipt,
plus a hand-filled invoice and a blurred phone photo of a taxi receipt.

    samples/invoices/*.pdf|jpg    16 supplier documents
    samples/invoices/labels.json  ground truth used by `invoice_triage.py --labels`
"""
from __future__ import annotations

import io
import json
import math
import random
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageEnhance, ImageFilter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = Path("samples/invoices")
A4 = (595, 842)
BUYER = ["Acme Ops Ltd", "Accounts Payable", "12 Example Street", "Springfield, EX1 2AB"]
HANDWRITING_FONTS = [Path("C:/Windows/Fonts/Inkfree.ttf"), Path("C:/Windows/Fonts/segoesc.ttf")]


def rgb(hexa: str) -> tuple:
    return tuple(int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5))


def money(value: float, cur: str) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}{cur}{abs(value):,.2f}"


def totals(d: dict) -> tuple[float, float, float]:
    subtotal = sum(q * u for _, q, u in d["lines"])
    tax = round(subtotal * d["tax_rate"], 2)
    return subtotal, tax, subtotal + tax + d.get("extra", 0.0)


# ------------------------------------------------------------------ logos (vector marks)
def logo(page: pymupdf.Page, kind: str, r: pymupdf.Rect, color: tuple) -> None:
    s = page.new_shape()
    cx, cy, w, h = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, r.width, r.height
    if kind == "cloud":
        for dx, dy, rad in ((-0.18, 0.08, 0.22), (0.05, -0.08, 0.28), (0.24, 0.1, 0.2)):
            s.draw_circle((cx + dx * w, cy + dy * h), rad * w)
        s.finish(fill=color, color=None)
    elif kind == "bars":
        for i in range(3):
            y = r.y0 + h * (0.12 + i * 0.3)
            s.draw_rect(pymupdf.Rect(r.x0 + w * (0.1 + 0.12 * i), y, r.x1 - w * 0.1, y + h * 0.18))
        s.finish(fill=color, color=None)
    elif kind == "wing":
        s.draw_polyline([(r.x0, r.y1), (cx, r.y0), (r.x1, r.y1), (cx, r.y1 - h * 0.3), (r.x0, r.y1)])
        s.finish(fill=color, color=None, closePath=True)
    elif kind == "arcs":
        s.draw_circle((r.x0 + w * 0.2, r.y1 - h * 0.2), w * 0.1)
        s.finish(fill=color, color=None)
        for k in (0.45, 0.7, 0.95):
            s.draw_sector((r.x0 + w * 0.2, r.y1 - h * 0.2), (r.x0 + w * (0.2 + k * 0.8), r.y1 - h * 0.2), -90, fullSector=False)
        s.finish(color=color, width=w * 0.07)
    elif kind == "paper":
        s.draw_polyline([(r.x0, r.y0), (r.x1 - w * 0.3, r.y0), (r.x1, r.y0 + h * 0.3), (r.x1, r.y1), (r.x0, r.y1), (r.x0, r.y0)])
        s.finish(fill=color, color=None, closePath=True)
        s.draw_polyline([(r.x1 - w * 0.3, r.y0), (r.x1 - w * 0.3, r.y0 + h * 0.3), (r.x1, r.y0 + h * 0.3)])
        s.finish(color=(1, 1, 1), width=1.5)
    elif kind == "star":
        pts = []
        for i in range(16):
            rad = (w / 2) * (1.0 if i % 2 == 0 else 0.42)
            a = math.pi * i / 8 - math.pi / 2
            pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
        s.draw_polyline(pts + [pts[0]])
        s.finish(fill=color, color=None, closePath=True)
    elif kind == "bolt":
        s.draw_polyline([(cx + w * 0.1, r.y0), (r.x0 + w * 0.15, cy + h * 0.08), (cx, cy + h * 0.08),
                         (cx - w * 0.1, r.y1), (r.x1 - w * 0.15, cy - h * 0.08), (cx, cy - h * 0.08), (cx + w * 0.1, r.y0)])
        s.finish(fill=color, color=None, closePath=True)
    elif kind == "globe":
        s.draw_circle((cx, cy), w / 2)
        s.draw_oval(pymupdf.Rect(cx - w * 0.2, r.y0, cx + w * 0.2, r.y1))
        s.draw_line((r.x0, cy), (r.x1, cy))
        s.finish(color=color, width=1.8)
    elif kind == "anchor":
        s.draw_circle((cx, r.y0 + h * 0.15), w * 0.12)
        s.draw_line((cx, r.y0 + h * 0.27), (cx, r.y1))
        s.draw_line((cx - w * 0.3, r.y0 + h * 0.42), (cx + w * 0.3, r.y0 + h * 0.42))
        s.draw_sector((cx, r.y1 - h * 0.35), (cx - w * 0.42, r.y1 - h * 0.35), -180, fullSector=False)
        s.finish(color=color, width=2.2)
    s.commit()


def stamp(page: pymupdf.Page, text: str, color: tuple, at: tuple) -> None:
    pivot = pymupdf.Point(*at)
    morph = (pivot, pymupdf.Matrix(-14))
    rect = pymupdf.Rect(at[0] - 10, at[1] - 38, at[0] + 22 * len(text) + 18, at[1] + 12)
    shape = page.new_shape()
    shape.draw_rect(rect)
    shape.finish(color=color, width=3, morph=morph)
    shape.insert_text(pymupdf.Point(at[0], at[1]), text, fontsize=34, fontname="hebo", color=color, morph=morph)
    shape.commit()


def lines_table(d: dict, head_bg: str, head_fg: str, border: str) -> str:
    cur = d["currency"]
    rows = "".join(
        f"<tr><td style='border-bottom:1px solid {border}'>{desc}</td>"
        f"<td class='r' style='border-bottom:1px solid {border}'>{qty:g}</td>"
        f"<td class='r' style='border-bottom:1px solid {border}'>{money(unit, cur)}</td>"
        f"<td class='r' style='border-bottom:1px solid {border}'>{money(qty * unit, cur)}</td></tr>"
        for desc, qty, unit in d["lines"])
    sub, tax, tot = totals(d)
    tax_txt = money(tax, cur) if d["tax_rate"] else "not applicable"
    extra = (f"<tr><td colspan='3' class='r'>{d['extra_label']}</td><td class='r'>{money(d['extra'], cur)}</td></tr>"
             if d.get("extra") else "")
    return f"""
<table>
 <tr style="background-color:{head_bg}"><th style="color:{head_fg}">Description</th><th class="r" style="color:{head_fg}">Qty</th>
     <th class="r" style="color:{head_fg}">Unit price</th><th class="r" style="color:{head_fg}">Amount</th></tr>
 {rows}
 <tr><td colspan='3' class='r'>Subtotal</td><td class='r'>{money(sub, cur)}</td></tr>
 <tr><td colspan='3' class='r'>{d['tax_label']}</td><td class='r'>{tax_txt}</td></tr>
 {extra}
 <tr><td colspan='3' class='r'><b>{d['total_label']}</b></td><td class='r'><b>{money(tot, cur)}</b></td></tr>
</table>"""


BASE_CSS = """
body { font-family: sans-serif; font-size: 11px; color: #1f2937; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 5px; font-size: 10px; }
td { padding: 5px; }
.r { text-align: right; }
.muted { color: #6b7280; }
.small { font-size: 8.5px; color: #6b7280; }
"""


def meta_rows(d: dict) -> str:
    return "".join(f"<tr><td class='muted' style='padding:2px'>{k}</td><td class='r' style='padding:2px'><b>{v}</b></td></tr>"
                   for k, v in d["meta"])


def notes_html(d: dict) -> str:
    return "".join(f"<p>{n}</p>" for n in d.get("notes", []))


# ------------------------------------------------------------------ layouts
def layout_saas(page: pymupdf.Page, d: dict) -> None:
    """Modern SaaS / cloud invoice: coloured header band, meta card, footer line."""
    col = rgb(d["color"])
    page.draw_rect(pymupdf.Rect(0, 0, A4[0], 96), color=None, fill=col)
    logo(page, d["logo"], pymupdf.Rect(40, 26, 84, 70), (1, 1, 1))
    page.insert_htmlbox(pymupdf.Rect(96, 28, 360, 90),
                        f"<p style='color:white;font-size:22px'><b>{d['seller'][0]}</b></p>"
                        f"<p style='color:white;font-size:9.5px'>{d['seller'][1]}</p>", css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(360, 34, 555, 80),
                        f"<p class='r' style='color:white;font-size:24px'><b>{d['title']}</b></p>", css=BASE_CSS)
    page.draw_rect(pymupdf.Rect(330, 112, 555, 190), color=None, fill=(0.96, 0.97, 0.98), radius=0.06)
    page.insert_htmlbox(pymupdf.Rect(340, 118, 548, 188), f"<table>{meta_rows(d)}</table>", css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(40, 112, 310, 200),
                        "<p class='muted'>BILL TO</p><p><b>" + "</b><br/>".join(BUYER[:1]) + "</b><br/>"
                        + "<br/>".join(BUYER[1:]) + "</p>", css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(40, 215, 555, 640),
                        lines_table(d, "#eef2ff", "#3730a3", "#e5e7eb") + notes_html(d), css=BASE_CSS)
    page.draw_line((40, 790), (555, 790), color=(0.85, 0.87, 0.9), width=0.8)
    page.insert_htmlbox(pymupdf.Rect(40, 795, 555, 830),
                        f"<p class='small'>{' &#183; '.join(d['seller'][2:])} &#183; Page 1 of 1</p>", css=BASE_CSS)


def layout_classic(page: pymupdf.Page, d: dict) -> None:
    """Classic corporate invoice: logo + name, big grey title, From / Bill to columns, bank footer."""
    col = rgb(d["color"])
    logo(page, d["logo"], pymupdf.Rect(40, 40, 78, 78), col)
    page.insert_htmlbox(pymupdf.Rect(88, 34, 330, 98),
                        f"<p style='font-size:19px;color:{d['color']}'><b>{d['seller'][0]}</b></p>"
                        f"<p class='muted'>{d['seller'][1]}</p>", css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(330, 36, 555, 80),
                        f"<p class='r' style='font-size:28px;color:#9ca3af'><b>{d['title']}</b></p>", css=BASE_CSS)
    page.draw_line((40, 106), (555, 106), color=col, width=2)
    page.insert_htmlbox(pymupdf.Rect(40, 116, 220, 208),
                        "<p class='muted'>FROM</p><p>" + "<br/>".join(d["seller"][2:]) + "</p>", css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(225, 116, 390, 208),
                        "<p class='muted'>BILL TO</p><p>" + "<br/>".join(BUYER) + "</p>", css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(395, 116, 555, 208), f"<table>{meta_rows(d)}</table>", css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(40, 222, 555, 660),
                        lines_table(d, "#1f2937", "#ffffff", "#d1d5db") + notes_html(d), css=BASE_CSS)
    page.draw_rect(pymupdf.Rect(40, 740, 555, 800), color=(0.82, 0.84, 0.87), width=0.8)
    page.insert_htmlbox(pymupdf.Rect(48, 745, 548, 798),
                        f"<p class='small'><b>Bank details</b> &#183; {d['bank']}<br/>"
                        f"{d.get('terms', 'Payment terms: 30 days net. Late payments may incur interest.')}</p>",
                        css=BASE_CSS)


def layout_letterhead(page: pymupdf.Page, d: dict) -> None:
    """Law-firm letterhead: centred serif name, double rule, narrative fee note."""
    css = BASE_CSS + "body { font-family: serif; font-size: 11.5px; }"
    logo(page, d["logo"], pymupdf.Rect(282, 34, 314, 66), rgb(d["color"]))
    page.insert_htmlbox(pymupdf.Rect(40, 70, 555, 120),
                        f"<p style='text-align:center;font-size:22px;color:{d['color']}'>{d['seller'][0].upper()}</p>"
                        f"<p style='text-align:center' class='muted'>{' &#183; '.join(d['seller'][1:])}</p>", css=css)
    for y in (126, 129):
        page.draw_line((90, y), (505, y), color=rgb(d["color"]), width=0.7)
    page.insert_htmlbox(pymupdf.Rect(40, 145, 300, 230), "<p>" + "<br/>".join(BUYER) + "</p>", css=css)
    page.insert_htmlbox(pymupdf.Rect(330, 145, 555, 230), f"<table>{meta_rows(d)}</table>", css=css)
    page.insert_htmlbox(pymupdf.Rect(40, 240, 555, 680),
                        f"<p style='font-size:14px'><b>{d['title']}</b></p><p>{d['narrative']}</p>"
                        + lines_table(d, "#f5f5f4", "#1c1917", "#e7e5e4") + notes_html(d), css=css)
    page.insert_htmlbox(pymupdf.Rect(40, 790, 555, 830),
                        f"<p class='small' style='text-align:center'>{d['footer']}</p>", css=css)


def layout_utility(page: pymupdf.Page, d: dict) -> None:
    """Utility bill: summary box with the amount to pay, 12-month consumption chart, details."""
    col = rgb(d["color"])
    logo(page, d["logo"], pymupdf.Rect(40, 36, 70, 76), col)
    page.insert_htmlbox(pymupdf.Rect(80, 32, 300, 96),
                        f"<p style='font-size:20px'><b>{d['seller'][0]}</b></p><p class='muted'>{d['seller'][1]}</p>",
                        css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(330, 40, 555, 80), f"<p class='r' style='font-size:16px'><b>{d['title']}</b></p>",
                        css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(40, 95, 280, 170), "<p class='muted'>CUSTOMER</p><p>" + "<br/>".join(BUYER) + "</p>",
                        css=BASE_CSS)
    _, _, tot = totals(d)
    page.draw_rect(pymupdf.Rect(300, 92, 555, 226), color=col, width=2, radius=0.08)
    page.insert_htmlbox(pymupdf.Rect(312, 98, 548, 222),
                        f"<p class='muted'>{d['total_label']}</p><p style='font-size:26px'><b>{money(tot, d['currency'])}</b></p>"
                        f"<table>{meta_rows(d)}</table>", css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(40, 240, 555, 262), "<p><b>Your consumption, last 12 months (kWh)</b></p>", css=BASE_CSS)
    base, top = 368, 270
    for i, v in enumerate(d["chart"]):
        x = 52 + i * 41
        h = (base - top) * v / max(d["chart"])
        page.draw_rect(pymupdf.Rect(x, base - h, x + 26, base), color=None, fill=col if i == 11 else (0.82, 0.85, 0.9))
        page.insert_text((x + 2, base + 12), d["months"][i], fontsize=7.5, fontname="helv", color=(0.42, 0.45, 0.5))
    page.insert_htmlbox(pymupdf.Rect(40, 395, 555, 720), lines_table(d, "#fef9c3", "#713f12", "#e5e7eb") + notes_html(d),
                        css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(40, 795, 555, 830),
                        f"<p class='small'>{' &#183; '.join(d['seller'][2:])} &#183; Customer service: Mon-Fri 8:00-18:00</p>",
                        css=BASE_CSS)


def layout_hotel(page: pymupdf.Page, d: dict) -> None:
    """Hotel guest folio: centred name with stars, one row per night, balance zero."""
    col = rgb(d["color"])
    logo(page, d["logo"], pymupdf.Rect(280, 34, 316, 74), col)
    page.insert_htmlbox(pymupdf.Rect(40, 76, 555, 160),
                        f"<p style='text-align:center;font-size:22px;color:{d['color']}'><b>{d['seller'][0]}</b></p>"
                        f"<p style='text-align:center;color:#b45309;font-size:13px'>&#9733; &#9733; &#9733; &#9733;</p>"
                        f"<p style='text-align:center' class='muted'>{' &#183; '.join(d['seller'][1:])}</p>", css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(40, 168, 555, 196), f"<p style='font-size:15px'><b>{d['title']}</b></p>", css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(40, 200, 300, 290), "<p>" + "<br/>".join(BUYER) + "</p>", css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(320, 200, 555, 290), f"<table>{meta_rows(d)}</table>", css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(40, 300, 555, 720), lines_table(d, "#ecfeff", "#155e75", "#e5e7eb") + notes_html(d),
                        css=BASE_CSS)
    page.insert_htmlbox(pymupdf.Rect(40, 800, 555, 830),
                        "<p class='small' style='text-align:center'>Thank you for staying with us. We hope to welcome you again.</p>",
                        css=BASE_CSS)


def render_typed(d: dict, path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=A4[0], height=A4[1])
    LAYOUTS[d["layout"]](page, d)
    if d.get("stamp"):
        stamp(page, *d["stamp"])
    doc.save(path)


def render_thermal(path: Path, lines: list[tuple[str, float, str]], height: int = 470) -> None:
    """Narrow thermal till receipt: (text, font size, font) per line; bold lines are centred."""
    doc = pymupdf.open()
    page = doc.new_page(width=226, height=height)
    y = 30
    for text, size, font in lines:
        x = 16
        if font == "cobo":
            x = (226 - pymupdf.get_text_length(text, fontname=font, fontsize=size)) / 2
        page.insert_text((x, y), text, fontsize=size, fontname=font)
        y += size + 6
    doc.save(path)


def render_handwritten(path: Path) -> None:
    """A hand-filled invoice on a carbon-copy pad from a one-person plumbing business."""
    doc = pymupdf.open()
    page = doc.new_page(width=A4[0], height=A4[1])
    font = next((f for f in HANDWRITING_FONTS if f.exists()), None)
    name = "hand"
    if font:
        page.insert_font(fontname=name, fontfile=str(font))
    else:
        name = "tiro"  # built-in fallback outside Windows
    blue = (0.08, 0.17, 0.55)
    page.draw_rect(pymupdf.Rect(30, 30, 565, 600), color=(0.6, 0.6, 0.6), width=1, fill=(0.99, 0.98, 0.94))
    for y in range(180, 590, 30):
        page.draw_line((45, y + 6), (550, y + 6), color=(0.78, 0.84, 0.92), width=0.6)
    page.insert_text((45, 70), "RAY'S PLUMBING & HEATING", fontsize=18, fontname="hebo")
    page.insert_text((45, 88), "7 Copper Lane, Springfield - ray@plumbing.example", fontsize=9, fontname="helv")
    page.insert_text((400, 70), "INVOICE No. 0412", fontsize=11, fontname="hebo", color=(0.75, 0.1, 0.1))
    lines = [
        (120, "Date: 22 Sept 2026"),
        (150, "To: Acme Ops Ltd - 12 Example Street"),
        (195, "Emergency call-out (Saturday)  ........  95.00"),
        (225, "Replace leaking valve, kitchen  ........  140.00"),
        (255, "Parts: valve + seals  .....................  38.50"),
        (300, "Subtotal  273.50"),
        (330, "VAT 20%  54.70"),
        (365, "TOTAL  328.20"),
        (420, "Payment within 15 days, bank transfer please"),
        (450, "Thank you!  - Ray"),
    ]
    for y, text in lines:
        page.insert_text((60, y), text, fontsize=17 if y != 365 else 21, fontname=name, color=blue)
    page.draw_line((55, 375), (300, 375), color=blue, width=1.5)
    doc.save(path)


def photo_of(pdf_path: Path, jpg_path: Path, seed: int = 7) -> None:
    """Turn a rendered document into a skewed, blurred, unevenly lit phone photo."""
    pix = pymupdf.open(pdf_path)[0].get_pixmap(dpi=200)
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    img = img.rotate(4.5, resample=Image.BICUBIC, expand=True, fillcolor=(96, 88, 80))
    img = img.filter(ImageFilter.GaussianBlur(1.1))
    img = ImageEnhance.Brightness(img).enhance(0.86)
    rng = random.Random(seed)
    px = img.load()
    w, h = img.size
    for y in range(h):
        shade = int(28 * y / h)
        for x in range(0, w):
            r, g, b = px[x, y]
            n = rng.randint(-9, 9)
            px[x, y] = (max(0, r - shade + n), max(0, g - shade + n), max(0, b - shade - 6 + n))
    img.save(jpg_path, quality=55)


LAYOUTS = {"saas": layout_saas, "classic": layout_classic, "letterhead": layout_letterhead,
           "utility": layout_utility, "hotel": layout_hotel}

KESTREL = ["Kestrel Computers", "Business IT equipment", "88 Forge Road, Lyon", "sales@kestrel.example",
           "VAT ID: FR 00 000000000 (sample)"]
KESTREL_BANK = "Example Bank &#183; IBAN FR00 0000 0000 0000 0000 0000 000 (sample) &#183; BIC SAMPLEXX"
NIMBUS = ["Nimbus Docs", "Collaborative docs for teams", "4 Cloud Avenue, Dublin", "billing@nimbus.example",
          "VAT ID: IE 0000000XX (sample)"]
STRATUS = ["Stratus Cloud", "Infrastructure as a service", "500 Harbor Blvd, Seattle", "invoices@stratus.example",
           "Tax ID: 00-0000000 (sample)"]

DOCS: list[dict] = [
    dict(file="01_nimbus_saas_invoice", layout="saas", logo="cloud", color="#4f46e5", currency="€", title="INVOICE",
         seller=NIMBUS, meta=[("Invoice no.", "ND-2026-11873"), ("Date", "01 Sep 2026"), ("Paid", "01 Sep 2026")],
         lines=[("Team plan - annual subscription (12 seats)", 12, 180.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Total paid",
         notes=["Paid by card ending 4242. Thank you for your business."],
         stamp=("PAID", (0.09, 0.6, 0.3), (390, 520)),
         label=dict(doc_type="invoice", category="software_saas", payment_status="paid", vat_shown=True,
                    amount_band="1000_to_10000")),
    dict(file="02_stratus_cloud_invoice", layout="saas", logo="bars", color="#0284c7", currency="$", title="INVOICE",
         seller=STRATUS, meta=[("Invoice no.", "SC-2026-0917"), ("Billing period", "Sep 2026"), ("Due date", "31 Oct 2026")],
         lines=[("Compute instances (vCPU-hours)", 1240, 0.42), ("Block storage (GB-month)", 800, 0.08),
                ("Data transfer out (GB)", 912, 0.09)],
         tax_rate=0.0, tax_label="Sales tax", total_label="Amount due",
         notes=["Payment is due by 31 Oct 2026. Pay online at the billing console."],
         label=dict(doc_type="invoice", category="cloud_hosting", payment_status="due", vat_shown=False,
                    amount_band="100_to_1000")),
    dict(file="03_kestrel_hardware_invoice", layout="classic", logo="wing", color="#b45309", currency="€", title="INVOICE",
         seller=KESTREL, bank=KESTREL_BANK,
         meta=[("Invoice no.", "KC-55102"), ("Date", "12 Sep 2026"), ("Paid", "15 Sep 2026")],
         lines=[("Laptop 14\" Pro, 32 GB RAM", 2, 1890.00), ("27\" 4K monitor", 2, 420.00),
                ("USB-C docking station", 2, 380.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Total",
         notes=["Settled by bank transfer on 15 Sep 2026. Warranty: 3 years on-site."],
         stamp=("PAID", (0.09, 0.6, 0.3), (390, 560)),
         label=dict(doc_type="invoice", category="hardware", payment_status="paid", vat_shown=True,
                    amount_band="1000_to_10000")),
    dict(file="04_harbor_inn_receipt", layout="hotel", logo="anchor", color="#0f766e", currency="£", title="GUEST FOLIO - RECEIPT",
         seller=["Harbor Inn", "3 Quay Street, Bristol", "frontdesk@harborinn.example"],
         meta=[("Folio", "HI-88412"), ("Arrival", "22 Sep 2026"), ("Departure", "25 Sep 2026"), ("Guest", "J. Doe (Acme Ops)")],
         lines=[("22 Sep - Standard room", 1, 135.00), ("23 Sep - Standard room", 1, 135.00),
                ("24 Sep - Standard room", 1, 135.00), ("Breakfast", 3, 12.00)],
         tax_rate=0.10, tax_label="VAT 10%", total_label="Total charged",
         notes=["Balance: 0.00 - paid by card at check-out. Trip: DevOps conference."],
         label=dict(doc_type="receipt", category="travel", payment_status="paid", vat_shown=True,
                    amount_band="100_to_1000")),
    dict(file="06_volt_energy_bill", layout="utility", logo="bolt", color="#ca8a04", currency="€", title="ELECTRICITY BILL",
         seller=["Volt Grid Energy", "Business electricity", "1 Power Plaza, Rotterdam", "service@voltgrid.example"],
         meta=[("Account", "VG-778120"), ("Period", "Sep 2026"), ("Direct debit on", "15 Oct 2026")],
         lines=[("Consumption, office (kWh)", 4120, 0.24), ("Standing charge (days)", 30, 1.10)],
         tax_rate=0.21, tax_label="VAT 21%", total_label="Amount to be debited",
         chart=[3980, 4210, 4400, 4105, 3890, 3720, 3650, 3580, 3700, 3910, 4060, 4120],
         months=["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"],
         notes=["The amount will be collected by direct debit on 15 Oct 2026."],
         label=dict(doc_type="invoice", category="utilities", payment_status="due", vat_shown=True,
                    amount_band="1000_to_10000")),
    dict(file="07_fiberlink_telecom_invoice", layout="saas", logo="arcs", color="#7c3aed", currency="€", title="INVOICE",
         seller=["FiberLink Business", "Internet & mobile for companies", "9 Signal Street, Madrid", "billing@fiberlink.example"],
         meta=[("Invoice no.", "FL-2026-30551"), ("Date", "28 Sep 2026"), ("Due date", "10 Oct 2026")],
         lines=[("Fibre 1 Gbps, static IP", 1, 89.00), ("Mobile line, 50 GB", 5, 24.00), ("Router rental", 1, 6.00)],
         tax_rate=0.21, tax_label="VAT 21%", total_label="Amount due",
         label=dict(doc_type="invoice", category="telecom", payment_status="due", vat_shown=True,
                    amount_band="100_to_1000")),
    dict(file="08_paperline_supplies_invoice", layout="classic", logo="paper", color="#15803d", currency="€", title="INVOICE",
         seller=["Paperline Supplies", "Office stationery", "40 Mill Lane, Lille", "orders@paperline.example"],
         bank="Example Bank &#183; IBAN FR00 1111 2222 3333 4444 5555 666 (sample)",
         meta=[("Invoice no.", "PL-9902"), ("Date", "05 Sep 2026"), ("Paid", "05 Sep 2026")],
         lines=[("A4 printer paper, box of 5 reams", 2, 21.50), ("Toner cartridge, black", 1, 24.90),
                ("Notebooks, pack of 10", 1, 12.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Total paid",
         stamp=("PAID", (0.09, 0.6, 0.3), (390, 520)),
         label=dict(doc_type="invoice", category="office_supplies", payment_status="paid", vat_shown=True,
                    amount_band="under_100")),
    dict(file="09_atlas_legal_invoice", layout="letterhead", logo="globe", color="#1e3a8a", currency="£", title="Fee note - Invoice",
         seller=["Atlas Legal LLP", "Commercial law", "2 Temple Row, Birmingham", "accounts@atlaslegal.example"],
         meta=[("Invoice no.", "AL-24-0611"), ("Date", "26 Sep 2026"), ("Due date", "26 Oct 2026"), ("Matter", "ACME/0042")],
         narrative="For professional services rendered in September 2026: review of your SaaS master agreement, "
                   "redline of the liability and data-protection clauses, and one call with your supplier.",
         lines=[("Review of SaaS master agreement (hours)", 6.5, 280.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Amount due",
         notes=["Payment terms: 30 days. Please quote the invoice number with your payment."],
         footer="Atlas Legal LLP (sample firm) &#183; Registered in England No. 00000000 &#183; Regulated by the Example Law Society",
         label=dict(doc_type="invoice", category="professional_services", payment_status="due", vat_shown=True,
                    amount_band="1000_to_10000")),
    dict(file="10_kestrel_quote", layout="classic", logo="wing", color="#b45309", currency="€", title="QUOTATION",
         seller=KESTREL, bank=KESTREL_BANK,
         terms="This is a quotation, not an invoice. Prices valid 30 days.",
         meta=[("Quote no.", "Q-7781"), ("Date", "29 Sep 2026"), ("Valid until", "29 Oct 2026")],
         lines=[("Laptop 14\" Pro, 32 GB RAM", 10, 1490.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Quoted total",
         notes=["This is a quotation, not an invoice. Sign and return to confirm the order."],
         label=dict(doc_type="quote", category="hardware", payment_status="no_payment_info", vat_shown=True,
                    amount_band="over_10000")),
    dict(file="11_nimbus_credit_note", layout="saas", logo="cloud", color="#4f46e5", currency="€", title="CREDIT NOTE",
         seller=NIMBUS, meta=[("Credit note no.", "CN-2026-0042"), ("Date", "20 Sep 2026"), ("Refers to", "ND-2026-11873")],
         lines=[("Seats removed from Team plan", 2, -180.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Total credited",
         notes=["This amount has been refunded to the card ending 4242."],
         label=dict(doc_type="credit_note", category="software_saas", payment_status=None, vat_shown=True,
                    amount_band=None)),
    dict(file="12_stratus_overdue_reminder", layout="saas", logo="bars", color="#dc2626", currency="$", title="PAYMENT REMINDER",
         seller=STRATUS, meta=[("Original invoice", "SC-2026-0817"), ("Due date", "31 Aug 2026"), ("Days overdue", "31")],
         lines=[("Unpaid balance, invoice SC-2026-0817", 1, 1190.40)],
         tax_rate=0.0, tax_label="Sales tax", extra=25.00, extra_label="Late payment fee",
         total_label="Now due immediately",
         notes=["Your account is OVERDUE. Services may be suspended if payment is not received within 7 days."],
         stamp=("OVERDUE", (0.85, 0.1, 0.1), (330, 560)),
         label=dict(doc_type="payment_reminder", category="cloud_hosting", payment_status="overdue", vat_shown=False,
                    amount_band="1000_to_10000")),
    dict(file="14_kestrel_repair_invoice", layout="classic", logo="wing", color="#b45309", currency="€", title="INVOICE",
         seller=KESTREL, bank=KESTREL_BANK,
         meta=[("Invoice no.", "KC-55188"), ("Date", "24 Sep 2026"), ("Due date", "24 Oct 2026")],
         lines=[("On-site repair: replace cracked laptop screen", 1, 210.00), ("Labour (hours)", 1.5, 60.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Amount due",
         label=dict(doc_type="invoice", category="repairs_maintenance", payment_status="due", vat_shown=True,
                    amount_band="100_to_1000")),
    dict(file="15_northlight_print_invoice", layout="classic", logo="star", color="#be185d", currency="€", title="INVOICE",
         seller=["Northlight Print", "Digital & offset printing", "5 Harbour Road, Hamburg", "hello@northlight.example"],
         bank="Example Bank &#183; IBAN DE00 0000 0000 0000 0000 00 (sample)",
         meta=[("Invoice no.", "NP-26-4410"), ("Date", "16 Sep 2026"), ("Paid", "16 Sep 2026")],
         lines=[("A5 flyers, 2,000 copies (trade fair)", 1, 340.00), ("Roll-up banner 85x200 cm", 2, 95.00)],
         tax_rate=0.19, tax_label="VAT 19%", total_label="Total (paid)",
         notes=["Thank you for your order!"],
         label=dict(doc_type="invoice", category="marketing", payment_status="paid", vat_shown=True,
                    amount_band="100_to_1000")),
]

COPPER_POT = [
    ("THE COPPER POT", 14, "cobo"), ("Restaurant & bar", 8, "cour"), ("21 Market Square, Ghent", 8, "cour"),
    ("", 6, "cour"), ("Table 12      Covers 4", 9, "cour"), ("18 Sep 2026        13:42", 9, "cour"),
    ("------------------------------", 9, "cour"),
    ("4 x Lunch menu      112.00", 9, "cour"), ("2 x Sparkling water   9.00", 9, "cour"), ("4 x Coffee           14.00", 9, "cour"),
    ("------------------------------", 9, "cour"),
    ("SUBTOTAL            135.00", 9, "cour"), ("VAT 10%              13.50", 9, "cour"),
    ("TOTAL EUR       148.50", 12, "cobo"), ("", 6, "cour"),
    ("CARD PAYMENT     APPROVED", 9, "cobo"), ("**** **** **** 4242", 9, "cour"), ("", 6, "cour"),
    ("Thank you, see you soon!", 8, "cour"),
]
COPPER_POT_LABEL = dict(doc_type="receipt", category="meals", payment_status="paid", vat_shown=True,
                        amount_band="100_to_1000")

TAXI = [
    ("CITY CAB 24", 14, "cobo"), ("Licensed taxi no. 4471", 8, "cour"), ("", 6, "cour"),
    ("RECEIPT", 12, "cobo"), ("24 Sep 2026   23:10", 9, "cour"), ("From: Airport T2", 9, "cour"),
    ("To:   Harbor Inn", 9, "cour"), ("------------------------", 9, "cour"),
    ("Fare            EUR 41.50", 9, "cour"), ("Luggage x2      EUR  4.00", 9, "cour"),
    ("------------------------", 9, "cour"), ("TOTAL           EUR 45.50", 10, "cobo"),
    ("incl. VAT 10%   EUR  4.14", 9, "cour"), ("", 6, "cour"), ("PAID BY CARD  **** 4242", 9, "cobo"),
    ("Thank you - safe travels", 8, "cour"),
]
TAXI_LABEL = dict(doc_type="receipt", category="travel", payment_status="paid", vat_shown=True, amount_band="under_100")
HANDWRITTEN_LABEL = dict(doc_type="invoice", category="repairs_maintenance", payment_status="due", vat_shown=True,
                         amount_band="100_to_1000")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    labels: dict[str, dict] = {}
    for d in DOCS:
        path = OUT / f"{d['file']}.pdf"
        render_typed(d, path)
        labels[path.name] = d["label"]
        print(f"wrote {path}")

    pot = OUT / "05_copper_pot_receipt.pdf"
    render_thermal(pot, COPPER_POT, height=420)
    labels[pot.name] = COPPER_POT_LABEL
    print(f"wrote {pot} (thermal till receipt)")

    taxi_pdf = OUT / "_taxi_source.pdf"
    render_thermal(taxi_pdf, TAXI, height=360)
    taxi_jpg = OUT / "13_taxi_receipt.jpg"
    photo_of(taxi_pdf, taxi_jpg)
    taxi_pdf.unlink()
    labels[taxi_jpg.name] = TAXI_LABEL
    print(f"wrote {taxi_jpg} (degraded phone photo)")

    hand = OUT / "16_rays_plumbing_handwritten.pdf"
    render_handwritten(hand)
    labels[hand.name] = HANDWRITTEN_LABEL
    print(f"wrote {hand}")

    (OUT / "labels.json").write_text(json.dumps(dict(sorted(labels.items())), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT / 'labels.json'} ({len(labels)} documents)")


if __name__ == "__main__":
    main()
