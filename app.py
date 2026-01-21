import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import LETTER
from io import BytesIO

st.set_page_config(page_title="Job Status Report", layout="wide")

st.title("Job Status Report Generator")

# -----------------------------
# USER INPUTS
# -----------------------------
uploaded_file = st.file_uploader("Upload Job Status CSV", type=["csv"])

registration = st.text_input("Aircraft Registration")
serial_number = st.text_input("Aircraft Serial Number")
notes = st.text_area("Notes")

# -----------------------------
# SAFE DATA PROCESSING
# -----------------------------
status_counts = {}

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        # find status column
        status_col = None
        for col in df.columns:
            if col.lower() in ["status", "m", "m1"]:
                status_col = col
                break

        if status_col is None:
            st.error("No Status column found.")
        else:
            df[status_col] = df[status_col].astype(str).str.lower()

            statuses = {
                "lead reviewed": "Lead Reviewed",
                "manager review": "Manager Review",
                "complete": "Complete"
            }

            for key in statuses:
                status_counts[statuses[key]] = df[status_col].str.contains(key).sum()

            st.success("File processed successfully.")

    except Exception as e:
        st.error(f"Error processing file: {e}")

# -----------------------------
# DISPLAY PIE CHART
# -----------------------------
if status_counts:
    fig, ax = plt.subplots()
    ax.pie(
        status_counts.values(),
        labels=status_counts.keys(),
        autopct="%1.1f%%",
        startangle=90
    )
    ax.axis("equal")
    st.pyplot(fig)

# -----------------------------
# PDF GENERATION (BUTTON ONLY)
# -----------------------------
if st.button("Export PDF"):
    if not status_counts:
        st.error("No data available to export.")
    else:
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=LETTER)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("Job Status Report", styles["Title"]))
            elements.append(Spacer(1, 12))

            elements.append(Paragraph(f"Aircraft Registration: {registration}", styles["Normal"]))
            elements.append(Paragraph(f"Serial Number: {serial_number}", styles["Normal"]))
            elements.append(Spacer(1, 12))

            for k, v in status_counts.items():
                elements.append(Paragraph(f"{k}: {v}", styles["Normal"]))

            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Notes:", styles["Heading2"]))
            elements.append(Paragraph(notes or "N/A", styles["Normal"]))

            doc.build(elements)

            st.download_button(
                "Download PDF",
                data=buffer.getvalue(),
                file_name="job_status_report.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"PDF generation failed: {e}")
