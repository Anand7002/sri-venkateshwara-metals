from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# -------- COLORS --------
ACCENT = colors.black
TEXT_LIGHT = colors.HexColor("#6B7280")
BG_LIGHT = colors.HexColor("#F3F4F6")

DEFAULT_FONT_NAME = "Helvetica"

FONT_SEARCH_PATHS = [
    Path(__file__).resolve().parent / "fonts",
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts/truetype/noto"),
    Path("/usr/share/fonts/truetype/liberation"),
    Path("/usr/share/fonts/truetype/freefont"),
    Path("C:/Windows/Fonts"),
]

FONT_CANDIDATES = [
    ("NotoSans", "NotoSans-Regular.ttf"),
    ("Roboto", "Roboto-Regular.ttf"),
    ("DejaVuSans", "DejaVuSans.ttf"),
    ("NirmalaUI", "Nirmala.ttf"),
    ("ArialUnicode", "arialuni.ttf"),
    ("SegoeUI", "segoeui.ttf"),
    ("Arial", "arial.ttf"),
]


def _resolve_font_name():
    for font_name, filename in FONT_CANDIDATES:
        for directory in FONT_SEARCH_PATHS:
            font_path = directory / filename
            if font_path.exists():
                if font_name not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                return font_name
    return DEFAULT_FONT_NAME


INVOICE_FONT = _resolve_font_name()
NORMAL_FONT = INVOICE_FONT
BOLD_FONT = (
    f"{INVOICE_FONT}-Bold"
    if f"{INVOICE_FONT}-Bold" in pdfmetrics.getRegisteredFontNames()
    else INVOICE_FONT
)


def generate_invoice_pdf(invoice):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=10 * mm,
    )

    styles = getSampleStyleSheet()

    # -------- STYLES --------
    styles.add(ParagraphStyle(
        name="InvoiceTitle",
        fontName=BOLD_FONT,
        fontSize=20,
        alignment=1,
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        name="Label",
        fontName=BOLD_FONT,
        fontSize=9,
    ))

    styles.add(ParagraphStyle(
        name="Value",
        fontName=NORMAL_FONT,
        fontSize=10,
        leading=14,
    ))

    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontName=BOLD_FONT,
        fontSize=11,
        spaceBefore=10,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="Currency",
        fontName=BOLD_FONT,
        fontSize=10,
        alignment=2,
    ))

    elements = []

    # -------- TITLE --------
    elements.append(Paragraph("<b>Sri Venkateswara Metals</b>", styles["InvoiceTitle"]))

    # -------- HEADER --------
    header_table = Table(
        [[
            Paragraph(
                "Mobile: +91 87786 55591<br/>"
                "GSTIN: 33BRLPM124C1ZA<br/>"
                "Dhramapuri Main Road, Pochampalli – 635206",
                styles["Value"],
            ),
            Paragraph(
                f"<b>Invoice No:</b> {invoice.invoice_no}<br/>"
                f"<b>Date:</b> {invoice.date.strftime('%d %b %Y %I:%M %p')}",
                styles["Value"],
            ),
        ]],
        colWidths=[doc.width * 0.6, doc.width * 0.4],
    )

    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(header_table)

    # Divider
    elements.append(Table([[""]], colWidths=[doc.width],
        style=[('LINEBELOW', (0, 0), (-1, -1), 1, colors.black)]
    ))

    # -------- BILL TO --------
    if invoice.customer:
        bill_to = Table([[
            Paragraph(
                "<b>BILL TO</b><br/><br/>"
                f"<b>{invoice.customer.name}</b><br/>"
                f"Phone: {invoice.customer.phone or '-'}",
                styles["Value"],
            )
        ]], colWidths=[doc.width])

        bill_to.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(Spacer(1, 8))
        elements.append(bill_to)

    # -------- ITEMS --------
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("ITEM DETAILS", styles["SectionTitle"]))

    table_data = [["S.No", "Item", "Price", "QTY", "Line Total"]]

    for idx, line in enumerate(invoice.items.select_related("item"), start=1):
        line_total = line.price * line.quantity
        table_data.append([
            str(idx),
            line.item.name,
            Paragraph(f"₹{float(line.price):,.2f}", styles["Currency"]),
            f"{float(line.quantity):,.3f} kgs",
            Paragraph(f"₹{float(line_total):,.2f}", styles["Currency"]),
        ])

    item_table = Table(
        table_data,
        colWidths=[
            doc.width * 0.07,
            doc.width * 0.33,
            doc.width * 0.18,
            doc.width * 0.14,
            doc.width * 0.28,
        ],
        repeatRows=1,
    )

    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), BOLD_FONT),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
    ]))

    elements.append(item_table)

    # -------- SUMMARY --------
    payable = invoice.total_amount + invoice.gst_amount - invoice.discount

    elements.append(Spacer(1, 10))
    summary_table = Table([
        [Paragraph(f"Subtotal : ₹{invoice.total_amount:,.2f}", styles["Currency"])],
        [Paragraph(f"GST : ₹{invoice.gst_amount:,.2f}", styles["Currency"])],
        [Paragraph(f"Discount : ₹{invoice.discount:,.2f}", styles["Currency"])],
        [Paragraph(f"<b>Total Payable : ₹{payable:,.2f}</b>", styles["Currency"])],
    ], colWidths=[doc.width])

    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))

    elements.append(summary_table)

    # -------- FOOTER --------
    elements.append(Spacer(1, 12))
    elements.append(Table([[""]], colWidths=[doc.width],
        style=[('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.black)]
    ))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "<b>Thank you for choosing our service!</b><br/>"
        "<font color='#6B7280'>For queries, contact +91 87786 55591</font>",
        styles["Label"],
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
