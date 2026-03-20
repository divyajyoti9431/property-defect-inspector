import os
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Brand colours
C_DARK_BLUE = HexColor("#1B3A6B")
C_MID_BLUE = HexColor("#2563EB")
C_LIGHT_BLUE = HexColor("#DBEAFE")
C_RED = HexColor("#DC2626")
C_ORANGE = HexColor("#D97706")
C_GREEN = HexColor("#16A34A")
C_GRAY_BG = HexColor("#F9FAFB")
C_GRAY_BORDER = HexColor("#E5E7EB")
C_GRAY_TEXT = HexColor("#6B7280")
C_DARK_TEXT = HexColor("#111827")
C_WHITE = HexColor("#FFFFFF")

SEV_COLOR = {"major": "#DC2626", "moderate": "#D97706", "minor": "#16A34A"}
SEV_BG = {"major": "#FEF2F2", "moderate": "#FFFBEB", "minor": "#F0FDF4"}
COND_COLOR = {"good": C_GREEN, "fair": C_ORANGE, "poor": C_RED}


def _style(name, base, **kwargs):
    s = ParagraphStyle(name, parent=base)
    for k, v in kwargs.items():
        setattr(s, k, v)
    return s


def generate_pdf(session_data: dict, output_path: str) -> None:
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )

    base = getSampleStyleSheet()["Normal"]
    W = 174 * mm  # usable page width

    # ── styles ──────────────────────────────────────────────────
    s_title = _style("Title", base, fontSize=20, fontName="Helvetica-Bold",
                     textColor=C_WHITE, alignment=TA_CENTER)
    s_sub = _style("Sub", base, fontSize=9, fontName="Helvetica",
                   textColor=C_LIGHT_BLUE, alignment=TA_CENTER)
    s_section = _style("Section", base, fontSize=12, fontName="Helvetica-Bold",
                       textColor=C_DARK_BLUE, spaceBefore=8, spaceAfter=4)
    s_body = _style("Body", base, fontSize=8.5, fontName="Helvetica",
                    textColor=C_DARK_TEXT, spaceAfter=3, leading=12)
    s_bold = _style("Bold", base, fontSize=8.5, fontName="Helvetica-Bold",
                    textColor=C_DARK_TEXT)
    s_label = _style("Label", base, fontSize=7.5, fontName="Helvetica-Bold",
                     textColor=C_GRAY_TEXT)
    s_white = _style("White", base, fontSize=8, fontName="Helvetica-Bold",
                     textColor=C_WHITE, alignment=TA_CENTER)
    s_white_big = _style("WhiteBig", base, fontSize=22, fontName="Helvetica-Bold",
                         textColor=C_WHITE, alignment=TA_CENTER)
    s_footer = _style("Footer", base, fontSize=7, fontName="Helvetica",
                      textColor=C_GRAY_TEXT, alignment=TA_CENTER)
    s_th = _style("TH", base, fontSize=8, fontName="Helvetica-Bold", textColor=C_WHITE)
    s_td = _style("TD", base, fontSize=8, fontName="Helvetica", textColor=C_DARK_TEXT,
                  leading=11)

    elems = []

    # ── HEADER ───────────────────────────────────────────────────
    hdr = Table(
        [[Paragraph("PROPERTY DEFECT INSPECTION REPORT", s_title)],
         [Paragraph("Singapore Property Inspection System · AI-Powered Computer Vision", s_sub)]],
        colWidths=[W],
    )
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_DARK_BLUE),
        ("TOPPADDING", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elems.append(hdr)
    elems.append(Spacer(1, 6 * mm))

    # ── PROPERTY DETAILS ─────────────────────────────────────────
    elems.append(Paragraph("INSPECTION DETAILS", s_section))
    elems.append(HRFlowable(width="100%", thickness=1.5, color=C_DARK_BLUE))
    elems.append(Spacer(1, 3 * mm))

    rows = [
        ["Property Address", session_data.get("property_address", "N/A"),
         "Unit No.", session_data.get("unit_number", "N/A")],
        ["Property Owner", session_data.get("owner_name", "N/A"),
         "Inspection Date", session_data.get("inspection_date", "N/A")],
        ["Inspecting Agent", session_data.get("agent_name", "N/A"),
         "Report Generated", datetime.now().strftime("%d %b %Y  %H:%M")],
    ]
    det = Table(
        [[Paragraph(c, s_bold if i % 2 == 0 else s_body) for i, c in enumerate(r)]
         for r in rows],
        colWidths=[36 * mm, 54 * mm, 28 * mm, 56 * mm],
    )
    det.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), C_LIGHT_BLUE),
        ("BACKGROUND", (2, 0), (2, -1), C_LIGHT_BLUE),
        ("TEXTCOLOR", (0, 0), (0, -1), C_DARK_BLUE),
        ("TEXTCOLOR", (2, 0), (2, -1), C_DARK_BLUE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, C_GRAY_BORDER),
    ]))
    elems.append(det)
    elems.append(Spacer(1, 7 * mm))

    # ── SUMMARY COUNTERS ─────────────────────────────────────────
    results = session_data.get("results", [])
    total = major = moderate = minor = 0
    for r in results:
        for d in r.get("analysis", {}).get("defects", []):
            total += 1
            s = d.get("severity", "minor").lower()
            if s == "major":
                major += 1
            elif s == "moderate":
                moderate += 1
            else:
                minor += 1

    elems.append(Paragraph("INSPECTION SUMMARY", s_section))
    elems.append(HRFlowable(width="100%", thickness=1.5, color=C_DARK_BLUE))
    elems.append(Spacer(1, 3 * mm))

    cols = [
        (str(total), "TOTAL DEFECTS", C_DARK_BLUE),
        (str(major), "MAJOR", C_RED),
        (str(moderate), "MODERATE", C_ORANGE),
        (str(minor), "MINOR", C_GREEN),
        (str(len(results)), "IMAGES ANALYZED", HexColor("#4B5563")),
    ]
    cnt_data = [
        [Paragraph(v, s_white_big) for v, _, _ in cols],
        [Paragraph(lbl, s_white) for _, lbl, _ in cols],
    ]
    cnt = Table(cnt_data, colWidths=[W / 5] * 5)
    style_cmds = [
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]
    for i, (_, _, color) in enumerate(cols):
        style_cmds.append(("BACKGROUND", (i, 0), (i, -1), color))
    cnt.setStyle(TableStyle(style_cmds))
    elems.append(cnt)
    elems.append(Spacer(1, 5 * mm))

    # ── BUYER RECOMMENDATION BANNER ───────────────────────────────
    rec_counts = {"buy": 0, "negotiate": 0, "avoid": 0}
    for r in results:
        rec = r.get("analysis", {}).get("buyer_recommendation", "negotiate").lower()
        if rec in rec_counts:
            rec_counts[rec] += 1

    if rec_counts["avoid"] > 0:
        rec_label, rec_color, rec_note = "⛔  AVOID PURCHASE", C_RED, "Major defects found — high risk investment"
    elif rec_counts["negotiate"] > 0:
        rec_label, rec_color, rec_note = "⚠️  NEGOTIATE PRICE", C_ORANGE, "Defects found — negotiate repair costs with seller"
    else:
        rec_label, rec_color, rec_note = "✅  RECOMMENDED TO BUY", C_GREEN, "Property appears to be in good condition"

    rec_banner = Table(
        [[Paragraph(rec_label, _style("RecLbl", base, fontSize=13, fontName="Helvetica-Bold",
                                      textColor=C_WHITE, alignment=TA_CENTER)),
          Paragraph(rec_note, _style("RecNote", base, fontSize=9, fontName="Helvetica",
                                     textColor=C_WHITE, alignment=TA_CENTER))]],
        colWidths=[W * 0.4, W * 0.6],
    )
    rec_banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), rec_color),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elems.append(rec_banner)
    elems.append(Spacer(1, 8 * mm))

    # ── PER-IMAGE DEFECT DETAILS ──────────────────────────────────
    elems.append(Paragraph("DEFECT DETAILS BY IMAGE", s_section))
    elems.append(HRFlowable(width="100%", thickness=1.5, color=C_DARK_BLUE))

    for idx, result in enumerate(results):
        filename = result.get("filename", f"Image {idx + 1}")
        analysis = result.get("analysis", {})
        defects = analysis.get("defects", [])
        overall = analysis.get("overall_condition", "unknown").lower()
        summary_txt = analysis.get("summary", "")
        cond_color = COND_COLOR.get(overall, HexColor("#4B5563"))

        block_elems = [Spacer(1, 5 * mm)]

        # Image header bar
        img_hdr = Table(
            [[Paragraph(f"Image {idx + 1}: {filename}", s_th),
              Paragraph(f"Overall: {overall.upper()}", _style(
                  "CondR", base, fontSize=8, fontName="Helvetica-Bold",
                  textColor=C_WHITE, alignment=TA_RIGHT))]],
            colWidths=[W * 0.65, W * 0.35],
        )
        img_hdr.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_DARK_BLUE),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        block_elems.append(img_hdr)

        # Thumbnail + summary row
        file_path = result.get("file_path", "")
        img_widget = None
        if file_path and os.path.exists(file_path) and PIL_AVAILABLE:
            try:
                pil = PILImage.open(file_path)
                w_px, h_px = pil.size
                max_w, max_h = 78 * mm, 58 * mm
                ratio = min(max_w / w_px, max_h / h_px)
                img_widget = Image(file_path, width=w_px * ratio, height=h_px * ratio)
            except Exception:
                pass

        if img_widget:
            left_cell = img_widget
        else:
            left_cell = Paragraph(f"[Image: {filename}]", s_body)

        right_cell = Paragraph(
            f"<b>AI Assessment:</b> {summary_txt}" if summary_txt else "", s_body
        )

        thumb_row = Table([[left_cell, right_cell]], colWidths=[82 * mm, 92 * mm])
        thumb_row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), C_GRAY_BG),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BOX", (0, 0), (-1, -1), 0.5, C_GRAY_BORDER),
        ]))
        block_elems.append(thumb_row)

        if not defects:
            ok_row = Table(
                [[Paragraph("✓  No defects detected in this image.", _style(
                    "OK", base, fontSize=9, fontName="Helvetica",
                    textColor=C_GREEN))]],
                colWidths=[W],
            )
            ok_row.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F0FDF4")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 1, HexColor("#86EFAC")),
            ]))
            block_elems.append(ok_row)
        else:
            # Defect table — includes buyer_impact column
            hdr_row = [
                Paragraph("Category", s_th),
                Paragraph("Description & Location", s_th),
                Paragraph("Severity", s_th),
                Paragraph("Buyer Impact (₹)", s_th),
                Paragraph("Action Required", s_th),
            ]
            tbl_rows = [hdr_row]
            for d in defects:
                sev = d.get("severity", "minor").lower()
                sev_hex = SEV_COLOR.get(sev, "#16A34A")
                desc = d.get("description", "")
                loc = d.get("location", "")
                desc_loc = f"{desc}<br/><i><font color='#6B7280'>📍 {loc}</font></i>" if loc else desc
                tbl_rows.append([
                    Paragraph(d.get("category", ""), s_td),
                    Paragraph(desc_loc, s_td),
                    Paragraph(
                        f'<font color="{sev_hex}"><b>{sev.upper()}</b></font>', s_td
                    ),
                    Paragraph(d.get("buyer_impact", "—"), s_td),
                    Paragraph(d.get("action_required", ""), s_td),
                ])

            dtbl = Table(
                tbl_rows,
                colWidths=[28 * mm, 54 * mm, 16 * mm, 38 * mm, 38 * mm],
            )
            ts = [
                ("BACKGROUND", (0, 0), (-1, 0), C_DARK_BLUE),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.4, C_GRAY_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
            for i in range(1, len(tbl_rows)):
                if i % 2 == 0:
                    ts.append(("BACKGROUND", (0, i), (-1, i), C_GRAY_BG))
            dtbl.setStyle(TableStyle(ts))
            block_elems.append(dtbl)

        elems.append(KeepTogether(block_elems))

    # ── FOOTER ───────────────────────────────────────────────────
    elems.append(Spacer(1, 10 * mm))
    elems.append(HRFlowable(width="100%", thickness=0.8, color=C_GRAY_BORDER))
    elems.append(Spacer(1, 3 * mm))
    elems.append(Paragraph(
        f"Report generated by AI Property Defect Inspection System on "
        f"{datetime.now().strftime('%d %B %Y at %H:%M')}. "
        "This is an AI-assisted inspection — verify critical findings with a qualified BCA-registered inspector. "
        "Analysis is based on visual data only.",
        s_footer,
    ))

    doc.build(elems)
