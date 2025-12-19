''' import streamlit as st
from auth import AuthManager
from ocr_processor import OCRProcessor
from data_manager import DataManager
from visualizer import Visualizer
from config import NORMAL_RANGES
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Medical Report OCR System",
    page_icon="🏥",
    layout="wide"
)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# Initialize managers
auth_manager = AuthManager()

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()

def login_page():
    st.title("🏥 Medical Report OCR System")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login to Your Account")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary"):
            if login_username and login_password:
                success, message = auth_manager.login(login_username, login_password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Please enter both username and password")
    
    with tab2:
        st.subheader("Create New Account")
        signup_username = st.text_input("Username", key="signup_username")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        signup_password_confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm")
        
        if st.button("Sign Up", type="primary"):
            if signup_username and signup_email and signup_password:
                if signup_password != signup_password_confirm:
                    st.error("Passwords do not match")
                elif len(signup_password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    success, message = auth_manager.signup(signup_username, signup_password, signup_email)
                    if success:
                        st.success(message)
                        st.info("Please login with your credentials")
                    else:
                        st.error(message)
            else:
                st.warning("Please fill all fields")

def main_app():
    # Sidebar
    with st.sidebar:
        st.title(f"👤 {st.session_state.username}")
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["📤 Upload Report", "📊 Dashboard", "📋 All Reports", "⚙️ Settings"]
        )
        
        st.markdown("---")
        if st.button("Logout", type="primary"):
            logout()
    
    # Initialize managers for current user
    data_manager = DataManager(st.session_state.username)
    ocr_processor = OCRProcessor()
    visualizer = Visualizer()
    
    # Main content based on selected page
    if page == "📤 Upload Report":
        upload_page(data_manager, ocr_processor)
    elif page == "📊 Dashboard":
        dashboard_page(data_manager, visualizer)
    elif page == "📋 All Reports":
        all_reports_page(data_manager)
    elif page == "⚙️ Settings":
        settings_page()

def upload_page(data_manager, ocr_processor):
    st.title("📤 Upload Medical Report")
    st.markdown("Upload a PDF medical report to automatically extract and store vital information")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file is not None:
        with st.spinner("Processing PDF..."):
            try:
                pdf_bytes = uploaded_file.read()
                parsed_data, extracted_text = ocr_processor.process_pdf_report(pdf_bytes)
                
                st.success("PDF processed successfully!")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("Extracted Data")
                    st.info("Review and edit the extracted information before saving")
                    
                    with st.form("report_form"):
                        parsed_data["Date"] = st.date_input("Date", value=pd.to_datetime(parsed_data["Date"]))
                        parsed_data["Report Type"] = st.selectbox("Report Type", ["Blood Test", "Vitals Check", "General Checkup"])
                        
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            parsed_data["Hemoglobin"] = st.number_input("Hemoglobin (g/dL)", value=parsed_data.get("Hemoglobin"), format="%.2f")
                            parsed_data["RBC"] = st.number_input("RBC (million/µL)", value=parsed_data.get("RBC"), format="%.2f")
                            parsed_data["WBC"] = st.number_input("WBC (/µL)", value=parsed_data.get("WBC"), format="%.0f")
                            parsed_data["Platelets"] = st.number_input("Platelets (/µL)", value=parsed_data.get("Platelets"), format="%.0f")
                            parsed_data["Glucose"] = st.number_input("Glucose (mg/dL)", value=parsed_data.get("Glucose"), format="%.0f")
                            parsed_data["Cholesterol"] = st.number_input("Cholesterol (mg/dL)", value=parsed_data.get("Cholesterol"), format="%.0f")
                        
                        with col_b:
                            parsed_data["Blood Pressure Systolic"] = st.number_input("BP Systolic (mmHg)", value=parsed_data.get("Blood Pressure Systolic"), format="%.0f")
                            parsed_data["Blood Pressure Diastolic"] = st.number_input("BP Diastolic (mmHg)", value=parsed_data.get("Blood Pressure Diastolic"), format="%.0f")
                            parsed_data["Heart Rate"] = st.number_input("Heart Rate (bpm)", value=parsed_data.get("Heart Rate"), format="%.0f")
                            parsed_data["Temperature"] = st.number_input("Temperature (°F)", value=parsed_data.get("Temperature"), format="%.1f")
                        
                        parsed_data["Notes"] = st.text_area("Notes", value=parsed_data.get("Notes", ""))
                        
                        submitted = st.form_submit_button("Save Report", type="primary")
                        
                        if submitted:
                            parsed_data["Date"] = parsed_data["Date"].strftime("%Y-%m-%d")
                            success, message = data_manager.add_report(parsed_data)
                            if success:
                                st.success(message)
                                st.balloons()
                            else:
                                st.error(message)
                
                with col2:
                    st.subheader("Extracted Text")
                    st.text_area("Raw OCR Output", extracted_text, height=400)
            
            except Exception as e:
                st.error(f"Error processing PDF: {str(e)}")
                st.info("Make sure Tesseract OCR is installed on your system")

def dashboard_page(data_manager, visualizer):
    st.title("📊 Health Dashboard")
    
    df = data_manager.get_all_reports()
    
    if df.empty:
        st.info("No reports found. Upload your first medical report to get started!")
        return
    
    # Latest report summary
    st.subheader("Latest Report Summary")
    latest = df.iloc[0].to_dict()
    
    # Status cards
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = [
        ("Hemoglobin", col1),
        ("WBC", col2),
        ("Platelets", col3),
        ("Glucose", col4)
    ]
    
    for param, col in metrics:
        with col:
            value = latest.get(param)
            if value and not pd.isna(value):
                status, color = visualizer.check_value_status(param, value)
                unit = NORMAL_RANGES.get(param, {}).get("unit", "")
                col.metric(
                    label=param,
                    value=f"{value} {unit}",
                    delta=status,
                    delta_color="normal" if status == "Normal" else "inverse"
                )
            else:
                col.metric(label=param, value="N/A")
    
    st.markdown("---")
    
    # Status table
    st.subheader("Current Status Overview")
    status_df = visualizer.create_status_table(latest)
    if not status_df.empty:
        def highlight_status(row):
            if row['Status'] == 'High' or row['Status'] == 'Low':
                return ['background-color: #ffcccc'] * len(row)
            elif row['Status'] == 'Normal':
                return ['background-color: #ccffcc'] * len(row)
            return [''] * len(row)
        
        st.dataframe(
            status_df.style.apply(highlight_status, axis=1),
            use_container_width=True,
            hide_index=True
        )
    
    st.markdown("---")
    
    # Trend charts
    st.subheader("Parameter Trends")
    
    parameters_to_plot = ["Hemoglobin", "WBC", "Platelets", "Glucose"]
    
    for i in range(0, len(parameters_to_plot), 2):
        col1, col2 = st.columns(2)
        
        with col1:
            if i < len(parameters_to_plot):
                fig = visualizer.create_trend_chart(df, parameters_to_plot[i])
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if i + 1 < len(parameters_to_plot):
                fig = visualizer.create_trend_chart(df, parameters_to_plot[i + 1])
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

def all_reports_page(data_manager):
    st.title("📋 All Medical Reports")
    
    df = data_manager.get_all_reports()
    
    if df.empty:
        st.info("No reports found. Upload your first medical report to get started!")
        return
    
    st.subheader(f"Total Reports: {len(df)}")
    
    # Display dataframe
    st.dataframe(
        df.style.format(precision=2),
        use_container_width=True,
        hide_index=True
    )
    
    # Download option
    st.download_button(
        label="📥 Download as Excel",
        data=open(data_manager.excel_file, 'rb').read(),
        file_name=f"{st.session_state.username}_reports.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def settings_page():
    st.title("⚙️ Settings")
    
    st.subheader("Normal Ranges Reference")
    st.markdown("Below are the normal ranges used for health parameter evaluation:")
    
    ranges_data = []
    for param, ranges in NORMAL_RANGES.items():
        ranges_data.append({
            "Parameter": param,
            "Minimum": ranges["min"],
            "Maximum": ranges["max"],
            "Unit": ranges["unit"]
        })
    
    st.dataframe(pd.DataFrame(ranges_data), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("Account Information")
    st.info(f"Username: {st.session_state.username}")
    
    st.markdown("---")
    st.subheader("About")
    st.markdown("""
    This Medical Report OCR System helps you:
    - Upload PDF medical reports
    - Automatically extract vital parameters using OCR
    - Store and track your health data over time
    - Visualize trends and identify abnormal values
    - Export data as Excel files
    """)

# Main execution
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main() '''

