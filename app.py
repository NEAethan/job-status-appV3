import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
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

# Session storage
if "status_counts" not in st.session_state:
    st.session_state.status_counts = None

# -----------------------------
# PROCESS BUTTON
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
# DISPLAY RESULTS
# -----------------------------
if st.session_state.status_counts:
    st.subheader("Job Status Breakdown")

    fig, ax = plt.subplots()
    ax.pie(
        st.session_state.status_counts.values(),
        labels=st.session_state.status_counts.keys(),
        autopct="%1.1f%%",
        startangle=90
    )
    ax.axis("equal")
    st.pyplot(fig)

# -----------------------------
# PDF GENERATION
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

            elements.append(Paragraph("Job Status Report", styles["Title"]))
            elements.append(Spacer(1, 12))

            elements.append(Paragraph(f"Aircraft Registration: {registration}", styles["Normal"]))
            elements.append(Paragraph(f"Aircraft Serial Number: {serial_number}", styles["Normal"]))
            elements.append(Spacer(1, 12))

            for k, v in st.session_state.status_counts.items():
                elements.append(Paragraph(f"{k}: {v}", styles["Normal"]))

            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Notes", styles["Heading2"]))
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
