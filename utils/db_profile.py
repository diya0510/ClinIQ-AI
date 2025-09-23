from config.db_connection import get_connection
from dotenv import load_dotenv

def get_user_health_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM user_health_profile WHERE user_id = ?"
    cursor.execute(query, (user_id,))
    data = cursor.fetchone()
    conn.close()
    return data

def save_user_health_profile(user_id, weight, height, blood_group, blood_pressure, heart_rate,
                             chronic_diseases, family_history, allergies, medications, diet,
                             water_intake, sleep, smoking,alcohol):
    conn = get_connection()
    cursor = conn.cursor()

    # Check if record exists
    cursor.execute("SELECT COUNT(*) FROM user_health_profile WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()[0] > 0

    if exists:
        # Update existing record
        query = """
            UPDATE user_health_profile
            SET weight = ?, height = ?, blood_group = ?, blood_pressure = ?, heart_rate = ?,
                chronic_diseases = ?, family_history = ?, allergies = ?, medications = ?,
                diet = ?, water_intake = ?, sleep = ?, smoking = ?, alcohol = ?, last_updated = GETDATE()
            WHERE user_id = ?
        """
        values = (weight, height, blood_group, blood_pressure, heart_rate,
                  chronic_diseases, family_history, allergies, medications,
                  diet, water_intake, sleep, smoking, alcohol, user_id)
    else:
        # Insert new record
        query = """
            INSERT INTO user_health_profile (
                user_id, weight, height, blood_group, blood_pressure, heart_rate,
                chronic_diseases, family_history, allergies, medications, diet,
                water_intake, sleep, smoking, alcohol
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (user_id, weight, height, blood_group, blood_pressure, heart_rate,
                  chronic_diseases, family_history, allergies, medications,
                  diet, water_intake, sleep, smoking, alcohol)

    cursor.execute(query, values)
    conn.commit()
    conn.close()