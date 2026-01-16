"""
Extension module for Job Status Completion Analyzer

This file ADDS functionality without modifying the main app file.
Import and call the helpers from app.py when ready.
"""

import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
import tempfile

# ---- STATUS DEFINITIONS (UPDATED) ----
EXPECTED_STATUSES = [
    "open",
    "pending",
    "Lead Reviewed",
    "Manager Review",   # updated wording
    "QA Reviewed",
]

COMPLETED_STATUSES = [
    "Lead Reviewed",
    "Manager Review",
    "QA Reviewed",
]

EXPECTED_STATUSES_LOWER = [s.lower() for s in EXPECTED_STATUSES]
COMPLETED_STATUSES_LOWER = [s.lower() for s in COMPLETED_STATUSES]


def calculate_status_metrics(df, status_column):
    """Case-insensitive status calculation"""
    total_jobs = len(df)
    status_series = df[status_column].astype(str).str.strip().str.lower()
    status_counts = status_series.value_counts()

    results = []
    for display, key in zip(EXPECTED_STATUSES, EXPECTED_STATUSES_LOWER):
        count = status_counts.get(key, 0)
        percent = (count / total_jobs) * 100 if total_jobs else 0
        results.append((display, count, round(percent, 2)))

    completed_jobs = sum(status_counts.get(s, 0) for s in COMPLETED_STATUSES_LOWER)
    overall_completion = (completed_jobs / total_jobs) * 100 if total_jobs else 0

    return results, overall_completion, completed_jobs, total_jobs


def generate_enhanced_pdf(results, overall_completion, completed_jobs, total_jobs,
                          registration, serial_number):
    """Generates a styled PDF with header info and bar chart"""

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Header",
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkblue
    ))

    elements = []

    # Title
    elements.append(Paragraph("Job Status Completion Report", styles["Header"]))
    elements.append(Paragraph(f"Aircraft Registration: <b>{registration}</b>", styles["Normal"]))
    elements.append(Paragraph(f"Aircraft Serial Number: <b>{serial_number}</b>", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Summary
    elements.append(Paragraph(f"Total Jobs: {total_jobs}", styles["Normal"]))
    elements.append(Paragraph(
        f"Overall Completion: <b>{round(overall_completion, 2)}%</b> ",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 12))

    # Table
    table_data = [["Status", "Jobs", "Percentage (%)"]]
    for status, jobs, pct in results:
        table_data.append([status, str(jobs), str(pct)])

    table = Table(table_data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E6EEF6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('GRID', (0, 0), (-1, -1), 0.75, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # Bar chart
    drawing = Drawing(400, 200)
    chart = VerticalBarChart()
    chart.x = 50
    chart.y = 30
    chart.height = 150
    chart.width = 300
    chart.data = [[r[1] for r in results]]
    chart.categoryAxis.categoryNames = [r[0] for r in results]
    chart.valueAxis.valueMin = 0
    chart.barWidth = 20
    chart.groupSpacing = 10
    chart.bars[0].fillColor = colors.HexColor('#4A90E2')

    drawing.add(chart)
    elements.append(drawing)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf = SimpleDocTemplate(tmp.name, pagesize=LETTER)
    pdf.build(elements)

    return tmp.name
