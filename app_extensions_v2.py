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

# ---------------------------
# Status Definitions
# ---------------------------
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

# Job log text (placeholder – replace with logo later if desired)
INDEED_JOB_LOG = (
    "<b>Northeast Air</b><br/>"
    "Portland, ME<br/>"
    "Job Status Activity Summary"
)

# ---------------------------
# Metrics Calculation
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

    completed = sum(
        counts.get(s.lower(), 0) for s in COMPLETED_STATUSES
    )
    overall_completion = (completed / total_jobs) * 100 if total_jobs else 0

    return results, overall_completion, completed, total_jobs

# ---------------------------
# PDF Generation
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
    styles.add(
        ParagraphStyle(
            "Header",
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=10
        )
    )

    elements = []

    # Header / Job log
    elements.append(Paragraph(INDEED_JOB_LOG, styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Aircraft info
    elements.append(
        Paragraph(f"<b>Aircraft Registration:</b> {registration}", styles["Normal"])
    )
    elements.append(
        Paragraph(f"<b>Aircraft Serial Number:</b> {serial_number}", styles["Normal"])
    )

    if notes:
        elements.append(Spacer(1, 6))
        elements.append(
            Paragraph(f"<b>Notes:</b><br/>{notes}", styles["Normal"])
        )

    elements.append(Spacer(1, 12))

    # Status table
    table_data = [["Status", "Jobs", "Percentage (%)"]] + [
        [r[0], str(r[1]), str(r[2])] for r in results
    ]

    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.75, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 14))

    # Pie chart
    drawing = Drawing(300, 200)
    pie = Pie()
    pie.x = 90
    pie.y = 10
    pie.width = 150
    pie.height = 150
    pie.data = [r[1] for r in results]
    pie.labels = [""] * len(results)

    for i, slice_ in enumerate(pie.slices):
        slice_.fillColor = STATUS_COLORS[i]

    drawing.add(pie)
    elements.append(drawing)
    elements.append(Spacer(1, 10))

    # Legend (SAFE TABLE VERSION)
    legend_data = []
    for label, color in zip([r[0] for r in results], STATUS_COLORS):
        legend_data.append(
            [Paragraph(" ", styles["Normal"]), label]
        )

    legend_table = Table(legend_data, colWidths=[20, 200])
    legend_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.white),
    ]))

    elements.append(legend_table)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf = SimpleDocTemplate(tmp.name, pagesize=LETTER)
    pdf.build(elements)

    return tmp.name
