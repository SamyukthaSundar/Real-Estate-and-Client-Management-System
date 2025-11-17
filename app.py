import streamlit as st
from PIL import Image
from utils.auth import authenticate_user, create_user, reset_password
from frontend.client import client_dashboard
from frontend.agent import agent_dashboard
from frontend.admin import admin_dashboard
import re

# ------------------------------------------------------------
# Email Validation Helper
# ------------------------------------------------------------
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email)


# ------------------------------------------------------------
# Sidebar Menu
# ------------------------------------------------------------
def sidebar_menu():
    st.sidebar.markdown(
        """<div style='text-align:center; padding-bottom:8px;'>
            <h1 style='color:#00b4d8;'>🏙️ UrbanSpaces</h1>
            <hr style='border:1px solid #444;'>
        </div>""",
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        """<h2>Navigation</h2>""", unsafe_allow_html=True
    )
    selected = st.sidebar.radio(
        "",
        ["Login", "Create Account", "Forgot Password"],
    )
    return selected


# ------------------------------------------------------------
# Login Page
# ------------------------------------------------------------
def login_page():
    st.markdown(
        """<style>.main {background-color: #232323;}</style>""",
        unsafe_allow_html=True,
    )
    st.markdown("#")
    col1, col2 = st.columns([1, 2])
    with col2:
        st.markdown("### 🔐 Login")
        username = st.text_input("Email", placeholder="Your email")
        password = st.text_input("Password", type="password", placeholder="Your password")
        login_btn = st.button("Login")

        if login_btn:
            # ✅ Email format validation
            if not is_valid_email(username):
                st.error("❌ Please enter a valid email address (e.g., name@domain.ext).")
                return
            user = authenticate_user(username, password)
            if user:
                st.session_state.user = user
                # Route based on role
                if user["role"] == "Client":
                    st.session_state.page = "client_dashboard"
                elif user["role"] == "Agent":
                    st.session_state.page = "agent_dashboard"
                elif user["role"] == "Admin":
                    st.session_state.page = "admin_dashboard"
            else:
                st.error("❌ Incorrect email or password.")


# ------------------------------------------------------------
# Create Account Page (Clients only)
# ------------------------------------------------------------
def create_account_page():
    st.markdown("### 🧾 Create Client Account")
    st.info("All new users are registered as Clients by default.")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    password = st.text_input("Password", type="password")

    create_btn = st.button("Create Account")

    if create_btn:
        # ✅ Validate email before account creation
        if not is_valid_email(email):
            st.error("❌ Please enter a valid email address (e.g., name@domain.ext).")
            return
        
        # Role automatically defaults to 'Client'
        success = create_user(name, email, phone, password)
        if success:
            st.success("✅ Account created successfully! You can now log in.")
            st.session_state.page = "login"
        else:
            st.error("❌ Account creation failed. Try again.")


# ------------------------------------------------------------
# Forgot Password Page
# ------------------------------------------------------------
def forgot_password_page():
    st.markdown("### 🔑 Forgot Password")
    email = st.text_input("Email")
    new_password = st.text_input("New Password", type="password")
    change_btn = st.button("Change Password")

    if change_btn:
        # ✅ Validate email before password reset
        if not is_valid_email(email):
            st.error("❌ Invalid email format. Please enter a valid email.")
            return
        
        if reset_password(email, new_password):
            st.success("✅ Password changed successfully! Return to login.")
            st.session_state.page = "login"
        else:
            st.error("❌ Error changing password. Check your email.")


# ------------------------------------------------------------
# Main App Logic
# ------------------------------------------------------------
def main():
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.page == "login":
        selected = sidebar_menu()
        if selected == "Login":
            login_page()
        elif selected == "Create Account":
            create_account_page()
        elif selected == "Forgot Password":
            forgot_password_page()

    elif st.session_state.page == "client_dashboard":
        client_dashboard(st.session_state.user)
    elif st.session_state.page == "agent_dashboard":
        agent_dashboard(st.session_state.user)
    elif st.session_state.page == "admin_dashboard":
        admin_dashboard(st.session_state.user)


if __name__ == "__main__":
    main()
