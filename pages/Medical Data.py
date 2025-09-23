import streamlit as st
from config.db_connection import get_connection
from utils.ocr import extract_and_store
import tempfile
import os
from pathlib import Path
import glob
from langchain_huggingface import HuggingFaceEndpoint,ChatHuggingFace
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import faiss


def save_pdf(uploaded_file, user_id):
    # Create a directory per user if not exists
    save_dir = f"uploaded_reports/{user_id}"
    os.makedirs(save_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def generate_summary(report_data):
    llm=HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.3",
                        task="text-generation")
    model=ChatHuggingFace(llm=llm)
    summary_prompt = PromptTemplate.from_template("""
    You are a medical assistant AI.

    The following is the raw medical report texts from a user. Summarize the overall findings, trends, or any red flags.
    Provide a clean and professional medical summary.

    Reports:
    {report_data}

    --- Medical Summary ---
    """)
    summary_chain = summary_prompt | model
    summary_response = summary_chain.invoke({"report_data": report_data})
    summary_text = summary_response.content.strip()


def get_medical_data(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_health_profile WHERE user_id = ?", user_id)
    row = cursor.fetchone()
    conn.close()
    return row

def show_uploaded_pdfs(user_id):
    st.subheader("📁 Uploaded Medical Reports")

    user_dir = Path(f"uploaded_reports/{user_id}")
    if user_dir.exists():
        pdf_files = glob.glob(str(user_dir / "*.pdf"))
        
        if not pdf_files:
            st.info("No reports uploaded yet.")
        else:
            for pdf_path in pdf_files:
                file_name = os.path.basename(pdf_path)
                with open(pdf_path, "rb") as f:
                    st.download_button(label=f"📄 {file_name}",
                                       data=f,
                                       file_name=file_name,
                                       mime="application/pdf"
                                       )
    else:
        st.info("No reports uploaded yet.")

def update_medical_data(user_id, weight, height, blood_group, blood_pressure, heart_rate,
                             chronic_diseases, family_history, allergies, medications, diet,
                             water_intake, sleep, smoking, alcohol):
    conn = get_connection()
    cursor = conn.cursor()

    # Update if record exists, else insert
    cursor.execute("SELECT user_id FROM user_health_profile WHERE user_id = ?", user_id)
    if cursor.fetchone():
        cursor.execute("""
            UPDATE user_health_profile SET weight=?, height=?, blood_group= ?,blood_pressure=?, heart_rate=?, chronic_diseases=?,
                       family_history=?,allergies=?,medications=?,diet=?,water_intake=?,sleep=?,smoking=?,alcohol=? 
                       WHERE user_id=?
        """, (weight, height, blood_group, blood_pressure, heart_rate,
                             chronic_diseases, family_history, allergies, medications, diet,
                             water_intake, sleep, smoking, alcohol,user_id))
    else:
        cursor.execute("""
            INSERT INTO user_health_profile (user_id, weight, height, blood_group, blood_pressure, heart_rate,
                             chronic_diseases, family_history, allergies, medications, diet,
                             water_intake, sleep, smoking, alcohol)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?)
        """, (user_id, weight, height, blood_group, blood_pressure, heart_rate,
                             chronic_diseases, family_history, allergies, medications, diet,
                             water_intake, sleep, smoking, alcohol))
    
    conn.commit()
    conn.close()

def medical_data_page():
    st.set_page_config(page_title="Medical Data", page_icon="🏥", layout="wide")
    st.title("🏥 Medical Data")
    if "user_id" not in st.session_state:
        st.warning("⚠️ Please log in to view your medical data.")
        return

    user_id = st.session_state.user_id
    data = get_medical_data(user_id)

    if data and not st.session_state.get("edit_mode"):
        st.subheader("🩺 Your Medical Information")
        labels = [
    "Weight (kg)",
    "Height (cm)",
    "Blood Group",
    "Blood Pressure (e.g., 120/80)",
    "Heart Rate (bpm)",
    "Chronic Diseases",
    "Family History of Illness",
    "Allergies",
    "Current Medications",
    "Diet Preference",
    "Water Intake (liters/day)",
    "Sleep Duration (hours/day)",
    "Do you smoke?",
    "Do you consume alcohol?"
]

        for label, value in zip(labels, data[1:]):
            st.write(f"**{label}:** {value}")
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

        if uploaded_file is not None:
            save_pdf(uploaded_file,user_id)
            st.success(f"✅ Uploaded: {uploaded_file.name}")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                temp_path = tmp_file.name
            extract_and_store(user_id, path=temp_path)
        
        if st.button("Edit Information"):
            st.session_state.edit_mode = True

        show_uploaded_pdfs(user_id)
        return

   
    st.subheader("📝 Update Your Medical Profile")
    weight = st.number_input("Weight (kg)", min_value=0.0, value=data[2] if data else 0.0)
    height = st.number_input("Height (cm)", min_value=0.0, value=data[1] if data else 0.0)
    blood_group = st.text_input("Blood Group", value=data[3] if data else "")
    blood_pressure = st.text_input("Blood Pressure (e.g., 120/80)", value=data[4] if data else "")
    heart_rate = st.number_input("Heart Rate (bpm)", min_value=0, value=data[5] if data else 0)
    chronic_diseases = st.text_area("Chronic Diseases", value=data[6] if data else "")
    family_history = st.text_area("Family History of Illness", value=data[7] if data else "")
    allergies = st.text_area("Allergies", value=data[8] if data else "")
    medications = st.text_area("Current Medications", value=data[9] if data else "")
    diet = st.text_input("Diet Preference", value=data[10] if data else "")
    water_intake = st.number_input("Water Intake (liters/day)", min_value=0, value=data[11] if data else 0)
    sleep = st.number_input("Sleep Duration (hours/day)", min_value=0, value=data[12] if data else 0)
    smoking = st.selectbox("Do you smoke?", ["No", "Yes", "Occasionally"], index=["No", "Yes", "Occasionally"].index(data[13]) if data else 0)
    alcohol = st.selectbox("Do you consume alcohol?", ["No", "Yes", "Occasionally"], index=["No", "Yes", "Occasionally"].index(data[14]) if data else 0)

    if st.button("Save Medical Data"):
        update_medical_data(user_id, weight, height, blood_group, blood_pressure, heart_rate,
                             chronic_diseases, family_history, allergies, medications, diet,
                             water_intake, sleep, smoking, alcohol)
        st.success("✅ Medical data updated successfully.")
        st.session_state.edit_mode = False
    

# Entry point for the Streamlit page
medical_data_page()
