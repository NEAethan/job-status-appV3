import pandas as pd
import streamlit as st
import app_extensions
import app_extensions_v2 as ext


st.set_page_config(page_title="Job Status Completion", layout="centered")

st.title("Job Status Completion Analyzer")
st.write("Upload a CSV file to see the percentage of jobs in each status, overall completion, and export results as a PDF.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

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

        # Calculate metrics using the extension
        results, overall_completion, completed_jobs, total_jobs = app_extensions.calculate_status_metrics(df, status_column)

        # Display table
        result_df = pd.DataFrame(results, columns=["Status", "Jobs", "Percentage"])
        st.subheader("Completion Breakdown")
        st.dataframe(result_df, use_container_width=True)

        # Display overall completion
        st.subheader("Overall Completion")
        st.metric(
            label="Jobs Completed",
            value=f"{round(overall_completion, 2)}%",
            delta=f"{completed_jobs} of {total_jobs} jobs"
        )

        # Aircraft info inputs
        registration = st.text_input("Aircraft Registration")
        serial_number = st.text_input("Aircraft Serial Number")

        notes = st.text_area("Notes")


        # PDF export using enhanced layout
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
        st.download_button(
            label="Download Enhanced PDF",
            data=f,
            file_name="job_status_completion_report.pdf",
            mime="application/pdf"
        )



    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("Please upload a CSV file to begin.")

