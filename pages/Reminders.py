import streamlit as st
import pandas as pd
from datetime import datetime, time
from config.db_connection import get_connection





# Function to get reminders
def fetch_reminders(user_id):
    conn = get_connection()
    query = """
        SELECT reminder_id, type, title, time, repeat_pattern, is_active, created_at
        FROM reminderrs
        WHERE user_id = ?
        ORDER BY created_at DESC
    """
    df = pd.read_sql(query, conn, params=(user_id,))
    conn.close()
    return df

# Function to add reminder
def add_reminder(user_id, r_type, title, r_time, repeat):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reminderrs (user_id, type, title, time, repeat_pattern)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, r_type, title, r_time, repeat))
    conn.commit()
    conn.close()

# Function to toggle status
def toggle_status(reminder_id, current_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE reminderrs SET is_active = ? WHERE reminder_id = ?
    """, (0 if current_status else 1, reminder_id))
    conn.commit()
    conn.close()

# Function to delete a reminder
def delete_reminder(reminder_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE reminder_id = ?", (reminder_id,))
    conn.commit()
    conn.close()

# UI Layout
def main():
 if "user_id" not in st.session_state:
        st.warning("⚠️ Please log in to view your medical data.")
        return

 user_id = st.session_state.user_id
 st.set_page_config(page_title="Reminders", page_icon="📅", layout="wide")
 st.title("🔔 Reminder Management")

# Add new reminder
 st.subheader("➕ Add New Reminder")
 with st.form("reminder_form"):
    r_type = st.selectbox("Reminder Type", ["Medication", "Checkup", "Water", "Exercise", "Custom"])
    title = st.text_input("Title")
    r_time = st.time_input("Reminder Time", value=time(9, 0))
    repeat = st.selectbox("Repeat Pattern", ["Daily", "Weekly", "Monthly", "One-time"])
    submitted = st.form_submit_button("Add Reminder")
    if submitted:
        add_reminder(user_id, r_type, title, r_time, repeat)
        st.success("Reminder added successfully!")

# Show existing reminders
 st.subheader("📋 Existing Reminders")

 reminders_df = fetch_reminders(user_id)

 if reminders_df.empty:
    st.info("No reminders set.")
 else:
    if 'taken_status' not in st.session_state:
     st.session_state.taken_status = {}

 for _, row in reminders_df.iterrows():
    reminder_id = row['reminder_id']
    if reminder_id not in st.session_state.taken_status:
        st.session_state.taken_status[reminder_id] = False

    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
    
    with col1:
        st.markdown(f"**{row['title']}**")
        st.caption(f"{row['type']} • {row['repeat_pattern']} • {row['time']}")
    
    with col2:
        status_label = "✅ Active" if row["is_active"] else "🚫 Inactive"
        if st.button(status_label, key=f"toggle_{reminder_id}"):
            toggle_status(reminder_id, row["is_active"])
            st.experimental_rerun()

    with col3:
        if st.button("🗑️ Delete", key=f"delete_{reminder_id}"):
            delete_reminder(reminder_id)
            st.success("Reminder deleted.")
            st.experimental_rerun()

    with col4:
        taken_label = "☑️ Taken" if st.session_state.taken_status[reminder_id] else "❌ Not Taken"
        if st.button(taken_label, key=f"taken_{reminder_id}"):
            st.session_state.taken_status[reminder_id] = not st.session_state.taken_status[reminder_id]

main()