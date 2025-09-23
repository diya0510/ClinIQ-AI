import streamlit as st
import pyodbc
import os
from datetime import datetime
from utils.db_profile import get_user_health_profile, save_user_health_profile
from utils.ocr import extract_and_store
import tempfile
from config.db_connection import get_connection

def save_pdf(uploaded_file, user_id):
    # Create a directory per user if not exists
    save_dir = f"uploaded_reports/{user_id}"
    os.makedirs(save_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path


# Get user data by ID
def get_user_data(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, age, gender, email FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_user_reports(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT report_type, report_date, report_data 
        FROM reports 
        WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


# Main Profile Page
def show_profile():
    if "user_id" not in st.session_state:
        st.warning("You are not logged in. Please log in first.")
        st.stop()
    
    user_id = st.session_state.user_id  # ✅ Get user_id from session
    st.set_page_config(page_title="User Profile", page_icon="👤", layout="wide")
    st.title("👤 User Profile")
    
    # Fetch and show user details
    user = get_user_data(user_id)
    if user:
        st.subheader("📌 Personal Details")
        st.write(f"**Name:** {user[0]}")
        st.write(f"**Age:** {user[1]}")
        st.write(f"**Gender:** {user[2]}")
        st.write(f"**Email:** {user[3]}")
    existing_data = get_user_health_profile(user_id)

    if existing_data:
        st.success("✅ You've already submitted your health profile.")
        st.info("To view your data, go to the **Medical Data** page.")
        return  # Exit early, don’t show the form again

    # Else, show the form
    with st.form("health_form"):
        st.subheader("Please complete your health profile")
        weight = st.number_input("Weight (kg)", min_value=0.0)
        height = st.number_input("Height (cm)", min_value=0.0)
        blood_group = st.text_input("Blood Group")
        blood_pressure = st.text_input("Blood Pressure (e.g., 120/80)")
        heart_rate = st.number_input("Heart Rate (bpm)", min_value=0)
        chronic_diseases = st.text_area("Chronic Diseases")
        family_history = st.text_area("Family History of Illness")
        allergies = st.text_area("Allergies")
        medications = st.text_area("Current Medications")
        diet = st.text_input("Diet Preference")
        water_intake = st.number_input("Water Intake (liters/day)", min_value=0)
        sleep = st.number_input("Sleep Duration (hours/day)", min_value=0)
        smoking = st.selectbox("Do you smoke?", ["No", "Yes", "Occasionally"])
        alcohol = st.selectbox("Do you consume alcohol?", ["No", "Yes", "Occasionally"])
        submit = st.form_submit_button("Submit")

        if submit:
            save_user_health_profile(
                user_id, weight, height, blood_group, blood_pressure,
                heart_rate, chronic_diseases, family_history,
                allergies, medications, diet, water_intake, sleep,
                smoking, alcohol
            )
            st.success("🎉 Health profile submitted successfully!")
            st.rerun()
    # Upload medical report
    st.subheader("📤 Upload Medical Report")
    uploaded_file = st.file_uploader("Choose a file (PDF, JPG, PNG)", type=["pdf", "jpg", "png"])

    if uploaded_file is not None:
        save_pdf(uploaded_file,user_id)
        st.success(f"✅ Uploaded: {uploaded_file.name}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_path = tmp_file.name
        extract_and_store(user_id, path=temp_path)
        
    if st.button("Edit Information"):
        st.session_state.edit_mode = True

    # Show uploaded reports
    st.subheader("🗂 Your Uploaded Reports")
    reports = get_user_reports(user_id)
    if reports:
        for report_type, report_date, report_data in reports:
            st.markdown(f"📁 **{os.path.basename(report_data)}** ({report_type}) — uploaded on {report_date.strftime('%Y-%m-%d %H:%M')}")
    else:
        st.info("No reports uploaded yet.")

show_profile()

