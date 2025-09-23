from passlib.hash import bcrypt
from config.db_connection import get_connection

def register_user(name, age, gender, email, password):
    conn = get_connection()
    cursor = conn.cursor()

    password_hash = bcrypt.hash(password)

    try:
        cursor.execute(
            "INSERT INTO users (name, age, gender, email, password_hash) VALUES (?, ?, ?, ?, ?)",
            (name, age, gender, email, password_hash)
        )
        conn.commit()
        return True
    except Exception as e:
        print("Registration error:", e)
        return False
    finally:
        conn.close()

def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash, name FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()

    if result and bcrypt.verify(password, result[1]):
        return True, result[2], result[0]  # name, user_id
    
    return False, None, None 
