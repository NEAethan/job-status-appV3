import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
import tempfile

# Status definitions
EXPECTED_STATUSES = ["open", "pending", "Lead Reviewed", "Manager Review", "QA Reviewed"]
COMPLETED_STATUSES = ["Lead Reviewed", "Manager Review", "QA Reviewed"]
COLORS = [colors.HexColor("#4A90E2"), colors.HexColor("#50E3C2"), colors.HexColor("#F5A623"), colors.HexColor("#D0021B"), colors.HexColor("#9013FE")]
EXPECTED_STATUSES_LOWER = [s.lower() for s in EXPECTED_STATUSES]
COMPLETED_STATUSES_LOWER = [s.lower() for s in COMPLETED_STATUSES]

# Example Indeed job log text
INDEED_JOB_LOG = (
    "Northeast Air L, Portland, ME Jobs: Full listing from Indeed.com, includes job titles, postings, and locations."
)

def calculate_status_metrics(df, status_column):
    total_jobs = len(df)
    status_series = df[status_column].astype(str).str.strip().str.lower()
    status_counts = status_series.value_counts()
    results = []
    for display, key in zip(EXPECTED_STATUSES, EXPECTED_STATUSES_LOWER):
        count = status_counts.get(key,0)
        percent = (count/total_jobs)*100 if total_jobs else 0
        results.append((display,count,round(percent,2)))
    completed_jobs = sum(status_counts.get(s,0) for s in COMPLETED_STATUSES_LOWER)
    overall_completion = (completed_jobs/total_jobs)*100 if total_jobs else 0
    return results, overall_completion, completed_jobs, total_jobs

class Legend(Flowable):
    """Custom legend for pie chart"""
    def __init__(self, labels, colors, width=200, height=20):
        Flowable.__init__(self)
        self.labels = labels
        self.colors = colors
        self.width = width
        self.height = height

    def draw(self):
        x = 0
        for label, color in zip(self.labels, self.colors):
            self.canv.setFillColor(color)
            self.canv.rect(x, 0, 10, 10, fill=1)
            self.canv.setFillColor(colors.black)
            self.canv.drawString(x + 12, 0, label)
            x += 80

def generate_pdf_with_pie_and_legend(results, overall_completion, completed_jobs, total_jobs, registration, serial_number, notes):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('Header', fontSize=16, textColor=colors.darkblue, spaceAfter=12))
    elements = []

    # Indeed job log top-left
    elements.append(Paragraph(f"<b>Job Log:</b><br/>{INDEED_JOB_LOG}", styles['Normal']))
    elements.append(Spacer(1,12))

    # Aircraft info
    elements.append(Paragraph(f"Aircraft Registration: <b>{registration}</b>", styles['Normal']))
    elements.append(Paragraph(f"Aircraft Serial Number: <b>{serial_number}</b>", styles['Normal']))
    if notes:
        elements.append(Paragraph(f"<b>Notes:</b> {notes}", styles['Normal']))
    elements.append(Spacer(1,12))

    # Status table
    table_data = [["Status","Jobs","Percentage (%)"]]+[[r[0],str(r[1]),str(r[2])] for r in results]
    table = Table(table_data, hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
                               ('GRID',(0,0),(-1,-1),0.75,colors.grey),
                               ('ALIGN',(1,1),(-1,-1),'CENTER'),
                               ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
    elements.append(table)
    elements.append(Spacer(1,12))

    # Pie chart
    drawing = Drawing(300,200)
    pie = Pie()
    pie.x = 100
    pie.y = 0
    pie.width = 150
    pie.height = 150
    pie.data = [r[1] for r in results]
    pie.labels = ["" for _ in results]  # hide labels on slices
    for i, s in enumerate(pie.slices):
        s.fillColor = COLORS[i % len(COLORS)]
        s.strokeWidth = 0.5
    drawing.add(pie)
    elements.append(drawing)

    # Legend under pie chart
    legend = Legend(labels=[r[0] for r in results], colors=COLORS[:len(results)])
    elements.append(Spacer(1,6))
    elements.append(legend)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf = SimpleDocTemplate(tmp.name, pagesize=LETTER)
    pdf.build(elements)
    return tmp.name
