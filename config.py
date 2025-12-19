''' import os

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Normal ranges for medical parameters
NORMAL_RANGES = {
    "Hemoglobin": {"min": 12.0, "max": 17.0, "unit": "g/dL"},
    "RBC": {"min": 4.0, "max": 6.0, "unit": "million/µL"},
    "WBC": {"min": 4000, "max": 11000, "unit": "/µL"},
    "Platelets": {"min": 150000, "max": 400000, "unit": "/µL"},
    "Glucose": {"min": 70, "max": 100, "unit": "mg/dL"},
    "Cholesterol": {"min": 0, "max": 200, "unit": "mg/dL"},
    "Blood Pressure Systolic": {"min": 90, "max": 120, "unit": "mmHg"},
    "Blood Pressure Diastolic": {"min": 60, "max": 80, "unit": "mmHg"},
    "Heart Rate": {"min": 60, "max": 100, "unit": "bpm"},
    "Temperature": {"min": 97.0, "max": 99.0, "unit": "°F"},
}

# Excel columns
EXCEL_COLUMNS = [
    "Date",
    "Report Type",
    "Hemoglobin",
    "RBC",
    "WBC",
    "Platelets",
    "Glucose",
    "Cholesterol",
    "Blood Pressure Systolic",
    "Blood Pressure Diastolic",
    "Heart Rate",
    "Temperature",
    "Notes"
] '''


import os

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Normal ranges for medical parameters
NORMAL_RANGES = {
    # Basic Vitals
    "Hemoglobin": {"min": 12.0, "max": 17.0, "unit": "g/dL"},
    "RBC": {"min": 4.0, "max": 6.0, "unit": "million/µL"},
    "WBC": {"min": 4000, "max": 11000, "unit": "/µL"},
    "Platelets": {"min": 150000, "max": 400000, "unit": "/µL"},
    "Glucose": {"min": 70, "max": 100, "unit": "mg/dL"},
    "Cholesterol": {"min": 0, "max": 200, "unit": "mg/dL"},
    "Blood Pressure Systolic": {"min": 90, "max": 120, "unit": "mmHg"},
    "Blood Pressure Diastolic": {"min": 60, "max": 80, "unit": "mmHg"},
    "Heart Rate": {"min": 60, "max": 100, "unit": "bpm"},
    "Temperature": {"min": 97.0, "max": 99.0, "unit": "°F"},
    
    # Liver Function Test (LFT)
    "Total Bilirubin": {"min": 0.2, "max": 1.2, "unit": "mg/dL"},
    "Conjugated Bilirubin": {"min": 0.0, "max": 0.3, "unit": "mg/dL"},
    "Unconjugated Bilirubin": {"min": 0.2, "max": 0.9, "unit": "mg/dL"},
    "SGOT (AST)": {"min": 5, "max": 40, "unit": "U/L"},
    "SGPT (ALT)": {"min": 5, "max": 40, "unit": "U/L"},
    "Alkaline Phosphatase": {"min": 30, "max": 120, "unit": "U/L"},
    "Total Protein": {"min": 6.0, "max": 8.3, "unit": "g/dL"},
    "Albumin": {"min": 3.5, "max": 5.5, "unit": "g/dL"},
    "Globulin": {"min": 2.0, "max": 3.5, "unit": "g/dL"},
    "A/G Ratio": {"min": 1.0, "max": 2.5, "unit": "ratio"},
    
    # Complete Blood Picture (CBP)
    "PCV/HCT": {"min": 36, "max": 50, "unit": "%"},
    "MCV": {"min": 80, "max": 100, "unit": "fL"},
    "MCH": {"min": 27, "max": 32, "unit": "pg"},
    "MCHC": {"min": 32, "max": 36, "unit": "g/dL"},
    "RDW-CV": {"min": 11.5, "max": 14.5, "unit": "%"},
    "MPV": {"min": 7.5, "max": 11.5, "unit": "fL"},
    
    # Thyroid Test
    "T3 (Triiodothyronine)": {"min": 0.8, "max": 2.0, "unit": "ng/mL"},
    "T4 (Thyroxine)": {"min": 5.0, "max": 12.0, "unit": "µg/dL"},
    "TSH": {"min": 0.4, "max": 4.5, "unit": "µIU/mL"},
    
    # Differential Count and Additional Parameters
    "Neutrophils": {"min": 40, "max": 70, "unit": "%"},
    "Lymphocytes": {"min": 20, "max": 40, "unit": "%"},
    "Monocytes": {"min": 2, "max": 8, "unit": "%"},
    "Eosinophils": {"min": 1, "max": 6, "unit": "%"},
    "Gamma Glutamyl Transferase": {"min": 8, "max": 61, "unit": "U/L"},
}

# Report types
REPORT_TYPES = [
    "Blood Test",
    "Vitals Check",
    "General Checkup",
    "Liver Function Test (LFT)",
    "Complete Blood Picture (CBP)",
    "Thyroid Test",
    "Comprehensive Health Check"
]

# Excel columns - organized by test type
EXCEL_COLUMNS = [
    # Basic Information
    "Date",
    "Report Type",
    "Notes",
    
    # Basic Vitals
    "Hemoglobin",
    "RBC",
    "WBC",
    "Platelets",
    "Glucose",
    "Cholesterol",
    "Blood Pressure Systolic",
    "Blood Pressure Diastolic",
    "Heart Rate",
    "Temperature",
    
    # Liver Function Test
    "Total Bilirubin",
    "Conjugated Bilirubin",
    "Unconjugated Bilirubin",
    "SGOT (AST)",
    "SGPT (ALT)",
    "Alkaline Phosphatase",
    "Total Protein",
    "Albumin",
    "Globulin",
    "A/G Ratio",
    
    # Complete Blood Picture
    "PCV/HCT",
    "MCV",
    "MCH",
    "MCHC",
    "RDW-CV",
    "MPV",
    "Neutrophils",
    "Lymphocytes",
    "Monocytes",
    "Eosinophils",
    
    # Thyroid Test
    "T3 (Triiodothyronine)",
    "T4 (Thyroxine)",
    "TSH",
]

# Test parameter mapping for automatic detection
TEST_PARAMETERS = {
    "Liver Function Test (LFT)": [
        "Total Bilirubin", "Conjugated Bilirubin", "Unconjugated Bilirubin",
        "SGOT (AST)", "SGPT (ALT)", "Alkaline Phosphatase",
        "Total Protein", "Albumin", "Globulin", "A/G Ratio"
    ],
    "Complete Blood Picture (CBP)": [
        "Hemoglobin", "RBC", "WBC", "Platelets",
        "PCV/HCT", "MCV", "MCH", "MCHC", "RDW-CV", "MPV",
        "Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils"
    ],
    "Thyroid Test": [
        "T3 (Triiodothyronine)", "T4 (Thyroxine)", "TSH"
    ],
    "Blood Test": [
        "Hemoglobin", "RBC", "WBC", "Platelets", "Glucose", "Cholesterol"
    ],
    "Vitals Check": [
        "Blood Pressure Systolic", "Blood Pressure Diastolic",
        "Heart Rate", "Temperature"
    ]
}