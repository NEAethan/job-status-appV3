import matplotlib
matplotlib.use("Agg")  # Important for Streamlit Cloud headless environment

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
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

# Session storage for results
if "status_counts" not in st.session_state:
    st.session_state.status_counts = None

# -----------------------------
# PROCESS CSV BUTTON
# -----------------------------
if st.button("Process CSV"):
    if uploaded_file is None:
        st.error("Please upload a CSV file first.")
    else:
        try:
            df = pd.read_csv(uploaded_file)

            # Find status column
            status_col = None
            for col in df.columns:
                if col.lower() in ["status", "m", "m1"]:
                    status_col = col
                    break

            if status_col is None:
                st.error("No Status column found.")
            else:
                statuses = df[status_col].astype(str).str.lower()

                # Count occurrences (case-insensitive)
                st.session_state.status_counts = {
                    "Lead Reviewed": statuses.str.contains("lead reviewed").sum(),
                    "Manager Review": statuses.str.contains("manager review").sum(),
                    "QA Reviewed": statuses.str.contains("qa reviewed").sum(),
                    "Complete": statuses.str.contains("complete").sum(),
                }

                st.success("CSV processed successfully.")

        except Exception as e:
            st.error(f"Error processing CSV: {e}")

# -----------------------------
# DISPLAY BAR GRAPH
# -----------------------------
if st.session_state.status_counts:
    st.subheader("Job Status Breakdown")

    # Professional bar chart
    fig, ax = plt.subplots(figsize=(8,5))

    bars = ax.bar(
        st.session_state.status_counts.keys(),
        st.session_state.status_counts.values(),
        color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],  # professional colors
    )

    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)

    # Styling
    ax.set_ylabel("Number of Jobs")
    ax.set_xlabel("Status")
    ax.set_title("Job Status Summary", fontsize=14, fontweight='bold')
    ax.set_ylim(0, max(st.session_state.status_counts.values()) * 1.2)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)  # horizontal gridlines
    plt.xticks(rotation=30, ha='right')  # rotate labels to avoid overlap
    plt.tight_layout()

    st.pyplot(fig)

# -----------------------------
# PDF GENERATION BUTTON
# -----------------------------
if st.button("Export PDF"):
    if not st.session_state.status_counts:
        st.error("Please process a CSV first.")
    else:
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=LETTER)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            elements.append(Paragraph("Job Status Report", styles["Title"]))
            elements.append(Spacer(1, 12))

            # Aircraft info
            elements.append(Paragraph(f"Aircraft Registration: {registration}", styles["Normal"]))
            elements.append(Paragraph(f"Serial Number: {serial_number}", styles["Normal"]))
            elements.append(Spacer(1, 12))

            # Status counts
            for k, v in st.session_state.status_counts.items():
                elements.append(Paragraph(f"{k}: {v}", styles["Normal"]))

            elements.append(Spacer(1, 12))

            # Notes
            elements.append(Paragraph("Notes", styles["Heading2"]))
            elements.append(Paragraph(notes or "N/A", styles["Normal"]))

            # Build PDF
            doc.build(elements)

            # Download button
            st.download_button(
                "Download PDF",
                data=buffer.getvalue(),
                file_name="job_status_report.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"PDF generation failed: {e}")
