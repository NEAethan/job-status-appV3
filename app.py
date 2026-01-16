import streamlit as st
import pandas as pd
import app_extensions_v2 as ext

st.set_page_config(page_title="Job Status Completion App", layout="centered")

st.title("Job Status Completion Report")

# ---------------------------
# User Inputs
# ---------------------------
uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

registration = st.text_input("Aircraft Registration")
serial_number = st.text_input("Aircraft Serial Number")
notes = st.text_area("Notes")

# ---------------------------
# Helper: Find Status Column
# ---------------------------
def find_status_column(df):
    possible_columns = ["Status", "status", "M", "M1"]
    for col in df.columns:
        if col in possible_columns:
            return col
    return None

# ---------------------------
# Process CSV
# ---------------------------
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        status_column = find_status_column(df)

        if status_column is None:
            st.error(
                "No Status column found. Column must be named Status, status, M, or M1."
            )
        else:
            results, overall_completion, completed_jobs, total_jobs = (
                ext.calculate_status_metrics(df, status_column)
            )

            # Display results table
            st.subheader("Status Breakdown")
            results_df = pd.DataFrame(
                results, columns=["Status", "Jobs", "Percentage (%)"]
            )
            st.dataframe(results_df, width="stretch")

            # Overall completion
            st.metric(
                label="Overall Completion Percentage",
                value=f"{round(overall_completion, 2)}%"
            )

            # PDF Export
            st.subheader("Export Report")

            if st.button("Export Results as PDF"):
                pdf_path = ext.generate_pdf_with_pie_and_legend(
                    results=results,
                    overall_completion=overall_completion,
                    completed_jobs=completed_jobs,
                    total_jobs=total_jobs,
                    registration=registration,
                    serial_number=serial_number,
                    notes=notes
                )

                with open(pdf_path, "rb") as f:
                    st