import streamlit as st
from auth import AuthManager
from ocr_processor import OCRProcessor
from data_manager import DataManager
from visualizer import Visualizer
from config import NORMAL_RANGES, REPORT_TYPES, TEST_PARAMETERS
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Medical Report OCR System",
    page_icon="🏥",
    layout="wide"
)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# Initialize managers
auth_manager = AuthManager()

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()

def login_page():
    st.title("🏥 Medical Report OCR System")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login to Your Account")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary"):
            if login_username and login_password:
                success, message = auth_manager.login(login_username, login_password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Please enter both username and password")
    
    with tab2:
        st.subheader("Create New Account")
        signup_username = st.text_input("Username", key="signup_username")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        signup_password_confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm")
        
        if st.button("Sign Up", type="primary"):
            if signup_username and signup_email and signup_password:
                if signup_password != signup_password_confirm:
                    st.error("Passwords do not match")
                elif len(signup_password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    success, message = auth_manager.signup(signup_username, signup_password, signup_email)
                    if success:
                        st.success(message)
                        st.info("Please login with your credentials")
                    else:
                        st.error(message)
            else:
                st.warning("Please fill all fields")

def main_app():
    # Sidebar
    with st.sidebar:
        st.title(f"👤 {st.session_state.username}")
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["📤 Upload Report", "📊 Dashboard", "📋 All Reports", "⚙️ Settings"]
        )
        
        st.markdown("---")
        if st.button("Logout", type="primary"):
            logout()
    
    # Initialize managers for current user
    data_manager = DataManager(st.session_state.username)
    ocr_processor = OCRProcessor()
    visualizer = Visualizer()
    
    # Main content based on selected page
    if page == "📤 Upload Report":
        upload_page(data_manager, ocr_processor)
    elif page == "📊 Dashboard":
        dashboard_page(data_manager, visualizer)
    elif page == "📋 All Reports":
        all_reports_page(data_manager)
    elif page == "⚙️ Settings":
        settings_page()

def upload_page(data_manager, ocr_processor):
    st.title("📤 Upload Medical Report")
    st.markdown("Upload a PDF medical report to automatically extract and store vital information")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file is not None:
        with st.spinner("Processing PDF..."):
            try:
                pdf_bytes = uploaded_file.read()
                parsed_data, extracted_text = ocr_processor.process_pdf_report(pdf_bytes)
                
                st.success("PDF processed successfully!")
                
                # Get detected parameters
                detected_params = ocr_processor.get_detected_parameters(parsed_data)
                
                if detected_params:
                    st.info(f"✓ Detected {len(detected_params)} parameters: {', '.join(detected_params[:5])}{'...' if len(detected_params) > 5 else ''}")
                else:
                    st.warning("No parameters detected automatically. Please enter values manually.")
                
                # === DEBUG SECTION ===
                with st.expander("🔍 Debug Information (Click to expand)"):
                    st.write("### 📊 Detection Summary")
                    col_debug1, col_debug2 = st.columns(2)
                    with col_debug1:
                        st.metric("Total Parameters Detected", len(detected_params))
                    with col_debug2:
                        st.metric("OCR Text Length", f"{len(extracted_text):,} chars")
                    
                    st.write("### 📋 Detected Parameters List")
                    if detected_params:
                        # Group parameters by category
                        blood_params = [p for p in detected_params if p in ["Hemoglobin", "RBC", "WBC", "Platelets", "PCV/HCT", "MCV", "MCH", "MCHC", "RDW-CV", "MPV", "Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils"]]
                        liver_params = [p for p in detected_params if p in ["Total Bilirubin", "Conjugated Bilirubin", "Unconjugated Bilirubin", "SGOT (AST)", "SGPT (ALT)", "Alkaline Phosphatase", "Total Protein", "Albumin", "Globulin", "A/G Ratio"]]
                        other_params = [p for p in detected_params if p not in blood_params + liver_params]
                        
                        if blood_params:
                            st.write("**🩸 Blood Parameters:**")
                            st.write(", ".join(blood_params))
                        
                        if liver_params:
                            st.write("**🧪 Liver Function:**")
                            st.write(", ".join(liver_params))
                        
                        if other_params:
                            st.write("**📝 Other Parameters:**")
                            st.write(", ".join(other_params))
                    else:
                        st.write("No parameters detected")
                    
                    st.write("### 📄 All Extracted Values")
                    if detected_params:
                        # Create a table of detected values
                        debug_data = []
                        for param in detected_params:
                            value = parsed_data.get(param)
                            if value is not None:
                                debug_data.append({
                                    "Parameter": param,
                                    "Value": value,
                                    "Type": "Detected"
                                })
                        
                        if debug_data:
                            st.dataframe(pd.DataFrame(debug_data), use_container_width=True, hide_index=True)
                    
                    st.write("### 🔤 Raw OCR Text Sample (First 2000 characters)")
                    st.text_area("OCR Output", extracted_text[:2000], height=300, label_visibility="collapsed")
                    
                    # Option to download full OCR text
                    st.download_button(
                        label="📥 Download Full OCR Text",
                        data=extracted_text.encode('utf-8'),
                        file_name="ocr_full_text.txt",
                        mime="text/plain"
                    )
                # === END DEBUG SECTION ===
                
                # Add test type selector with change button BEFORE the form
                st.markdown("### 🔄 Change Test Type")
                col_select1, col_select2 = st.columns([3, 1])
                
                with col_select1:
                    # Use session state to track selected report type
                    if 'selected_report_type' not in st.session_state:
                        st.session_state.selected_report_type = parsed_data["Report Type"]
                    
                    new_report_type = st.selectbox(
                        "Select Test Type",
                        REPORT_TYPES,
                        index=REPORT_TYPES.index(st.session_state.selected_report_type),
                        key="report_type_selector"
                    )
                
                with col_select2:
                    if st.button("Apply Change", type="primary", use_container_width=True):
                        st.session_state.selected_report_type = new_report_type
                        parsed_data["Report Type"] = new_report_type
                        st.rerun()
                
                # Update parsed_data with selected report type
                parsed_data["Report Type"] = st.session_state.selected_report_type
                
                st.markdown("---")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("Extracted Data")
                    st.info(f"Currently showing: **{parsed_data['Report Type']}** parameters")
                    
                    with st.form("report_form"):
                        # Basic Information
                        st.markdown("### Basic Information")
                        col_basic1, col_basic2 = st.columns(2)
                        with col_basic1:
                            parsed_data["Date"] = st.date_input("Date", value=pd.to_datetime(parsed_data["Date"]))
                        with col_basic2:
                            st.info(f"Report Type: {parsed_data['Report Type']}")
                        
                        st.markdown("---")
                        
                        # Display parameters based on report type
                        if "Liver Function Test" in parsed_data["Report Type"]:
                            st.markdown("### 🧪 Liver Function Parameters")
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                parsed_data["Total Bilirubin"] = st.number_input("Total Bilirubin (mg/dL)", 
                                                                                  value=parsed_data.get("Total Bilirubin"), format="%.2f", key="tb")
                                parsed_data["Conjugated Bilirubin"] = st.number_input("Conjugated Bilirubin (mg/dL)", 
                                                                                       value=parsed_data.get("Conjugated Bilirubin"), format="%.2f", key="cb")
                                parsed_data["Unconjugated Bilirubin"] = st.number_input("Unconjugated Bilirubin (mg/dL)", 
                                                                                         value=parsed_data.get("Unconjugated Bilirubin"), format="%.2f", key="ub")
                                parsed_data["SGOT (AST)"] = st.number_input("SGOT/AST (U/L)", 
                                                                             value=parsed_data.get("SGOT (AST)"), format="%.1f", key="sgot")
                                parsed_data["SGPT (ALT)"] = st.number_input("SGPT/ALT (U/L)", 
                                                                             value=parsed_data.get("SGPT (ALT)"), format="%.1f", key="sgpt")
                            
                            with col_b:
                                parsed_data["Alkaline Phosphatase"] = st.number_input("Alkaline Phosphatase (U/L)", 
                                                                                       value=parsed_data.get("Alkaline Phosphatase"), format="%.1f", key="alp")
                                parsed_data["Total Protein"] = st.number_input("Total Protein (g/dL)", 
                                                                                value=parsed_data.get("Total Protein"), format="%.2f", key="tp")
                                parsed_data["Albumin"] = st.number_input("Albumin (g/dL)", 
                                                                          value=parsed_data.get("Albumin"), format="%.2f", key="alb")
                                parsed_data["Globulin"] = st.number_input("Globulin (g/dL)", 
                                                                           value=parsed_data.get("Globulin"), format="%.2f", key="glob")
                                parsed_data["A/G Ratio"] = st.number_input("A/G Ratio", 
                                                                            value=parsed_data.get("A/G Ratio"), format="%.2f", key="ag")
                        
                        if "Complete Blood Picture" in parsed_data["Report Type"] or "Blood Test" in parsed_data["Report Type"]:
                            st.markdown("### 🩸 Blood Parameters")
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                parsed_data["Hemoglobin"] = st.number_input("Hemoglobin (g/dL)", 
                                                                             value=parsed_data.get("Hemoglobin"), format="%.2f", key="hb")
                                parsed_data["RBC"] = st.number_input("RBC (million/µL)", 
                                                                      value=parsed_data.get("RBC"), format="%.2f", key="rbc")
                                parsed_data["WBC"] = st.number_input("WBC (/µL)", 
                                                                      value=parsed_data.get("WBC"), format="%.0f", key="wbc")
                                parsed_data["Platelets"] = st.number_input("Platelets (/µL)", 
                                                                            value=parsed_data.get("Platelets"), format="%.0f", key="plt")
                            
                            with col_b:
                                parsed_data["PCV/HCT"] = st.number_input("PCV/HCT (%)", 
                                                                          value=parsed_data.get("PCV/HCT"), format="%.1f", key="pcv")
                                parsed_data["MCV"] = st.number_input("MCV (fL)", 
                                                                      value=parsed_data.get("MCV"), format="%.1f", key="mcv")
                                parsed_data["MCH"] = st.number_input("MCH (pg)", 
                                                                      value=parsed_data.get("MCH"), format="%.1f", key="mch")
                                parsed_data["MCHC"] = st.number_input("MCHC (g/dL)", 
                                                                       value=parsed_data.get("MCHC"), format="%.1f", key="mchc")
                            
                            col_c, col_d = st.columns(2)
                            with col_c:
                                parsed_data["RDW-CV"] = st.number_input("RDW-CV (%)", 
                                                                         value=parsed_data.get("RDW-CV"), format="%.1f", key="rdw")
                            with col_d:
                                parsed_data["MPV"] = st.number_input("MPV (fL)", 
                                                                      value=parsed_data.get("MPV"), format="%.1f", key="mpv")
                        
                        if "Thyroid" in parsed_data["Report Type"]:
                            st.markdown("### 🦋 Thyroid Parameters")
                            col_a, col_b, col_c = st.columns(3)
                            
                            with col_a:
                                parsed_data["T3 (Triiodothyronine)"] = st.number_input("T3 (ng/mL)", 
                                                                                         value=parsed_data.get("T3 (Triiodothyronine)"), format="%.2f", key="t3")
                            with col_b:
                                parsed_data["T4 (Thyroxine)"] = st.number_input("T4 (µg/dL)", 
                                                                                  value=parsed_data.get("T4 (Thyroxine)"), format="%.2f", key="t4")
                            with col_c:
                                parsed_data["TSH"] = st.number_input("TSH (µIU/mL)", 
                                                                      value=parsed_data.get("TSH"), format="%.3f", key="tsh")
                        
                        if "Vitals" in parsed_data["Report Type"]:
                            st.markdown("### ❤️ Vital Signs")
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                parsed_data["Blood Pressure Systolic"] = st.number_input("BP Systolic (mmHg)", 
                                                                                          value=parsed_data.get("Blood Pressure Systolic"), format="%.0f", key="bps")
                                parsed_data["Blood Pressure Diastolic"] = st.number_input("BP Diastolic (mmHg)", 
                                                                                           value=parsed_data.get("Blood Pressure Diastolic"), format="%.0f", key="bpd")
                            
                            with col_b:
                                parsed_data["Heart Rate"] = st.number_input("Heart Rate (bpm)", 
                                                                             value=parsed_data.get("Heart Rate"), format="%.0f", key="hr")
                                parsed_data["Temperature"] = st.number_input("Temperature (°F)", 
                                                                              value=parsed_data.get("Temperature"), format="%.1f", key="temp")
                        
                        # Additional parameters for comprehensive check
                        if "Comprehensive" in parsed_data["Report Type"]:
                            col_a, col_b = st.columns(2)
                            with col_a:
                                parsed_data["Glucose"] = st.number_input("Glucose (mg/dL)", 
                                                                          value=parsed_data.get("Glucose"), format="%.0f", key="gluc")
                            with col_b:
                                parsed_data["Cholesterol"] = st.number_input("Cholesterol (mg/dL)", 
                                                                              value=parsed_data.get("Cholesterol"), format="%.0f", key="chol")
                        
                        st.markdown("---")
                        parsed_data["Notes"] = st.text_area("Notes", value=parsed_data.get("Notes", ""), height=100, key="notes")
                        
                        submitted = st.form_submit_button("Save Report", type="primary", use_container_width=True)
                        
                        if submitted:
                            parsed_data["Date"] = parsed_data["Date"].strftime("%Y-%m-%d")
                            # Clear the session state when saving
                            if 'selected_report_type' in st.session_state:
                                del st.session_state.selected_report_type
                            success, message = data_manager.add_report(parsed_data)
                            if success:
                                st.success(message)
                                st.balloons()
                            else:
                                st.error(message)
                
                with col2:
                    st.subheader("Extracted Text")
                    st.text_area("Raw OCR Output", extracted_text, height=600, key="ocr_text")
            
            except Exception as e:
                st.error(f"Error processing PDF: {str(e)}")
                st.info("Make sure Tesseract OCR and Poppler are installed on your system")

def dashboard_page(data_manager, visualizer):
    st.title("📊 Health Dashboard")
    
    df = data_manager.get_all_reports()
    
    if df.empty:
        st.info("No reports found. Upload your first medical report to get started!")
        return
    
    # Latest report summary
    st.subheader("Latest Report Summary")
    latest = df.iloc[0].to_dict()
    
    st.info(f"📅 Report Date: {latest['Date']} | 📋 Type: {latest['Report Type']}")
    
    # Status table
    st.subheader("Current Status Overview")
    status_df = visualizer.create_status_table(latest)
    if not status_df.empty:
        def highlight_status(row):
            if row['Status'] == 'High' or row['Status'] == 'Low':
                return ['background-color: #ffcccc'] * len(row)
            elif row['Status'] == 'Normal':
                return ['background-color: #ccffcc'] * len(row)
            return [''] * len(row)
        
        st.dataframe(
            status_df.style.apply(highlight_status, axis=1),
            use_container_width=True,
            hide_index=True
        )
    
    st.markdown("---")
    
    # Trend charts
    st.subheader("Parameter Trends")
    
    # Get parameters that have data
    available_params = [col for col in df.columns 
                        if col in NORMAL_RANGES and df[col].notna().sum() > 0]
    
    if available_params:
        # Create tabs for different test types
        tabs = st.tabs(["All Parameters", "Blood", "Liver", "Thyroid"])
        
        with tabs[0]:
            for i in range(0, len(available_params), 2):
                col1, col2 = st.columns(2)
                
                with col1:
                    if i < len(available_params):
                        fig = visualizer.create_trend_chart(df, available_params[i])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if i + 1 < len(available_params):
                        fig = visualizer.create_trend_chart(df, available_params[i + 1])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
        
        with tabs[1]:
            blood_params = [p for p in available_params if p in ["Hemoglobin", "RBC", "WBC", "Platelets", "PCV/HCT", "MCV", "MCH", "MCHC"]]
            for idx, param in enumerate(blood_params):
                fig = visualizer.create_trend_chart(df, param)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_blood_{param}_{idx}")
        
        with tabs[2]:
            liver_params = [p for p in available_params if p in TEST_PARAMETERS["Liver Function Test (LFT)"]]
            for idx, param in enumerate(liver_params):
                fig = visualizer.create_trend_chart(df, param)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_liver_{param}_{idx}")
        
        with tabs[3]:
            thyroid_params = [p for p in available_params if p in TEST_PARAMETERS["Thyroid Test"]]
            for idx, param in enumerate(thyroid_params):
                fig = visualizer.create_trend_chart(df, param)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_thyroid_{param}_{idx}")

def all_reports_page(data_manager):
    st.title("📋 All Medical Reports")
    
    df = data_manager.get_all_reports()
    
    if df.empty:
        st.info("No reports found. Upload your first medical report to get started!")
        return
    
    st.subheader(f"Total Reports: {len(df)}")
    
    # Filter by report type
    report_types = df['Report Type'].dropna().unique().tolist()
    selected_type = st.selectbox("Filter by Report Type", ["All"] + report_types)
    
    if selected_type != "All":
        df_display = df[df['Report Type'] == selected_type]
    else:
        df_display = df
    
    # Display dataframe
    st.dataframe(
        df_display.style.format(precision=2),
        use_container_width=True,
        hide_index=True
    )
    
    # Download option
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download All Reports (Excel)",
            data=open(data_manager.excel_file, 'rb').read(),
            file_name=f"{st.session_state.username}_all_reports.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col2:
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered Reports (CSV)",
            data=csv,
            file_name=f"{st.session_state.username}_filtered_reports.csv",
            mime="text/csv"
        )

