"""Shared selection and readable document generation for both export formats."""
from datetime import date
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle, Spacer


def select_events(events, month=None, shows=None):
    # Keep the full schedule's conflict information, even when exporting one show.
    return [e for e in events
            if (not month or e["datum"].startswith(month))
            and (not shows or ("ŽBF 2" if e["naziv_predstave"].startswith("ŽBF 2")
                               else e["naziv_predstave"]) in shows)]


def excel_document(events):
    book = Workbook()
    sheet = book.active
    sheet.title = "Termini"
    sheet.append(["Datum", "Ura", "Predstava", "Lokacija", "Status", "Konflikt s", "Vir", "URL"])
    for e in events:
        sheet.append([date.fromisoformat(e["datum"]), e["ura"] or "", e["naziv_predstave"],
                      e["lokacija"] or "", e["status"], ", ".join(e["konflikt_s"]), e["vir"], e["url"]])
        sheet.cell(sheet.max_row, 1).number_format = "DD.MM.YYYY"
    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            # Scraped text must remain text, including strings starting with '='.
            if isinstance(cell.value, str):
                cell.data_type = "s"
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="123047")
    for col, width in zip("ABCDEFGH", [14, 9, 35, 48, 15, 42, 22, 50]):
        sheet.column_dimensions[col].width = width
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    output = BytesIO()
    book.save(output)
    output.seek(0)
    return output


def pdf_document(events, month=None, shows=None):
    fonts = Path(reportlab.__file__).parent / "fonts"
    for name, filename in [("Export", "Vera.ttf"), ("ExportBold", "VeraBd.ttf")]:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))
    normal = ParagraphStyle("cell", fontName="Export", fontSize=8, leading=11, splitLongWords=True)
    header = ParagraphStyle("header", parent=normal, fontName="ExportBold", textColor=colors.white)
    def paragraph(value, style=normal):
        return Paragraph(escape(str(value or "—")).replace("\n", "<br/>"), style)
    rows = [[paragraph(v, header) for v in ["Datum", "Ura", "Predstava", "Lokacija", "Status", "Konflikt s"]]]
    for e in events:
        rows.append([paragraph(v) for v in [
            date.fromisoformat(e["datum"]).strftime("%d.%m.%Y"), e["ura"],
            e["naziv_predstave"], e["lokacija"], e["status"], ", ".join(e["konflikt_s"])]])
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=28,
                            rightMargin=28, topMargin=28, bottomMargin=32)
    table = Table(rows, repeatRows=1, colWidths=[70, 40, 155, 220, 75, doc.width - 560])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123047")),
        ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    period = f"{month[5:7]}.{month[:4]}" if month else "Vsi meseci"
    description = f"{period} | {', '.join(shows) if shows else 'Vse predstave'} | Terminov: {len(events)}"
    def footer(canvas, document):
        canvas.setFont("Export", 8)
        canvas.drawRightString(landscape(A4)[0] - 28, 16, f"Stran {document.page}")
    doc.build([Paragraph("Termini predstav", ParagraphStyle("title", fontName="ExportBold", fontSize=16, leading=20)),
               Spacer(1, 8), paragraph(description), Spacer(1, 12), table],
              onFirstPage=footer, onLaterPages=footer)
    output.seek(0)
    return output
