import streamlit as st
from auth import AuthManager
from ocr_processor import OCRProcessor
from data_manager import DataManager
from visualizer import Visualizer
from config import NORMAL_RANGES, REPORT_TYPES
import pandas as pd
import os
from datetime import datetime

# ----------------------------------
# PAGE CONFIG
# ----------------------------------
st.set_page_config(
    page_title="Medical Report OCR System",
    page_icon="🏥",
    layout="wide"
)

# ----------------------------------
# SESSION STATE INIT
# ----------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None
if "selected_family_member" not in st.session_state:
    st.session_state.selected_family_member = None
if "family_members" not in st.session_state:
    st.session_state.family_members = {}

auth_manager = AuthManager()

# ----------------------------------
# LOGOUT
# ----------------------------------
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.selected_patient = None
    st.session_state.selected_family_member = None
    st.session_state.family_members = {}
    st.rerun()

# ----------------------------------
# LOGIN PAGE
# ----------------------------------
def login_page():
    st.title("🏥 Medical Report OCR System")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    # LOGIN TAB
    with tab1:
        st.subheader("Login to Your Account")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", type="primary", key="login_button"):
            if username and password:
                success, msg = auth_manager.login(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.family_members = auth_manager.get_family_members(username)
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Please enter both username & password")

    # SIGN UP TAB
    with tab2:
        st.subheader("Create Account")
        username = st.text_input("New Username", key="signup_username")
        email = st.text_input("Email", key="signup_email")
        pwd = st.text_input("Password", type="password", key="signup_password")
        confirm = st.text_input("Confirm Password", type="password", key="signup_confirm_password")

        if st.button("Sign Up", type="primary", key="signup_button"):
            if not username or not email or not pwd:
                st.warning("Fill all fields")
            elif pwd != confirm:
                st.error("Passwords do not match")
            elif len(pwd) < 6:
                st.error("Password must be 6+ chars")
            else:
                success, msg = auth_manager.signup(username, pwd, email)
                if success:
                    st.success(msg)
                    st.info("Login with your credentials")
                else:
                    st.error(msg)

# ----------------------------------
# MAIN APPLICATION UI
# ----------------------------------
def main_app():
    with st.sidebar:
        st.title(f"👤 {st.session_state.username}")
        st.markdown("---")

        st.subheader("👨‍👩‍👧‍👦 Select Profile")

        profiles = [f"👤 {st.session_state.username}"]

        if st.session_state.family_members:
            for _, m in st.session_state.family_members.items():
                emoji = (
                    "👨" if m.get("gender", "").lower() == "male"
                    else "👩" if m.get("gender", "").lower() == "female"
                    else "👤"
                )
                profiles.append(f"{emoji} {m['name']} ({m['relationship']})")

        profiles.append("➕ Add New Family Member")

        selected = st.selectbox("Select Profile", profiles, key="profile_selector")

        if selected.startswith("➕"):
            st.session_state.selected_patient = "new_member"
        elif selected.startswith("👤 " + st.session_state.username):
            st.session_state.selected_patient = st.session_state.username
            st.session_state.selected_family_member = None
        else:
            name = selected.split(" ", 1)[1].split(" (")[0]
            st.session_state.selected_patient = name
            st.session_state.selected_family_member = name

        st.markdown("---")

        page = st.radio(
            "Navigation",
            ["📤 Upload Report", "📊 Dashboard", "📋 All Reports", "👨‍👩‍👧‍👦 Family Profiles", "⚙️ Settings"],
            key="navigation"
        )

        st.markdown("---")
        if st.button("Logout", type="primary", key="logout_button"):
            logout()

    # IMPORTANT: Correct DataManager usage
    data_manager = DataManager(st.session_state.username)

    ocr = OCRProcessor()
    visualizer = Visualizer()

    if page == "📤 Upload Report":
        upload_page(data_manager, ocr)
    elif page == "📊 Dashboard":
        dashboard_page(data_manager, visualizer)
    elif page == "📋 All Reports":
        all_reports_page(data_manager)
    elif page == "👨‍👩‍👧‍👦 Family Profiles":
        family_profiles_page(auth_manager)
    elif page == "⚙️ Settings":
        settings_page()

# ----------------------------------
# UPLOAD PAGE
# ----------------------------------
def upload_page(data_manager, ocr):
    st.title("📤 Upload Medical Report")

    uploaded = st.file_uploader("Upload PDF Report", type=["pdf"], key="pdf_upload")

    if uploaded:
        with st.spinner("Processing OCR..."):
            try:
                pdf_bytes = uploaded.read()
                parsed, text = ocr.process_pdf_report(pdf_bytes)

                st.success("OCR Successful!")
                st.json(parsed)

                success, msg = data_manager.add_report(parsed)
                if success:
                    st.success("Report Saved 👍")
                else:
                    st.error(msg)

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Ensure Tesseract & Poppler installed")

# ----------------------------------
# DASHBOARD
# ----------------------------------
def dashboard_page(data_manager, visualizer):
    st.title("📊 Dashboard")

    df = data_manager.get_all_reports()

    if df.empty:
        st.info("No reports yet. Upload one.")
        return

    st.subheader("Latest Report")
    latest = df.iloc[-1]
    st.info(f"📅 {latest.get('Date','')} | 📋 {latest.get('Report Type','')}")

    st.subheader("Trend Charts")

    params = [c for c in df.columns if c not in ["Date", "Report Type", "Patient Name", "Notes"]]

    for param in params[:6]:
        fig = visualizer.create_multi_test_trend_chart(df, param, latest.get("Report Type", "Report"))
        if fig:
            st.plotly_chart(fig, use_container_width=True)

# ----------------------------------
# ALL REPORTS
# ----------------------------------
def all_reports_page(data_manager):
    st.title("📋 All Reports")

    df = data_manager.get_all_reports()

    if df.empty:
        st.info("No reports yet")
        return

    st.dataframe(df, use_container_width=True)

    if os.path.exists(data_manager.excel_file):
        with open(data_manager.excel_file, "rb") as f:
            st.download_button(
                "Download Excel",
                f,
                file_name="reports.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# ----------------------------------
# FAMILY PROFILES
# ----------------------------------
def family_profiles_page(auth_manager):
    st.title("👨‍👩‍👧‍👦 Family Profiles")

    members = auth_manager.get_family_members(st.session_state.username)

    if not members:
        st.info("No family members added")
    else:
        st.json(members)

# ----------------------------------
# SETTINGS
# ----------------------------------
def settings_page():
    st.title("⚙️ Settings")
    st.info(f"Username: {st.session_state.username}")
    st.info(f"Family Count: {len(st.session_state.family_members)}")

# ----------------------------------
# RUN APP
# ----------------------------------
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()