def settings_page():
    st.title("⚙️ Settings")
    
    st.subheader("Normal Ranges Reference")
    st.markdown("Below are the normal ranges used for health parameter evaluation:")
    
    # Organize by category
    tabs = st.tabs(["Blood Parameters", "Liver Function", "Thyroid", "Vitals"])
    
    with tabs[0]:
        blood_params = {k: v for k, v in NORMAL_RANGES.items() 
                        if k in ["Hemoglobin", "RBC", "WBC", "Platelets", "PCV/HCT", "MCV", "MCH", "MCHC", "RDW-CV", "MPV"]}
        ranges_data = []
        for param, ranges in blood_params.items():
            ranges_data.append({
                "Parameter": param,
                "Minimum": ranges["min"],
                "Maximum": ranges["max"],
                "Unit": ranges["unit"]
            })
        st.dataframe(pd.DataFrame(ranges_data), use_container_width=True, hide_index=True)
    
    with tabs[1]:
        liver_params = {k: v for k, v in NORMAL_RANGES.items() 
                        if k in TEST_PARAMETERS["Liver Function Test (LFT)"]}
        ranges_data = []
        for param, ranges in liver_params.items():
            ranges_data.append({
                "Parameter": param,
                "Minimum": ranges["min"],
                "Maximum": ranges["max"],
                "Unit": ranges["unit"]
            })
        st.dataframe(pd.DataFrame(ranges_data), use_container_width=True, hide_index=True)
    
    with tabs[2]:
        thyroid_params = {k: v for k, v in NORMAL_RANGES.items() 
                          if k in TEST_PARAMETERS["Thyroid Test"]}
        ranges_data = []
        for param, ranges in thyroid_params.items():
            ranges_data.append({
                "Parameter": param,
                "Minimum": ranges["min"],
                "Maximum": ranges["max"],
                "Unit": ranges["unit"]
            })
        st.dataframe(pd.DataFrame(ranges_data), use_container_width=True, hide_index=True)
    
    with tabs[3]:
        vital_params = {k: v for k, v in NORMAL_RANGES.items() 
                        if k in ["Blood Pressure Systolic", "Blood Pressure Diastolic", "Heart Rate", "Temperature", "Glucose", "Cholesterol"]}
        ranges_data = []
        for param, ranges in vital_params.items():
            ranges_data.append({
                "Parameter": param,
                "Minimum": ranges["min"],
                "Maximum": ranges["max"],
                "Unit": ranges["unit"]
            })
        st.dataframe(pd.DataFrame(ranges_data), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("Account Information")
    st.info(f"Username: {st.session_state.username}")
    
    st.markdown("---")
    st.subheader("About")
    st.markdown("""
    This Medical Report OCR System helps you:
    - Upload PDF medical reports (Blood Test, LFT, CBP, Thyroid Test, etc.)
    - Automatically extract vital parameters using OCR
    - Store and track your health data over time
    - Visualize trends and identify abnormal values
    - Export data as Excel or CSV files
    
    **Supported Tests:**
    - Complete Blood Picture (CBP)
    - Liver Function Test (LFT)
    - Thyroid Function Test
    - Basic Blood Tests
    - Vital Signs
    """)

# Main execution
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
