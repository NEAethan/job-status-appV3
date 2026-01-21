import matplotlib
matplotlib.use("Agg")  # Required for headless environments

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
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
# SESSION STATE FOR RESULTS
# -----------------------------
if "status_counts" not in st.session_state:
    st.session_state.status_counts = None
if "status_percentages" not in st.session_state:
    st.session_state.status_percentages = None
if "df_processed" not in st.session_state:
    st.session_state.df_processed = None
if "total_jobs" not in st.session_state:
    st.session_state.total_jobs = None
if "completion_percent" not in st.session_state:
    st.session_state.completion_percent = None

# -----------------------------
# PROCESS CSV BUTTON
# -----------------------------
if st.button("Process CSV"):
    if uploaded_file is None:
        st.error("Please upload a CSV file first.")
    else:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.total_jobs = len(df)

            # Find status column
            status_col = None
            for col in df.columns:
                if col.lower() in ["status", "m", "m1"]:
                    status_col = col
                    break

            if status_col is None:
                st.error("No Status column found.")
            else:
                statuses_lower = df[status_col].astype(str).str.lower()

                # Count occurrences (case-insensitive)
                st.session_state.status_counts = {
                    "Open": statuses_lower.str.contains("open").sum(),
                    "Pending": statuses_lower.str.contains("pending").sum(),
                    "Lead Reviewed": statuses_lower.str.contains("lead reviewed").sum(),
                    "Manager Review": statuses_lower.str.contains("manager review").sum(),
                    "QA Reviewed": statuses_lower.str.contains("qa reviewed").sum(),
                }

                # Calculate percentages for each status
                st.session_state.status_percentages = {
                    k: round(v / st.session_state.total_jobs * 100, 1)
                    for k, v in st.session_state.status_counts.items()
                }

                # Calculate overall completion
                completed = sum(
                    st.session_state.status_counts[k]
                    for k in ["Lead Reviewed", "Manager Review", "QA Reviewed"]
                )
                st.session_state.completion_percent = round(completed / st.session_state.total_jobs * 100, 1)

                # Store DataFrame for display and PDF table
                st.session_state.df_processed = pd.DataFrame(
                    {
                        "Status": list(st.session_state.status_counts.keys()),
                        "Count": list(st.session_state.status_counts.values()),
                        "Percentage": list(st.session_state.status_percentages.values()),
                    }
                )

                st.success("CSV processed successfully.")

        except Exception as e:
            st.error(f"Error processing CSV: {e}")

# -----------------------------
# DISPLAY JOB COMPLETION SUMMARY
# -----------------------------
if st.session_state.status_percentages:
    st.subheader("Job Completion Summary")
    st.metric("Overall Completion %", f"{st.session_state.completion_percent}%")
    st.write(f"Total Jobs: {st.session_state.total_jobs}")

# -----------------------------
# DISPLAY BAR GRAPH
# -----------------------------
if st.session_state.status_counts:
    st.subheader("Job Status Breakdown")

    fig, ax = plt.subplots(figsize=(8,5))
    bars = ax.bar(
        st.session_state.status_counts.keys(),
        st.session_state.status_counts.values(),
        color=["#d62728", "#ff7f0e", "#1f77b4", "#1f77b4", "#2ca02c"],  # Open/ Pending red/orange, others green/blue
    )

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)

    ax.set_ylabel("Number of Jobs")
    ax.set_xlabel("Status")
    ax.set_title("Job Status Summary", fontsize=14, fontweight='bold')
    ax.set_ylim(0, max(st.session_state.status_counts.values()) * 1.2)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()

    st.pyplot(fig)

    # -----------------------------
    # DISPLAY TABLE
    # -----------------------------
    st.subheader("Job Status Table")
    st.table(st.session_state.df_processed)

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

            # Overall completion
            elements.append(Paragraph(f"Total Jobs: {st.session_state.total_jobs}", styles["Normal"]))
            elements.append(Paragraph(f"Overall Completion %: {st.session_state.completion_percent}%", styles["Normal"]))
            elements.append(Spacer(1, 12))

            # -----------------------------
            # Add Bar Chart to PDF
            # -----------------------------
            fig, ax = plt.subplots(figsize=(6,4))
            bars = ax.bar(
                st.session_state.status_counts.keys(),
                st.session_state.status_counts.values(),
                color=["#d62728", "#ff7f0e", "#1f77b4", "#1f77b4", "#2ca02c"],
            )
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=10)
            ax.set_ylabel("Number of Jobs")
            ax.set_xlabel("Status")
            ax.set_title("Job Status Summary", fontsize=12, fontweight='bold')
            ax.set_ylim(0, max(st.session_state.status_counts.values()) * 1.2)
            ax.yaxis.grid(True, linestyle='--', alpha=0.7)
            plt.xticks(rotation=30, ha='right')
            plt.tight_layout()

            chart_buffer = BytesIO()
            fig.savefig(chart_buffer, format='PNG', bbox_inches='tight')
            chart_buffer.seek(0)
            elements.append(Image(chart_buffer, width=400, height=250))
            elements.append(Spacer(1, 12))

            # -----------------------------
            # Add Table to PDF
            # -----------------------------
            table_data = [["Status", "Count", "Percentage (%)"]] + st.session_state.df_processed.values.tolist()
            pdf_table = Table(table_data, hAlign='LEFT')
            pdf_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                ('ALIGN',(0,0),(-1,-1),'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('BACKGROUND',(0,1),(-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            elements.append(pdf_table)
            elements.append(Spacer(1, 12))

            # Notes
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
