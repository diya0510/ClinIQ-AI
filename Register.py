import streamlit as st
from utils.auth import register_user, login_user

st.set_page_config(page_title="Medical Dashboard Login", layout="centered")
st.title("🩺 Medical Dashboard Login System")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

    if menu == "Login":
        st.subheader("🔐 Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            success, name, user_id = login_user(email, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.success(f"Welcome, {name} 👋")
                st.switch_page("pages/User Profile.py")
            else:
                st.error("❌ Invalid credentials")

    elif menu == "Register":
        st.subheader("📝 Register")
        name = st.text_input("Full Name")
        age = st.number_input("Age", min_value=0, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Register"):
            if name and age and gender and email and password:
                success = register_user(name, age, gender, email, password)
                if success:
                    st.success("🎉 Registration successful. Please log in.")
                else:
                    st.error("🚫 Registration failed. Email may already exist.")
            else:
                st.warning("Please fill all fields.")
else:
    st.success("✅ You are already logged in.")
    st.switch_page("pages/User Profile.py")
