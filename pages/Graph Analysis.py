import streamlit as st
import pandas as pd
import plotly.express as px
from config.db_connection import get_connection  # adjust this if your import path differs


REPORT_TYPE_MAPPING = {
    "LIVER FUNCTION TEST": "LFT",
    "LIVER FUNCTION TEST (LFT)": "LFT",
    "LFT": "LFT",
    "COMPLETE BLOOD COUNT": "CBC",
    "CBC": "CBC",
    "KIDNEY FUNCTION TEST": "KFT",
    "KFT": "KFT",
    # Add more as needed
}


def get_user_reports(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Make sure spelling matches your schema!
        cursor.execute("""
            SELECT r.report_type,
                   r.report_date,
                   rd.parameter_name,
                   rd.paramter_value,       
                   rd.unit,
                   rd.low_range,
                   rd.high_range
            FROM reports r
            JOIN report_parameters rd ON r.report_id = rd.report_id
            WHERE r.user_id = ?
        """, (user_id,))
        
        rows = cursor.fetchall()

        col_names = [desc[0] for desc in cursor.description]

        rows_fixed = [list(row) for row in rows]
        
        


        if rows:
            df = pd.DataFrame(rows_fixed, columns=col_names)
            st.success("Report data fetched successfully.")
            return df
        else:
            st.warning("No report records found for this user.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return pd.DataFrame()

def show_report_trends():
    if "user_id" not in st.session_state:
        st.warning("⚠️ Please log in to view your medical data.")
        return
    st.set_page_config(page_title="Graph Analysis", page_icon="📈", layout="wide")
    user_id = st.session_state.user_id
    st.title("📈 Health Report Trends")

    df = get_user_reports(user_id)

    if df.empty:
        st.warning("No reports uploaded yet.")
        return
    df["report_type"] = df["report_type"].str.strip().str.upper()
    df["report_type"] = df["report_type"].replace(REPORT_TYPE_MAPPING)



    report_types = df["report_type"].unique()

    for report_type in report_types:
        st.subheader(f"🩺 {report_type} Report")

        rpt_df = df[df["report_type"] == report_type]

        fig = px.line(
            rpt_df,
            x="report_date",
            y="paramter_value",       # <-- schema spelling!
            color="parameter_name",
            markers=True,
            labels={
                "report_date": "Report Date",
                "paramter_value": "Value",    # <-- schema spelling!
                "parameter_name": "Parameter"
            },
            title=f"{report_type} Parameters Over Time"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Highlight abnormal values
        for param in rpt_df["parameter_name"].unique():
            abnormal_values = rpt_df[
                (rpt_df["parameter_name"] == param) &
                (
                    (rpt_df["paramter_value"] < rpt_df["low_range"]) |
                    (rpt_df["paramter_value"] > rpt_df["high_range"])
                )
            ]
            if not abnormal_values.empty:
                st.warning(
                    f"⚠️ {param} has abnormal values on: "
                    + ", ".join(abnormal_values["report_date"].astype(str).tolist())
                )

# Entry point for running the app
show_report_trends()
