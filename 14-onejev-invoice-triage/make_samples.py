"""Generate the fictional sample documents used by the demos.

Every company, person, address and identifier below is invented. The samples are rendered
with PyMuPDF only (no browser), so `uv run python make_samples.py` rebuilds them anywhere.

    samples/invoices/*.pdf        15 supplier documents (invoices, receipts, a quote, a credit note...)
    samples/invoices/*.jpg        a degraded phone photo of a taxi receipt
    samples/invoices/labels.json  ground truth used by `invoice_triage.py --labels`
"""
from __future__ import annotations

import io
import json
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

CSS = """
* { font-family: sans-serif; font-size: 10px; color: #1f2937; }
h1 { font-size: 22px; margin: 0; }
.muted { color: #6b7280; }
table { width: 100%; border-collapse: collapse; }
th { background-color: #f3f4f6; text-align: left; padding: 4px; }
td { padding: 4px; border-bottom: 1px solid #e5e7eb; }
.r { text-align: right; }
.total td { font-weight: bold; border-bottom: none; }
"""


def money(value: float, cur: str) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}{cur}{abs(value):,.2f}"


def build_html(d: dict) -> tuple[str, str, str]:
    """Seller block, title block and body of a typed document."""
    cur = d["currency"]
    rows = "".join(
        f"<tr><td>{desc}</td><td class='r'>{qty:g}</td><td class='r'>{money(unit, cur)}</td>"
        f"<td class='r'>{money(qty * unit, cur)}</td></tr>"
        for desc, qty, unit in d["lines"]
    )
    subtotal = sum(q * u for _, q, u in d["lines"])
    tax = round(subtotal * d["tax_rate"], 2)
    total = subtotal + tax + d.get("extra", 0.0)
    tax_row = (f"<tr class='total'><td colspan='3' class='r'>{d['tax_label']}</td><td class='r'>{money(tax, cur)}</td></tr>"
               if d["tax_rate"] else
               f"<tr class='total'><td colspan='3' class='r'>{d['tax_label']}</td><td class='r'>not applicable</td></tr>")
    extra_row = (f"<tr class='total'><td colspan='3' class='r'>{d['extra_label']}</td><td class='r'>{money(d['extra'], cur)}</td></tr>"
                 if d.get("extra") else "")
    meta = "".join(f"<tr><td class='muted'>{k}</td><td class='r'>{v}</td></tr>" for k, v in d["meta"])
    seller = "<br/>".join(d["seller"][1:])
    buyer = "<br/>".join(BUYER)
    notes = "".join(f"<p>{n}</p>" for n in d.get("notes", []))
    left = f"<h1 style=\"color:{d['color']}\">{d['seller'][0]}</h1><p class=\"muted\">{seller}</p>"
    right = f"<h1 class=\"r\">{d['title']}</h1><table>{meta}</table>"
    body = f"""
<p><b>Bill to</b><br/>{buyer}</p>
<table>
  <tr><th>Description</th><th class="r">Qty</th><th class="r">Unit price</th><th class="r">Amount</th></tr>
  {rows}
  <tr class='total'><td colspan='3' class='r'>Subtotal</td><td class='r'>{money(subtotal, cur)}</td></tr>
  {tax_row}
  {extra_row}
  <tr class='total'><td colspan='3' class='r' style="font-size:13px">{d['total_label']}</td>
      <td class='r' style="font-size:13px">{money(total, cur)}</td></tr>
</table>
{notes}
"""
    return left, right, body


def stamp(page: pymupdf.Page, text: str, color: tuple, at: tuple = (390, 520)) -> None:
    pivot = pymupdf.Point(*at)
    morph = (pivot, pymupdf.Matrix(-14))
    rect = pymupdf.Rect(at[0] - 10, at[1] - 38, at[0] + 22 * len(text) + 18, at[1] + 12)
    shape = page.new_shape()
    shape.draw_rect(rect)
    shape.finish(color=color, width=3, morph=morph)
    shape.insert_text(pymupdf.Point(at[0], at[1]), text, fontsize=34, fontname="hebo", color=color, morph=morph)
    shape.commit()


