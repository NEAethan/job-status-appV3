import pandas as pd
import tempfile
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing

EXPECTED_STATUSES = [
    "Open",
    "Pending",
    "Lead Reviewed",
    "Manager Review",
    "QA Reviewed"
]

COMPLETED_STATUSES = [
    "Lead Reviewed",
    "Manager Review",
    "QA Reviewed"
]

STATUS_COLORS = [
    colors.HexColor("#4A90E2"),
    colors.HexColor("#50E3C2"),
    colors.HexColor("#F5A623"),
    colors.HexColor("#D0021B"),
    colors.HexColor("#9013FE")
]

INDEED_JOB_LOG = (
    "<b>Northeast Air</b><br/>"
    "Portland, ME<br/>"
    "Job Status Activity Summary"
)

# ---------------------------
# Metrics
# ---------------------------
def calculate_status_metrics(df, status_column):
    total_jobs = len(df)
    statuses = df[status_column].astype(str).str.strip().str.lower()
    counts = statuses.value_counts()

    results = []
    for status in EXPECTED_STATUSES:
        key = status.lower()
        count = counts.get(key, 0)
        percent = (count / total_jobs) * 100 if total_jobs else 0
        results.append((status, count, round(percent, 2)))

    completed = sum(counts.get(s.lower(), 0) for s in COMPLETED_STATUSES)
    overall_completion = (completed / total_jobs) * 100 if total_jobs else 0

    return results, overall_completion, completed, total_jobs

# ---------------------------
# PDF
# ---------------------------
def generate_pdf_with_pie_and_legend(
    results,
    overall_completion,
    completed_jobs,
    total_jobs,
    registration,
    serial_number,
    notes
):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Header", fontSize=14, spaceAfter=10))

    elements = []

    # Header
    elements.append(Paragraph(INDEED_JOB_LOG, styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"<b>Aircraft Registration:</b> {registration}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Aircraft Serial Number:</b> {serial_number}", styles["Normal"]))

    if notes:
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"<b>Notes:</b><br/>{notes}", styles["Normal"]))

    elements.append(Spacer(1, 12))

    # Table
    table_data = [["Status", "Jobs", "Percentage (%)"]] + [
        [r[0], r[1], r[2]] for r in results
    ]

    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.75, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 16))

    # ---------------------------
    # SAFE PIE CHART
    # ---------------------------
    values = [r[1] for r in results]

    if sum(values) > 0:
        drawing = Drawing(300, 200)
        pie = Pie()
        pie.x = 90
        pie.y = 10
        pie.width = 150
        pie.height = 150
        pie.data = values
        pie.labels = [""] * len(values)

        for i, slice_ in enumerate(pie.slices):
            slice_.fillColor = STATUS_COLORS[i % len(STATUS_COLORS)]

        drawing.add(pie)
        elements.append(drawing)
        elements.append(Spacer(1, 10))

        # Legend
        legend_data = []
        for i, r in enumerate(results):
            legend_data.append(["■", r[0]])

        legend = Table(legend_data, colWidths=[20, 200])
        legend.setStyle(TableStyle([
            ("TEXTCOLOR", (0, 0), (0, -1), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.white),
        ]))

        elements.append(legend)

    else:
        elements.append(
            Paragraph(
                "<i>No status data available to display chart.</i>",
                styles["Normal"]
            )
        )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf = SimpleDocTemplate(tmp.name, pagesize=LETTER)
    pdf.build(elements)

    return tmp.name
