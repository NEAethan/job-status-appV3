import pandas as pd
import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import tempfile

st.set_page_config(page_title="Job Status Completion", layout="centered")

st.title("Job Status Completion Analyzer")
st.write("Upload a CSV file to see the percentage of jobs in each status, overall completion, and export results as a PDF.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

EXPECTED_STATUSES = [
    "open",
    "pending",
    "Lead Reviewed",
    "Manager Reviewed",
    "QA Reviewed",
]

# Define what counts as "complete"
COMPLETED_STATUSES = [
    "Lead Reviewed",
    "Manager Reviewed",
    "QA Reviewed",
]
# --- User inputs for aircraft info ---
registration = st.text_input("Aircraft Registration")
serial_number = st.text_input("Aircraft Serial Number")

# Normalize expected statuses to lowercase for matching
EXPECTED_STATUSES_LOWER = [s.lower() for s in EXPECTED_STATUSES]
COMPLETED_STATUSES_LOWER = [s.lower() for s in COMPLETED_STATUSES]

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        # Normalize column names for detection
        normalized_columns = {col.lower(): col for col in df.columns}

        # Determine which column to use for status
        status_column = None
        for candidate in ["status", "m", "m1"]:
            if candidate in normalized_columns:
                status_column = normalized_columns[candidate]
                break

        if status_column is None:
            st.error("CSV must contain a status column named 'Status', 'status', 'M', or 'M1'.")
            st.stop()

        total_jobs = len(df)

        # Normalize status values to lowercase for counting
        status_series = df[status_column].astype(str).str.strip().str.lower()
        status_counts = status_series.value_counts()

        results = []
        for display_status, match_status in zip(EXPECTED_STATUSES, EXPECTED_STATUSES_LOWER):
            count = status_counts.get(match_status, 0)
            percent = (count / total_jobs) * 100 if total_jobs > 0 else 0
            results.append({
                "Status": display_status,
                "Jobs": count,
                "Percentage": round(percent, 2)
            })

        result_df = pd.DataFrame(results)

        completed_jobs = sum(status_counts.get(s, 0) for s in COMPLETED_STATUSES_LOWER)
        overall_completion = (completed_jobs / total_jobs) * 100 if total_jobs > 0 else 0

        st.subheader("Completion Breakdown")
        st.dataframe(result_df, use_container_width=True)

        st.subheader("Overall Completion")
        st.metric(
            label="Jobs Completed",
            value=f"{round(overall_completion, 2)}%",
            delta=f"{completed_jobs} of {total_jobs} jobs"
        )

        def generate_pdf():
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("Job Status Completion Report", styles['Title']))
            elements.append(Paragraph(f"Total Jobs: {total_jobs}", styles['Normal']))
            elements.append(Paragraph(f"Overall Completion: {round(overall_completion, 2)}%", styles['Normal']))

            table_data = [["Status", "Jobs", "Percentage (%)"]]
            for _, row in result_df.iterrows():
                table_data.append([
                    row["Status"],
                    str(row["Jobs"]),
                    str(row["Percentage"])
                ])

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ]))

            elements.append(table)

            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            pdf = SimpleDocTemplate(tmp_file.name)
            pdf.build(elements)

            return tmp_file.name

        if st.button("Export Results as PDF"):
            pdf_path = generate_pdf()
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download PDF",
                    data=f,
                    file_name="job_status_completion_report.pdf",
                    mime="application/pdf"
                )

    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("Please upload a CSV file to begin.")