def render_typed(d: dict, path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page(width=A4[0], height=A4[1])
    left, right, body = build_html(d)
    page.insert_htmlbox(pymupdf.Rect(40, 40, 330, 175), left, css=CSS)
    page.insert_htmlbox(pymupdf.Rect(345, 40, A4[0] - 40, 175), right, css=CSS)
    page.insert_htmlbox(pymupdf.Rect(40, 180, A4[0] - 40, A4[1] - 40), body, css=CSS)
    if d.get("stamp"):
        stamp(page, *d["stamp"])
    doc.save(path)


def render_handwritten(path: Path) -> None:
    """A hand-filled invoice from a one-person plumbing business."""
    doc = pymupdf.open()
    page = doc.new_page(width=A4[0], height=A4[1])
    font = next((f for f in HANDWRITING_FONTS if f.exists()), None)
    name = "hand"
    if font:
        page.insert_font(fontname=name, fontfile=str(font))
    else:
        name = "tiro"  # built-in fallback outside Windows
    blue = (0.08, 0.17, 0.55)
    page.draw_rect(pymupdf.Rect(30, 30, 565, 600), color=(0.6, 0.6, 0.6), width=1)
    page.insert_text((45, 70), "RAY'S PLUMBING & HEATING", fontsize=18, fontname="hebo")
    page.insert_text((45, 88), "7 Copper Lane, Springfield - ray@plumbing.example", fontsize=9, fontname="helv")
    page.insert_text((400, 70), "INVOICE No. 0412", fontsize=11, fontname="hebo")
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


def render_thermal(path: Path) -> None:
    """A narrow thermal-printer taxi receipt."""
    doc = pymupdf.open()
    page = doc.new_page(width=230, height=360)
    lines = [
        ("CITY CAB 24", 14, "cobo"), ("Licensed taxi no. 4471", 8, "cour"), ("", 8, "cour"),
        ("RECEIPT", 12, "cobo"), ("24 Sep 2026   23:10", 9, "cour"), ("From: Airport T2", 9, "cour"),
        ("To:   Harbor Inn", 9, "cour"), ("------------------------", 9, "cour"),
        ("Fare            EUR 41.50", 9, "cour"), ("Luggage x2      EUR  4.00", 9, "cour"),
        ("------------------------", 9, "cour"), ("TOTAL           EUR 45.50", 10, "cobo"),
        ("incl. VAT 10%   EUR  4.14", 9, "cour"), ("", 8, "cour"), ("PAID BY CARD  **** 4242", 9, "cobo"),
        ("Thank you - safe travels", 8, "cour"),
    ]
    y = 34
    for text, size, font in lines:
        page.insert_text((22, y), text, fontsize=size, fontname=font)
        y += size + 8
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


DOCS: list[dict] = [
    dict(file="01_nimbus_saas_invoice", color="#4f46e5", currency="€", title="INVOICE",
         seller=["Nimbus Docs", "Collaborative docs for teams", "4 Cloud Avenue, Dublin", "billing@nimbus.example",
                 "VAT ID: IE 0000000XX (sample)"],
         meta=[("Invoice no.", "ND-2026-11873"), ("Date", "01 Sep 2026"), ("Paid", "01 Sep 2026")],
         lines=[("Team plan - annual subscription (12 seats)", 12, 180.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Total paid",
         notes=["Paid by card ending 4242. Thank you for your business."],
         stamp=("PAID", (0.09, 0.6, 0.3)),
         label=dict(doc_type="invoice", category="software_saas", payment_status="paid", vat_shown=True,
                    amount_band="1000_to_10000")),
    dict(file="02_stratus_cloud_invoice", color="#0284c7", currency="$", title="INVOICE",
         seller=["Stratus Cloud", "Infrastructure as a service", "500 Harbor Blvd, Seattle", "invoices@stratus.example"],
         meta=[("Invoice no.", "SC-2026-0917"), ("Billing period", "Sep 2026"), ("Due date", "31 Oct 2026")],
         lines=[("Compute instances (vCPU-hours)", 1240, 0.42), ("Block storage (GB-month)", 800, 0.08),
                ("Data transfer out (GB)", 912, 0.09)],
         tax_rate=0.0, tax_label="Sales tax", total_label="Amount due",
         notes=["Payment is due by 31 Oct 2026. Pay online at the billing console."],
         label=dict(doc_type="invoice", category="cloud_hosting", payment_status="due", vat_shown=False,
                    amount_band="100_to_1000")),
    dict(file="03_kestrel_hardware_invoice", color="#b45309", currency="€", title="INVOICE",
         seller=["Kestrel Computers", "Business IT equipment", "88 Forge Road, Lyon", "sales@kestrel.example"],
         meta=[("Invoice no.", "KC-55102"), ("Date", "12 Sep 2026"), ("Paid", "15 Sep 2026")],
         lines=[("Laptop 14\" Pro, 32 GB RAM", 2, 1890.00), ("27\" 4K monitor", 2, 420.00),
                ("USB-C docking station", 2, 380.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Total",
         notes=["Settled by bank transfer on 15 Sep 2026. Warranty: 3 years on-site."],
         stamp=("PAID", (0.09, 0.6, 0.3)),
         label=dict(doc_type="invoice", category="hardware", payment_status="paid", vat_shown=True,
                    amount_band="1000_to_10000")),
    dict(file="04_harbor_inn_receipt", color="#0f766e", currency="£", title="RECEIPT",
         seller=["Harbor Inn", "Hotel & conference centre", "3 Quay Street, Bristol", "frontdesk@harborinn.example"],
         meta=[("Folio", "HI-88412"), ("Stay", "22-25 Sep 2026"), ("Guest", "J. Doe (Acme Ops)")],
         lines=[("Standard room, 3 nights", 3, 135.00), ("Breakfast", 3, 12.00)],
         tax_rate=0.10, tax_label="VAT included (10%)", total_label="Total charged",
         notes=["Balance: 0.00 - paid by card at check-out. Trip: DevOps conference."],
         label=dict(doc_type="receipt", category="travel", payment_status="paid", vat_shown=True,
                    amount_band="100_to_1000")),
    dict(file="05_copper_pot_receipt", color="#9f1239", currency="€", title="RECEIPT",
         seller=["The Copper Pot", "Restaurant & bar", "21 Market Square, Ghent"],
         meta=[("Table", "12"), ("Date", "18 Sep 2026 13:42"), ("Covers", "4")],
         lines=[("Lunch menu", 4, 28.00), ("Sparkling water", 2, 4.50), ("Coffee", 4, 3.50)],
         tax_rate=0.10, tax_label="VAT 10%", total_label="Paid by card",
         notes=["Client lunch. Thank you and see you soon!"],
         label=dict(doc_type="receipt", category="meals", payment_status="paid", vat_shown=True,
                    amount_band="100_to_1000")),
    dict(file="06_volt_energy_bill", color="#ca8a04", currency="€", title="ELECTRICITY BILL",
         seller=["Volt Grid Energy", "Business electricity", "1 Power Plaza, Rotterdam", "service@voltgrid.example"],
         meta=[("Account", "VG-778120"), ("Period", "Sep 2026"), ("Direct debit on", "15 Oct 2026")],
         lines=[("Consumption, office (kWh)", 4120, 0.24), ("Standing charge (days)", 30, 1.10)],
         tax_rate=0.21, tax_label="VAT 21%", total_label="Amount to be debited",
         notes=["The amount will be collected by direct debit on 15 Oct 2026."],
         label=dict(doc_type="invoice", category="utilities", payment_status="due", vat_shown=True,
                    amount_band="1000_to_10000")),
    dict(file="07_fiberlink_telecom_invoice", color="#7c3aed", currency="€", title="INVOICE",
         seller=["FiberLink Business", "Internet & mobile for companies", "9 Signal Street, Madrid"],
         meta=[("Invoice no.", "FL-2026-30551"), ("Date", "28 Sep 2026"), ("Due date", "10 Oct 2026")],
         lines=[("Fibre 1 Gbps, static IP", 1, 89.00), ("Mobile line, 50 GB", 5, 24.00), ("Router rental", 1, 6.00)],
         tax_rate=0.21, tax_label="VAT 21%", total_label="Amount due",
         label=dict(doc_type="invoice", category="telecom", payment_status="due", vat_shown=True,
                    amount_band="100_to_1000")),
    dict(file="08_paperline_supplies_invoice", color="#15803d", currency="€", title="INVOICE",
         seller=["Paperline Supplies", "Office stationery", "40 Mill Lane, Lille"],
         meta=[("Invoice no.", "PL-9902"), ("Date", "05 Sep 2026"), ("Paid", "05 Sep 2026")],
         lines=[("A4 printer paper, box of 5 reams", 2, 21.50), ("Toner cartridge, black", 1, 24.90),
                ("Notebooks, pack of 10", 1, 12.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Total paid",
         stamp=("PAID", (0.09, 0.6, 0.3)),
         label=dict(doc_type="invoice", category="office_supplies", payment_status="paid", vat_shown=True,
                    amount_band="under_100")),
    dict(file="09_atlas_legal_invoice", color="#1e3a8a", currency="£", title="INVOICE",
         seller=["Atlas Legal LLP", "Commercial law", "2 Temple Row, Birmingham", "accounts@atlaslegal.example"],
         meta=[("Invoice no.", "AL-24-0611"), ("Date", "26 Sep 2026"), ("Due date", "26 Oct 2026")],
         lines=[("Review of SaaS master agreement (hours)", 6.5, 280.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Amount due",
         notes=["Payment terms: 30 days. Please quote the invoice number."],
         label=dict(doc_type="invoice", category="professional_services", payment_status="due", vat_shown=True,
                    amount_band="1000_to_10000")),
    dict(file="10_kestrel_quote", color="#b45309", currency="€", title="QUOTATION",
         seller=["Kestrel Computers", "Business IT equipment", "88 Forge Road, Lyon", "sales@kestrel.example"],
         meta=[("Quote no.", "Q-7781"), ("Date", "29 Sep 2026"), ("Valid until", "29 Oct 2026")],
         lines=[("Laptop 14\" Pro, 32 GB RAM", 10, 1490.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Quoted total",
         notes=["This is a quotation, not an invoice. Sign and return to confirm the order."],
         label=dict(doc_type="quote", category="hardware", payment_status="no_payment_info", vat_shown=True,
                    amount_band="over_10000")),
    dict(file="11_nimbus_credit_note", color="#4f46e5", currency="€", title="CREDIT NOTE",
         seller=["Nimbus Docs", "Collaborative docs for teams", "4 Cloud Avenue, Dublin", "billing@nimbus.example"],
         meta=[("Credit note no.", "CN-2026-0042"), ("Date", "20 Sep 2026"), ("Refers to", "ND-2026-11873")],
         lines=[("Seats removed from Team plan", 2, -180.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Total credited",
         notes=["This amount has been refunded to the card ending 4242."],
         label=dict(doc_type="credit_note", category="software_saas", payment_status=None, vat_shown=True,
                    amount_band=None)),
    dict(file="12_stratus_overdue_reminder", color="#dc2626", currency="$", title="PAYMENT REMINDER",
         seller=["Stratus Cloud", "Infrastructure as a service", "500 Harbor Blvd, Seattle", "invoices@stratus.example"],
         meta=[("Original invoice", "SC-2026-0817"), ("Due date", "31 Aug 2026"), ("Days overdue", "31")],
         lines=[("Unpaid balance, invoice SC-2026-0817", 1, 1190.40)],
         tax_rate=0.0, tax_label="Sales tax", extra=25.00, extra_label="Late payment fee",
         total_label="Now due immediately",
         notes=["Your account is OVERDUE. Services may be suspended if payment is not received within 7 days."],
         stamp=("OVERDUE", (0.85, 0.1, 0.1), (330, 540)),
         label=dict(doc_type="payment_reminder", category="cloud_hosting", payment_status="overdue", vat_shown=False,
                    amount_band="1000_to_10000")),
    dict(file="14_kestrel_repair_invoice", color="#b45309", currency="€", title="INVOICE",
         seller=["Kestrel Computers", "Business IT equipment", "88 Forge Road, Lyon", "sales@kestrel.example"],
         meta=[("Invoice no.", "KC-55188"), ("Date", "24 Sep 2026"), ("Due date", "24 Oct 2026")],
         lines=[("On-site repair: replace cracked laptop screen", 1, 210.00), ("Labour (hours)", 1.5, 60.00)],
         tax_rate=0.20, tax_label="VAT 20%", total_label="Amount due",
         label=dict(doc_type="invoice", category="repairs_maintenance", payment_status="due", vat_shown=True,
                    amount_band="100_to_1000")),
    dict(file="15_northlight_print_invoice", color="#be185d", currency="€", title="INVOICE",
         seller=["Northlight Print", "Digital & offset printing", "5 Harbour Road, Hamburg"],
         meta=[("Invoice no.", "NP-26-4410"), ("Date", "16 Sep 2026"), ("Paid", "16 Sep 2026")],
         lines=[("A5 flyers, 2,000 copies (trade fair)", 1, 340.00), ("Roll-up banner 85x200 cm", 2, 95.00)],
         tax_rate=0.19, tax_label="VAT 19%", total_label="Total (paid)",
         notes=["Thank you for your order!"],
         label=dict(doc_type="invoice", category="marketing", payment_status="paid", vat_shown=True,
                    amount_band="100_to_1000")),
]

TAXI = dict(file="13_taxi_receipt",
            label=dict(doc_type="receipt", category="travel", payment_status="paid", vat_shown=True,
                       amount_band="under_100"))

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

    taxi_pdf = OUT / "_taxi_source.pdf"
    render_thermal(taxi_pdf)
    taxi_jpg = OUT / f"{TAXI['file']}.jpg"
    photo_of(taxi_pdf, taxi_jpg)
    taxi_pdf.unlink()
    labels[taxi_jpg.name] = TAXI["label"]
    print(f"wrote {taxi_jpg} (degraded phone photo)")

    hand = OUT / "16_rays_plumbing_handwritten.pdf"
    render_handwritten(hand)
    labels[hand.name] = HANDWRITTEN_LABEL
    print(f"wrote {hand}")

    (OUT / "labels.json").write_text(json.dumps(dict(sorted(labels.items())), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT / 'labels.json'} ({len(labels)} documents)")


if __name__ == "__main__":
    main()
