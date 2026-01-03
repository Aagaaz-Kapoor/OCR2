import streamlit as st
from auth import AuthManager
from ocr_processor import OCRProcessor
from data_manager import TrendAnalyzer, DataManager
from visualizer import Visualizer
from config import NORMAL_RANGES, REPORT_TYPES, TEST_PARAMETERS
import pandas as pd
import os
from datetime import datetime
import plotly.express as px 

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
if "current_report" not in st.session_state:
    st.session_state.current_report = None
if "manual_report" not in st.session_state:
    st.session_state.manual_report = None
if "editing_report" not in st.session_state:
    st.session_state.editing_report = False
if "selected_test_type" not in st.session_state:
    st.session_state.selected_test_type = None
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = None
if "report_saved" not in st.session_state:
    st.session_state.report_saved = False
if "show_all_reports_in_upload" not in st.session_state:
    st.session_state.show_all_reports_in_upload = False

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
    st.session_state.current_report = None
    st.session_state.manual_report = None
    st.session_state.editing_report = False
    st.session_state.selected_test_type = None
    st.session_state.extracted_text = None
    st.session_state.report_saved = False
    st.session_state.show_all_reports_in_upload = False
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
# LONGITUDINAL ANALYSIS PAGE (NEW)
# ----------------------------------
def longitudinal_analysis_page(data_manager):
    """Page for longitudinal analysis and trend tracking"""
    st.title("📈 Longitudinal Medical Analysis")
    
    # Get all reports
    df = data_manager.get_all_reports()
    
    if df.empty:
        st.info("No reports available for analysis. Upload some reports first.")
        return
    
    # Select patient
    patients = df['Patient Name'].unique()
    selected_patient = st.selectbox(
        "Select Patient for Analysis",
        patients,
        key="longitudinal_patient"
    )
    
    if not selected_patient:
        return
    
    # Get patient-specific data
    patient_data = df[df['Patient Name'] == selected_patient]
    
    # Show patient summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reports", len(patient_data))
    with col2:
        st.metric("Test Types", patient_data['Report Type'].nunique())
    with col3:
        try:
            date_range = f"{patient_data['Date'].min()} to {patient_data['Date'].max()}"
            st.metric("Date Range", date_range)
        except:
            st.metric("Date Range", "N/A")
    
    # Initialize trend analyzer
    trend_analyzer = TrendAnalyzer(data_manager)
    
    # Get test type summary
    test_summary = trend_analyzer.get_test_type_summary(selected_patient)
    
    # Display test type cards
    st.subheader("🔬 Test Type Analysis")
    
    for test_type, summary in test_summary.items():
        with st.expander(f"📋 {test_type} ({summary['count']} reports)", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.write("**First Test**")
                st.write(summary['first_date'].strftime('%Y-%m-%d'))
            
            with col2:
                st.write("**Latest Test**")
                st.write(summary['last_date'].strftime('%Y-%m-%d'))
            
            with col3:
                if summary['frequency_days']:
                    st.write("**Avg Frequency**")
                    st.write(f"{summary['frequency_days']:.1f} days")
            
            with col4:
                st.write("**Tracked Parameters**")
                st.write(len(summary['parameters']))
            
            # Show parameter trends for this test type
            if summary['parameters']:
                selected_param = st.selectbox(
                    f"Select parameter to analyze ({test_type})",
                    summary['parameters'],
                    key=f"param_{test_type}"
                )
                
                if selected_param:
                    # Get history
                    history = trend_analyzer.get_parameter_history(
                        selected_patient, test_type, selected_param
                    )
                    
                    if not history.empty:
                        # Create trend chart
                        visualizer = Visualizer()
                        fig = visualizer.create_multi_test_trend_chart(
                            patient_data, selected_param, test_type
                        )
                        
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Show trend analysis
                        from visualizer import AdvancedVisualizer
                        adv_visualizer = AdvancedVisualizer()
                        trend_card = adv_visualizer.create_trend_analysis_card(
                            selected_param, history,
                            NORMAL_RANGES.get(selected_param)
                        )
                        
                        if trend_card:
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric(
                                    "Current Value", 
                                    f"{trend_card['latest_value']:.2f}",
                                    f"{trend_card['change_percent']:.1f}%"
                                )
                            
                            with col2:
                                st.metric(
                                    "Initial Value",
                                    f"{trend_card['first_value']:.2f}"
                                )
                            
                            with col3:
                                st.metric(
                                    "Data Points",
                                    trend_card['data_points']
                                )
                            
                            with col4:
                                st.write("**Status**")
                                st.markdown(
                                    f"<span style='color:{trend_card['color']};font-weight:bold'>"
                                    f"{trend_card['status']}</span>",
                                    unsafe_allow_html=True
                                )
                        
                        # Detect significant changes
                        significant = trend_analyzer.detect_significant_changes(
                            selected_patient, test_type, selected_param, threshold_percent=10
                        )
                        
                        if significant:
                            st.subheader("⚠️ Significant Changes Detected")
                            for change in significant:
                                st.info(
                                    f"**{change['date'].strftime('%Y-%m-%d')}**: "
                                    f"{selected_param} changed by {abs(change['change_percent']):.1f}% "
                                    f"({change['direction']} from {change['from_value']:.2f} to {change['to_value']:.2f})"
                                )
    
    # Comprehensive dashboard
    st.subheader("📊 Comprehensive Trend Dashboard")
    
    # Select test type for comprehensive view
    test_types = patient_data['Report Type'].unique()
    selected_comprehensive_test = st.selectbox(
        "Select test type for comprehensive view",
        test_types,
        key="comprehensive_test"
    )
    
    if selected_comprehensive_test:
        # Get all parameters for this test type
        test_reports = patient_data[patient_data['Report Type'] == selected_comprehensive_test]
        
        # Identify parameters with sufficient data
        trackable_params = []
        for col in test_reports.columns:
            if col not in ['Date', 'Report Type', 'Patient Name', 'Notes', 
                          'Patient Age', 'Patient Gender']:
                non_null = test_reports[col].notna().sum()
                if non_null >= 2:  # Need at least 2 data points for trend
                    trackable_params.append(col)
        
        if trackable_params:
            # Let user select parameters to compare
            selected_params = st.multiselect(
                "Select parameters to compare",
                trackable_params,
                default=trackable_params[:3] if len(trackable_params) >= 3 else trackable_params,
                key="compare_params"
            )
            
            if selected_params:
                # Create comparison matrix
                from visualizer import AdvancedVisualizer
                visualizer = AdvancedVisualizer()
                matrix_fig = visualizer.create_parameter_comparison_matrix(
                    patient_data, selected_comprehensive_test
                )
                
                if matrix_fig:
                    st.plotly_chart(matrix_fig, use_container_width=True)
                
                # Create comprehensive trend chart
                trend_data = test_reports[['Date'] + selected_params].copy()
                # Ensure Date is datetime
                trend_data['Date'] = pd.to_datetime(trend_data['Date'])
                trend_fig = visualizer.create_comprehensive_trend_dashboard(trend_data)
                
                if trend_fig:
                    st.plotly_chart(trend_fig, use_container_width=True)
                
                # Show parameter correlations
                if len(selected_params) >= 2:
                    st.subheader("🔗 Parameter Correlations")
                    
                    # Calculate correlation matrix
                    corr_data = test_reports[selected_params].corr()
                    
                    fig_corr = px.imshow(
                        corr_data,
                        text_auto='.2f',
                        color_continuous_scale='RdBu',
                        title=f"Correlation Matrix - {selected_comprehensive_test}"
                    )
                    
                    st.plotly_chart(fig_corr, use_container_width=True)

# ----------------------------------
# HEALTH TIMELINE PAGE (NEW)
# ----------------------------------
def health_timeline_page(data_manager):
    """Page showing health timeline visualization"""
    st.title("⏳ Health Timeline")
    
    df = data_manager.get_all_reports()
    
    if df.empty:
        st.info("No reports available for timeline.")
        return
    
    # Select patient
    patients = df['Patient Name'].unique()
    selected_patient = st.selectbox(
        "Select Patient",
        patients,
        key="timeline_patient"
    )
    
    if not selected_patient:
        return
    
    # Get patient data
    patient_data = df[df['Patient Name'] == selected_patient].copy()
    patient_data['Date'] = pd.to_datetime(patient_data['Date'], errors='coerce')
    # Remove rows with invalid dates
    patient_data = patient_data[patient_data['Date'].notna()].copy()
    patient_data = patient_data.sort_values('Date', ascending=True)
    
    # Create timeline visualization
    st.subheader("Medical Test Timeline")
    
    # Create timeline using plotly
    from visualizer import AdvancedVisualizer
    visualizer = AdvancedVisualizer()
    timeline_fig = visualizer.create_timeline_visualization(patient_data)
    
    if timeline_fig:
        st.plotly_chart(timeline_fig, use_container_width=True)
    
    # Show chronological report summary
    st.subheader("📋 Chronological Report Summary")
    
    for idx, row in patient_data.iterrows():
        # Format date safely
        try:
            date_str = row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else 'Unknown Date'
        except:
            date_str = str(row['Date']) if pd.notna(row['Date']) else 'Unknown Date'
        
        report_type = row.get('Report Type', 'Unknown Type')
        with st.expander(f"{date_str} - {report_type}", expanded=False):
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.write("**Test Details**")
                st.write(f"Type: {row['Report Type']}")
                if 'Patient Age' in row and pd.notna(row['Patient Age']):
                    st.write(f"Age: {row['Patient Age']}")
                if 'Notes' in row and pd.notna(row['Notes']):
                    st.write(f"Notes: {row['Notes'][:100]}...")
            
            with col2:
                # Show key parameters
                st.write("**Key Parameters**")
                
                # Get parameters with values
                parameters = []
                for col in patient_data.columns:
                    if col not in ['Date', 'Report Type', 'Patient Name', 'Notes', 
                                  'Patient Age', 'Patient Gender', 'Ultrasound Findings', 
                                  'Ultrasound Impression']:
                        if pd.notna(row[col]):
                            parameters.append((col, row[col]))
                
                # Display in grid
                if parameters:
                    cols = st.columns(3)
                    for i, (param, value) in enumerate(parameters[:9]):  # Show first 9
                        with cols[i % 3]:
                            # Check status
                            if param in NORMAL_RANGES:
                                status, color = Visualizer().check_value_status(param, value)
                                st.markdown(
                                    f"<span style='color:{color};font-weight:bold'>{param}:</span> {value}",
                                    unsafe_allow_html=True
                                )
                            else:
                                st.write(f"{param}: {value}")

# ----------------------------------
# MAIN APPLICATION UI
# ----------------------------------
def main_app():
    with st.sidebar:
        # Get current patient name for display
        current_patient = st.session_state.selected_family_member or st.session_state.username
        
        st.title(f"👤 {st.session_state.username}")
        st.markdown("---")
        
        st.subheader(f"👤 Current Profile: {current_patient}")
        st.markdown("---")
        
        st.subheader("👨‍👩‍👧‍👦 Switch Profile")
        
        profiles = [f"👤 {st.session_state.username} (You)"]
        
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
            st.session_state.selected_family_member = None
        elif selected.startswith("👤 " + st.session_state.username):
            st.session_state.selected_patient = st.session_state.username
            st.session_state.selected_family_member = None
        else:
            name = selected.split(" ", 1)[1].split(" (")[0]
            st.session_state.selected_patient = name
            st.session_state.selected_family_member = name
        
        st.info(f"Currently viewing: **{st.session_state.selected_patient}**")
        st.markdown("---")

        page = st.radio(
            "Navigation",
            ["📤 Upload Report", "📈 Longitudinal Analysis", "⏳ Health Timeline", 
             "📊 Dashboard", "📋 All Reports", "👨‍👩‍👧‍👦 Family Profiles", "⚙️ Settings"],
            key="navigation"
        )

        st.markdown("---")
        if st.button("Logout", type="primary", key="logout_button"):
            logout()

    # IMPORTANT: Correct DataManager usage
    data_manager = DataManager(st.session_state.username)
    trend_analyzer = TrendAnalyzer(data_manager)

    ocr = OCRProcessor()
    visualizer = Visualizer()

    if page == "📤 Upload Report":
        upload_page(data_manager, ocr)
    elif page == "📈 Longitudinal Analysis":
        longitudinal_analysis_page(data_manager)
    elif page == "⏳ Health Timeline":
        health_timeline_page(data_manager)
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
    # Check if we're coming from the "View All Reports" button
    if "show_all_reports_in_upload" in st.session_state and st.session_state.show_all_reports_in_upload:
        # Reset the flag
        st.session_state.show_all_reports_in_upload = False
        # Show all reports directly
        all_reports_page(data_manager)
        return
    
    st.title("📤 Upload Medical Report")
    
    # Check if report was just saved
    if st.session_state.get("report_saved"):
        st.success("✅ Report saved successfully!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Upload Another Report"):
                st.session_state.report_saved = False
                st.session_state.editing_report = False
                st.rerun()
        with col2:
            if st.button("📋 View All Reports"):
                st.session_state.report_saved = False
                st.session_state.editing_report = False
                st.session_state.show_all_reports_in_upload = True
                st.rerun()
        return
    
    # Add manual entry option
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Option 1: Upload PDF")
        uploaded = st.file_uploader("Upload PDF Report", type=["pdf"], key="pdf_upload")
        
        if uploaded:
            # Process button - auto-detect test type
            if st.button("🚀 Process PDF", type="primary", key="process_pdf"):
                with st.spinner("Processing OCR and auto-detecting test type..."):
                    try:
                        pdf_bytes = uploaded.read()
                        
                        # Process PDF with auto-detection (pass None for selected_test_type)
                        parsed, text = ocr.process_pdf_report(pdf_bytes, None)
                        
                        st.success("✅ OCR Successful! Test type auto-detected.")
                        
                        # Store extracted text
                        st.session_state.extracted_text = text
                        
                        # Store parsed data in session for editing
                        st.session_state.current_report = parsed
                        st.session_state.editing_report = True
                        st.session_state.selected_test_type = parsed.get("Report Type")
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.info("Ensure Tesseract & Poppler are installed correctly")
    
    with col2:
        st.subheader("Option 2: Manual Entry")
        manual_report_type = st.selectbox(
            "Select Report Type",
            ["Blood Test", "Vitals Check", "General Checkup", "Liver Function Test (LFT)", 
             "Complete Blood Picture (CBP)", "Thyroid Test", "Comprehensive Health Check", 
             "Ultrasound Report"],
            key="manual_report_type"
        )
        
        if st.button("Create Manual Report", key="create_manual"):
            # Get patient info based on selection
            patient_info = {}
            if st.session_state.selected_family_member:
                patient_info["Patient Name"] = st.session_state.selected_family_member
                # Get age/gender from family members if available
                for member_id, member in st.session_state.family_members.items():
                    if member["name"] == st.session_state.selected_family_member:
                        patient_info["Patient Age"] = member.get("age", "")
                        patient_info["Patient Gender"] = member.get("gender", "")
                        break
            else:
                patient_info["Patient Name"] = st.session_state.username
            
            # Create manual report
            manual_report = ocr.create_manual_report(manual_report_type, patient_info)
            st.session_state.manual_report = manual_report
            st.session_state.editing_report = True
            st.rerun()
    
    # Show extracted text if available (for debugging)
    if st.session_state.get("extracted_text") and not st.session_state.get("editing_report"):
        with st.expander("📄 View Extracted Text (Debug)"):
            st.text_area("OCR Extracted Text", st.session_state.extracted_text, height=200)
    
    # Check if we're editing a report
    if "editing_report" in st.session_state and st.session_state.editing_report:
        edit_report_page(data_manager, ocr)
        return

# ----------------------------------
# EDIT REPORT PAGE
# ----------------------------------
def edit_report_page(data_manager, ocr):
    st.title("📝 Review & Save Report")
    
    # Get current report from session
    report = None
    if "current_report" in st.session_state:
        report = st.session_state.current_report
    elif "manual_report" in st.session_state:
        report = st.session_state.manual_report
    
    if not report:
        st.error("No report to edit")
        if st.button("Go Back"):
            st.session_state.editing_report = False
            st.rerun()
        return
    
    # Add "Apply Changes" functionality (OUTSIDE the form)
    if st.session_state.get("extracted_text"):
        st.subheader("🔄 Change Test Type & Re-parse")
        
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            new_test_type = st.selectbox(
                "Select new test type to re-parse:",
                ["Blood Test", "Vitals Check", "General Checkup", "Liver Function Test (LFT)", 
                 "Complete Blood Picture (CBP)", "Thyroid Test", "Comprehensive Health Check", 
                 "Ultrasound Report"],
                index=0,
                key="reparse_test_type"
            )
        
        with col2:
            if st.button("🔄 Apply Changes & Re-parse", type="secondary", key="apply_changes"):
                # Re-parse with new test type
                try:
                    new_parsed = ocr.parse_medical_report(st.session_state.extracted_text, new_test_type)
                    
                    # Keep patient info from current report
                    if report.get("Patient Name"):
                        new_parsed["Patient Name"] = report["Patient Name"]
                    if report.get("Patient Age"):
                        new_parsed["Patient Age"] = report["Patient Age"]
                    if report.get("Patient Gender"):
                        new_parsed["Patient Gender"] = report["Patient Gender"]
                    
                    # Update report with new parsed data
                    for key in new_parsed:
                        report[key] = new_parsed[key]
                    
                    st.session_state.current_report = report
                    st.session_state.selected_test_type = new_test_type
                    st.success(f"✅ Re-parsed as {new_test_type}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error re-parsing: {str(e)}")
        
        with col3:
            if st.button("📄 View OCR Text", key="view_ocr"):
                with st.expander("OCR Extracted Text"):
                    st.text_area("Text", st.session_state.extracted_text, height=300)
    
    # Display detected parameters
    if report:
        detected_params = [k for k, v in report.items() if v is not None and k not in 
                          ["Date", "Report Type", "Patient Name", "Patient Age", 
                           "Patient Gender", "Notes", "Ultrasound Findings", 
                           "Ultrasound Impression"]]
        if detected_params:
            st.info(f"📊 Detected {len(detected_params)} parameters")
    
    # Create form for editing
    with st.form("edit_report_form"):
        st.subheader("Basic Information")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            # Handle date input
            current_date = report.get("Date", datetime.now().strftime("%Y-%m-%d"))
            try:
                date_value = datetime.strptime(str(current_date), "%Y-%m-%d")
            except:
                date_value = datetime.now()
            
            date_input = st.date_input("Date", value=date_value)
        
        with col2:
            report_type_options = [
                "Blood Test", "Vitals Check", "General Checkup", 
                "Liver Function Test (LFT)", "Complete Blood Picture (CBP)", 
                "Thyroid Test", "Comprehensive Health Check", "Ultrasound Report"
            ]
            current_type = report.get("Report Type", "Blood Test")
            current_index = report_type_options.index(current_type) if current_type in report_type_options else 0
            report_type = st.selectbox(
                "Report Type",
                report_type_options,
                index=current_index
            )
        
        with col3:
            # Patient name based on selection
            if st.session_state.selected_family_member:
                patient_name = st.text_input("Patient Name", 
                    value=report.get("Patient Name", st.session_state.selected_family_member))
            else:
                patient_name = st.text_input("Patient Name", 
                    value=report.get("Patient Name", st.session_state.username))
        
        col4, col5 = st.columns(2)
        with col4:
            patient_age = st.text_input("Age", value=report.get("Patient Age", ""))
        
        with col5:
            gender_options = ["Male", "Female", "Other"]
            current_gender = report.get("Patient Gender", "")
            if current_gender not in gender_options:
                current_gender = ""
            patient_gender = st.selectbox("Gender", 
                options=[""] + gender_options,
                index=0 if not current_gender else gender_options.index(current_gender) + 1
            )
        
        notes = st.text_area("Notes", value=report.get("Notes", ""))
        
        st.divider()
        
        # Medical Parameters Section - Organized by test type
        st.subheader("Medical Parameters")
        
        # Get parameters for the selected report type
        relevant_params = []
        
        # Find parameters for this test type
        for test_type, params in TEST_PARAMETERS.items():
            if test_type in report_type:
                relevant_params = params
                break
        
        # If no specific test type found, show common parameters
        if not relevant_params:
            relevant_params = [
                "Hemoglobin", "RBC", "WBC", "Platelets", "Glucose", "Cholesterol",
                "Blood Pressure Systolic", "Blood Pressure Diastolic", 
                "Heart Rate", "Temperature"
            ]
        
        # Add ultrasound parameters if needed
        if report_type == "Ultrasound Report":
            relevant_params = [
                "Liver Size", "Gall Bladder Status", "Spleen Size", 
                "Pancreas Status", "Right Kidney Size", "Left Kidney Size",
                "Urinary Bladder Status"
            ]
        
        # Display parameters in a grid
        st.write(f"**Parameters for {report_type}:**")
        
        # Create columns for parameters
        num_cols = 3
        cols = st.columns(num_cols)
        
        # Dictionary to store updated values
        updated_values = {}
        
        for idx, param in enumerate(relevant_params):
            with cols[idx % num_cols]:
                current_value = report.get(param)
                
                # Format display value
                if current_value is None:
                    display_value = ""
                elif isinstance(current_value, (int, float)):
                    display_value = str(current_value)
                else:
                    display_value = str(current_value)
                
                # Get unit from normal ranges
                unit = NORMAL_RANGES.get(param, {}).get("unit", "")
                label = f"{param} ({unit})" if unit else param
                
                # Create input field
                new_value = st.text_input(
                    label,
                    value=display_value,
                    key=f"edit_{param}_{idx}"
                )
                
                # Store updated value
                updated_values[param] = new_value
        
        # Additional fields for ultrasound
        ultrasound_findings = ""
        ultrasound_impression = ""
        
        if report_type == "Ultrasound Report":
            st.subheader("Ultrasound Details")
            
            col1, col2 = st.columns(2)
            with col1:
                ultrasound_findings = st.text_area(
                    "Findings",
                    value=report.get("Ultrasound Findings", ""),
                    height=100,
                    key="ultrasound_findings"
                )
            
            with col2:
                ultrasound_impression = st.text_area(
                    "Impression",
                    value=report.get("Ultrasound Impression", ""),
                    height=100,
                    key="ultrasound_impression"
                )
        
        # Form buttons (inside form)
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            save_button = st.form_submit_button("💾 Save Report", type="primary")
        
        with col2:
            cancel_button = st.form_submit_button("❌ Cancel")
        
        with col3:
            clear_button = st.form_submit_button("🗑️ Clear Values")
    
    # Handle form submission (OUTSIDE the form)
    if save_button:
        # Update report with form values
        report["Date"] = date_input.strftime("%Y-%m-%d")
        report["Report Type"] = report_type
        report["Patient Name"] = patient_name
        report["Patient Age"] = patient_age
        report["Patient Gender"] = patient_gender if patient_gender else None
        report["Notes"] = notes
        
        # Update medical parameters
        for param, value in updated_values.items():
            if value:
                try:
                    # Try to convert to float
                    report[param] = float(value)
                except ValueError:
                    # Keep as string if not a number
                    report[param] = value
            else:
                report[param] = None
        
        # Update ultrasound fields
        if report_type == "Ultrasound Report":
            report["Ultrasound Findings"] = ultrasound_findings
            report["Ultrasound Impression"] = ultrasound_impression
        
        # Validate required fields
        if not report.get("Patient Name"):
            st.error("Patient Name is required")
        else:
            # Save the report
            success, msg = data_manager.add_report(report)
            if success:
                st.session_state.report_saved = True
                
                # Clear session state
                st.session_state.current_report = None
                st.session_state.manual_report = None
                st.session_state.editing_report = False
                st.session_state.selected_test_type = None
                st.session_state.extracted_text = None
                
                st.rerun()
            else:
                st.error(f"❌ Error saving report: {msg}")
    
    if cancel_button:
        # Clear session state and go back
        st.session_state.current_report = None
        st.session_state.manual_report = None
        st.session_state.editing_report = False
        st.session_state.selected_test_type = None
        st.session_state.extracted_text = None
        st.rerun()
    
    if clear_button:
        # Clear all parameter values but keep basic info
        for key in list(report.keys()):
            if key not in ["Date", "Report Type", "Patient Name", "Patient Age", 
                         "Patient Gender", "Notes", "Ultrasound Findings", 
                         "Ultrasound Impression"]:
                report[key] = None
        st.rerun()
    
    # Add back button (outside form)
    st.divider()
    if st.button("⬅️ Back to Upload"):
        st.session_state.editing_report = False
        st.rerun()

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
    latest = df.iloc[-1] if not df.empty else None
    
    # Check if latest is not None and not empty
    if latest is not None and not latest.empty:
        latest_date = latest.get('Date', 'Unknown')
        report_type = latest.get('Report Type', 'Unknown')
        patient_name = latest.get('Patient Name', 'Unknown')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if isinstance(latest_date, pd.Timestamp):
                st.metric("Date", latest_date.strftime("%Y-%m-%d"))
            else:
                st.metric("Date", str(latest_date))
        with col2:
            st.metric("Report Type", report_type)
        with col3:
            st.metric("Patient", patient_name)
    
    st.subheader("Trend Charts")

    # Get numeric parameters for trend charts
    numeric_params = []
    for col in df.columns:
        if col not in ["Date", "Report Type", "Patient Name", "Notes", 
                      "Patient Age", "Patient Gender", "Ultrasound Findings", 
                      "Ultrasound Impression", "Gall Bladder Status",
                      "Pancreas Status", "Urinary Bladder Status"]:
            # Check if column has numeric data
            try:
                # Try to convert to numeric
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                if numeric_series.notna().any():
                    numeric_params.append(col)
            except:
                continue
    
    # Limit to first 6 parameters to avoid overwhelming
    display_params = numeric_params[:6]
    
    if not display_params:
        st.info("No numeric parameters found for trend charts.")
        return
    
    # Create charts for each parameter
    for param in display_params:
        # Check if we have enough data points
        data_points = pd.to_numeric(df[param], errors='coerce').dropna().count()
        if data_points < 2:
            st.info(f"Need at least 2 data points for {param} trend chart. Currently have {data_points}.")
            continue
        
        # Create the chart
        # Safely get report type
        report_type = None
        if latest is not None and not latest.empty:
            report_type = latest.get("Report Type", None)
        fig = visualizer.create_multi_test_trend_chart(df, param, report_type)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Could not create chart for {param}")

# ----------------------------------
# ALL REPORTS PAGE
# ----------------------------------
def all_reports_page(data_manager):
    st.title("📋 All Reports")
    
    df = data_manager.get_all_reports()
    
    if df.empty:
        st.info("No reports yet. Upload one first.")
        return
    
    # Display dataframe with delete option
    st.dataframe(df, use_container_width=True)
    
    # Delete report section
    st.subheader("Manage Reports")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Reports", key="refresh_reports"):
            st.rerun()
    
    with col2:
        # Download Excel
        if os.path.exists(data_manager.excel_file):
            with open(data_manager.excel_file, "rb") as f:
                st.download_button(
                    "📥 Download Excel",
                    f,
                    file_name=f"medical_reports_{st.session_state.username}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel"
                )
    
    st.divider()
    
    # Delete report by index
    st.subheader("Delete Report")
    if not df.empty:
        # Create a list of report descriptions for selection
        report_options = []
        for idx, row in df.iterrows():
            date_str = str(row.get("Date", "Unknown Date"))
            report_type = row.get("Report Type", "Unknown Type")
            patient = row.get("Patient Name", "Unknown Patient")
            report_options.append(f"#{idx+1}: {date_str} - {report_type} - {patient}")
        
        selected_report = st.selectbox(
            "Select report to delete:",
            report_options,
            key="delete_report_select"
        )
        
        if selected_report and st.button("🗑️ Delete Selected Report", type="secondary"):
            # Extract index from selection
            try:
                report_idx = int(selected_report.split("#")[1].split(":")[0]) - 1
                
                # Confirm deletion
                st.warning(f"Are you sure you want to delete report #{report_idx+1}?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Delete", type="primary"):
                        success, msg = data_manager.delete_report(report_idx)
                        if success:
                            st.success("✅ Report deleted successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {msg}")
                with col2:
                    if st.button("❌ No, Cancel"):
                        st.rerun()
            except Exception as e:
                st.error(f"Error parsing report selection: {str(e)}")

# ----------------------------------
# FAMILY PROFILES PAGE
# ----------------------------------
def family_profiles_page(auth_manager):
    st.title("👨‍👩‍👧‍👦 Family Profiles")
    
    # Add new family member form
    with st.expander("➕ Add New Family Member", expanded=False):
        with st.form("add_family_member"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name", key="family_name")
                age = st.number_input("Age", min_value=0, max_value=150, value=30, key="family_age")
            with col2:
                gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="family_gender")
                relationship = st.selectbox("Relationship", 
                    ["Spouse", "Child", "Parent", "Sibling", "Grandparent", "Other"], 
                    key="family_relationship")
            
            if st.form_submit_button("Add Family Member", type="primary"):
                if name:
                    success, msg = auth_manager.add_family_member(
                        st.session_state.username,
                        name, age, gender, relationship
                    )
                    if success:
                        st.success(f"✅ {msg}")
                        # Refresh family members in session
                        st.session_state.family_members = auth_manager.get_family_members(st.session_state.username)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.warning("Please enter a name")
    
    # Display existing family members
    st.subheader("Family Members")
    members = auth_manager.get_family_members(st.session_state.username)
    
    if not members:
        st.info("No family members added yet. Add one above!")
    else:
        # Display in a nice format
        for member_id, member in members.items():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                
                with col1:
                    st.write(f"**{member['name']}**")
                with col2:
                    st.write(f"Age: {member['age']}")
                with col3:
                    st.write(f"Gender: {member['gender']}")
                with col4:
                    st.write(f"Relationship: {member['relationship']}")
                with col5:
                    if st.button("🗑️", key=f"delete_{member_id}"):
                        # Delete confirmation
                        st.warning(f"Delete {member['name']}?")
                        if st.button(f"✅ Yes, delete {member['name']}", key=f"confirm_delete_{member_id}"):
                            success, msg = auth_manager.delete_family_member(
                                st.session_state.username, member_id
                            )
                            if success:
                                st.success(f"✅ {msg}")
                                # Refresh family members
                                st.session_state.family_members = auth_manager.get_family_members(st.session_state.username)
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                
                st.divider()

# ----------------------------------
# SETTINGS PAGE
# ----------------------------------
def settings_page():
    st.title("⚙️ Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Account Information")
        st.info(f"**Username:** {st.session_state.username}")
        
        # Show user statistics
        data_manager = DataManager(st.session_state.username)
        df = data_manager.get_all_reports()
        
        st.metric("Total Reports", len(df))
        st.metric("Family Members", len(st.session_state.family_members))
        
        if not df.empty:
            try:
                latest_date = df['Date'].max()
                if isinstance(latest_date, pd.Timestamp):
                    st.metric("Latest Report", latest_date.strftime("%Y-%m-%d"))
                else:
                    st.metric("Latest Report", str(latest_date))
            except:
                st.metric("Latest Report", "Unknown")
    
    with col2:
        st.subheader("Data Management")
        
        # Export all data
        if st.button("📊 Export All Data", key="export_all"):
            data_manager = DataManager(st.session_state.username)
            if os.path.exists(data_manager.excel_file):
                with open(data_manager.excel_file, "rb") as f:
                    st.download_button(
                        "📥 Download Complete History",
                        f,
                        file_name=f"{st.session_state.username}_complete_history.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_complete"
                    )
        
        # Clear all data (with confirmation)
        st.divider()
        st.warning("Danger Zone")
        if st.button("🗑️ Clear All Reports", type="secondary", key="clear_all"):
            st.error("This will delete ALL your reports!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Delete Everything", type="primary"):
                    try:
                        data_manager = DataManager(st.session_state.username)
                        # Create empty dataframe
                        from config import EXCEL_COLUMNS
                        df = pd.DataFrame(columns=EXCEL_COLUMNS)
                        df.to_excel(data_manager.excel_file, index=False)
                        st.success("✅ All reports cleared!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            with col2:
                if st.button("❌ Cancel"):
                    st.rerun()
    
    st.divider()
    
    # System information
    st.subheader("System Information")
    st.info(f"Data Directory: {os.path.abspath('data')}")
    
    # Show file sizes
    if os.path.exists("data/users.json"):
        size_kb = os.path.getsize("data/users.json") / 1024
        st.write(f"Users Database: {size_kb:.2f} KB")
    
    data_manager = DataManager(st.session_state.username)
    if os.path.exists(data_manager.excel_file):
        size_mb = os.path.getsize(data_manager.excel_file) / (1024 * 1024)
        st.write(f"Your Reports: {size_mb:.2f} MB")

# ----------------------------------
# RUN APP
# ----------------------------------
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()