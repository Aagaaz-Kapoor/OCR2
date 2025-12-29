'''import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import re
from datetime import datetime
import os
from config import EXCEL_COLUMNS, TEST_PARAMETERS

class OCRProcessor:
    def __init__(self):
        """Local Machine Configuration - Add your paths below"""
        print("Environment:", os.name)
        
        # ===========================================
        # ADD YOUR TESSERACT PATH HERE
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        # ===========================================
        
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            print(f"✓ Tesseract configured: {tesseract_path}")
        else:
            print(f"⚠️ Tesseract not found at: {tesseract_path}")
            print("Please update tesseract_path variable with correct path")
        
        # ===========================================
        # ADD YOUR POPPLER PATH HERE
        # ===========================================
        poppler_path = r"C:\poppler-25.12.0\Library\bin"
        if os.path.exists(poppler_path):
            self.poppler_path = poppler_path
            print(f"✓ Poppler configured: {poppler_path}")
        else:
            print(f"⚠️ Poppler not found at: {poppler_path}")
            print("Please update poppler_path variable with correct path")
            self.poppler_path = None
    
    def create_manual_report(self, report_type, patient_info=None):
        """Create a manual report template for manual data entry"""
        # Initialize data structure with all columns
        data = {col: None for col in EXCEL_COLUMNS}
        
        # Set basic info
        data["Date"] = datetime.now().strftime("%Y-%m-%d")
        data["Report Type"] = report_type
        data["Notes"] = "Manual Entry"
        
        # Add patient info if provided
        if patient_info:
            data.update(patient_info)
        
        return data
    
    def extract_text_from_pdf(self, pdf_bytes):
        """Convert PDF to images and extract text using OCR"""
        try:
            if self.poppler_path:
                images = convert_from_bytes(
                    pdf_bytes,
                    poppler_path=self.poppler_path,
                    dpi=300
                )
            else:
                images = convert_from_bytes(
                    pdf_bytes,
                    dpi=300
                )
            
            text = ""
            for i, img in enumerate(images):
                print(f"Processing page {i+1}/{len(images)}...")
                
                page_text = pytesseract.image_to_string(
                    img,
                    lang="eng",
                    config="--psm 6 --oem 3"
                )
                
                text += page_text + "\n\n"
            
            return text
        
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def detect_report_type(self, text):
        """Automatically detect the type of medical report"""
        text_lower = text.lower()
        
        # Check for Ultrasound
        if any(keyword in text_lower for keyword in 
               ['ultrasound', 'sonography', 'usg', 'echotexture', 'mm']):
            return "Ultrasound Report"
        
        # Check for Liver Function Test
        elif any(keyword in text_lower for keyword in 
                 ['liver function', 'lft', 'sgot', 'sgpt', 'bilirubin']):
            return "Liver Function Test (LFT)"
        
        # Check for Complete Blood Picture
        elif any(keyword in text_lower for keyword in 
                 ['complete blood', 'cbc', 'cbp', 'hemoglobin', 'wbc', 'rbc']):
            return "Complete Blood Picture (CBP)"
        
        # Check for Thyroid Test
        elif any(keyword in text_lower for keyword in 
                 ['thyroid', 'tsh', 't3', 't4']):
            return "Thyroid Test"
        
        # Check for Vitals
        elif any(keyword in text_lower for keyword in 
                 ['blood pressure', 'heart rate', 'temperature', 'vitals']):
            return "Vitals Check"
        
        else:
            return "Blood Test"
    
    def extract_patient_info(self, text):
        """Extract patient information from report"""
        patient_info = {
            "Patient Name": None,
            "Patient Age": None,
            "Patient Gender": None
        }
        
        # Extract Patient Name - Improved pattern
        name_patterns = [
            r"Patient Name[:\s]*([A-Za-z\s\-]+)",
            r"Name[:\s]*([A-Za-z\s\-]+)",
            r"Patient[:\s]*([A-Za-z\s\-]+)",
            r"Baby\s+([A-Za-z\s\-]+)",
            r"([A-Z][a-z]+\s+[A-Z][a-z]+)"  # Simple name pattern
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2:  # Filter out very short matches
                    patient_info["Patient Name"] = name
                    break
        
        # Extract Age - Improved pattern
        age_patterns = [
            r"Age[:\s]*([0-9]+[YMD\s]*)",
            r"(\d+)[\s]*(?:years|yrs|year|Y|months|month|M|days|day|D)",
            r"(\d+)[YMD]"
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                patient_info["Patient Age"] = match.group(1).strip()
                break
        
        # Extract Gender
        gender_patterns = [
            r"Gender[:\s]*([A-Za-z]+)",
            r"Sex[:\s]*([A-Za-z]+)",
            r"\b(Male|Female)\b"
        ]
        
        for pattern in gender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                patient_info["Patient Gender"] = match.group(1).strip()
                break
        
        return patient_info
    
    def extract_ultrasound_data(self, text):
        """Extract ultrasound specific data"""
        ultrasound_data = {}
        
        # Extract Liver Size
        liver_pattern = r"Liver.*?(\d+)[\s]*mm"
        liver_match = re.search(liver_pattern, text, re.IGNORECASE)
        if liver_match:
            ultrasound_data["Liver Size"] = float(liver_match.group(1))
        
        # Extract Gall Bladder Status
        gb_keywords = ['normal', 'distended', 'calculi', 'wall thickening']
        for keyword in gb_keywords:
            if keyword in text.lower():
                ultrasound_data["Gall Bladder Status"] = keyword.capitalize()
                break
        
        # Extract Spleen Size
        spleen_pattern = r"Spleen.*?(\d+)[\s]*mm"
        spleen_match = re.search(spleen_pattern, text, re.IGNORECASE)
        if spleen_match:
            ultrasound_data["Spleen Size"] = float(spleen_match.group(1))
        
        # Extract Kidney Sizes
        kidney_pattern = r"kidney.*?(\d+)[\s]*x[\s]*(\d+)[\s]*mm"
        kidney_matches = re.findall(kidney_pattern, text, re.IGNORECASE)
        
        if len(kidney_matches) >= 2:
            ultrasound_data["Right Kidney Size"] = f"{kidney_matches[0][0]} x {kidney_matches[0][1]} mm"
            ultrasound_data["Left Kidney Size"] = f"{kidney_matches[1][0]} x {kidney_matches[1][1]} mm"
        
        # Extract Findings
        findings_pattern = r"Findings[:\s]*(.*?)(?:IMPRESSION|Conclusion|$)"
        findings_match = re.search(findings_pattern, text, re.DOTALL | re.IGNORECASE)
        if findings_match:
            ultrasound_data["Ultrasound Findings"] = findings_match.group(1).strip()[:500]
        
        # Extract Impression
        impression_pattern = r"IMPRESSION[:\s]*(.*?)(?:Dr\.|$)"
        impression_match = re.search(impression_pattern, text, re.DOTALL | re.IGNORECASE)
        if impression_match:
            ultrasound_data["Ultrasound Impression"] = impression_match.group(1).strip()[:500]
        
        return ultrasound_data
    
    def extract_medical_values(self, text):
        """Extract medical values with improved parsing"""
        values = {}
        
        # Improved patterns for medical parameters
        patterns = {
            "Hemoglobin": [r"HEMOGLOBIN.*?([0-9]+\.?[0-9]*)\s*g/dL", r"Hb.*?([0-9]+\.?[0-9]*)"],
            "RBC": [r"RBC.*?([0-9]+\.?[0-9]*)\s*10", r"Red Blood Cells.*?([0-9]+\.?[0-9]*)"],
            "WBC": [r"WBC.*?([0-9]+\.?[0-9]*)\s*10", r"White Blood Cells.*?([0-9]+\.?[0-9]*)"],
            "Platelets": [r"PLATELET.*?([0-9]+\.?[0-9]*)\s*10", r"Platelet Count.*?([0-9]+\.?[0-9]*)"],
            "Glucose": [r"GLUCOSE.*?([0-9]+\.?[0-9]*)\s*mg/dL", r"Blood Sugar.*?([0-9]+\.?[0-9]*)"],
            "Cholesterol": [r"CHOLESTEROL.*?([0-9]+\.?[0-9]*)\s*mg/dL"],
            "Total Bilirubin": [r"TOTAL BILIRUBIN.*?([0-9]+\.?[0-9]*)\s*mg/dL"],
            "Conjugated Bilirubin": [r"CONJUGATED BILIRUBIN.*?([0-9]+\.?[0-9]*)\s*mg/dL"],
            "Unconjugated Bilirubin": [r"UNCONJUGATED BILIRUBIN.*?([0-9]+\.?[0-9]*)\s*mg/dL"],
            "SGOT (AST)": [r"SGOT.*?([0-9]+\.?[0-9]*)\s*U/L", r"AST.*?([0-9]+\.?[0-9]*)\s*U/L"],
            "SGPT (ALT)": [r"SGPT.*?([0-9]+\.?[0-9]*)\s*U/L", r"ALT.*?([0-9]+\.?[0-9]*)\s*U/L"],
            "Alkaline Phosphatase": [r"ALKALINE PHOSPHATASE.*?([0-9]+\.?[0-9]*)\s*U/L"],
            "Total Protein": [r"TOTAL PROTEIN.*?([0-9]+\.?[0-9]*)\s*g/dL", r"PROTEIN.*?([0-9]+\.?[0-9]*)\s*g/dL"],
            "Albumin": [r"ALBUMIN.*?([0-9]+\.?[0-9]*)\s*g/dL"],
            "Globulin": [r"GLOBULIN.*?([0-9]+\.?[0-9]*)\s*g/dL"],
            "A/G Ratio": [r"A/G RATIO.*?([0-9]+\.?[0-9]*)"],
            "PCV/HCT": [r"PCV.*?([0-9]+\.?[0-9]*)\s*%", r"HCT.*?([0-9]+\.?[0-9]*)\s*%"],
            "MCV": [r"MCV.*?([0-9]+\.?[0-9]*)\s*fL"],
            "MCH": [r"MCH.*?([0-9]+\.?[0-9]*)\s*pg"],
            "MCHC": [r"MCHC.*?([0-9]+\.?[0-9]*)\s*g/dL"],
            "RDW-CV": [r"RDW.*?([0-9]+\.?[0-9]*)\s*%"],
            "MPV": [r"MPV.*?([0-9]+\.?[0-9]*)\s*fL"],
            "Neutrophils": [r"NEUTROPHILS.*?([0-9]+\.?[0-9]*)\s*%"],
            "Lymphocytes": [r"LYMPHOCYTES.*?([0-9]+\.?[0-9]*)\s*%"],
            "Monocytes": [r"MONOCYTES.*?([0-9]+\.?[0-9]*)\s*%"],
            "Eosinophils": [r"EOSINOPHILS.*?([0-9]+\.?[0-9]*)\s*%"],
            "T3 (Triiodothyronine)": [r"T3.*?([0-9]+\.?[0-9]*)\s*ng/mL", r"TRIIODOTHYRONINE.*?([0-9]+\.?[0-9]*)"],
            "T4 (Thyroxine)": [r"T4.*?([0-9]+\.?[0-9]*)\s*µg/dL", r"THYROXINE.*?([0-9]+\.?[0-9]*)"],
            "TSH": [r"TSH.*?([0-9]+\.?[0-9]*)\s*µIU/mL", r"THYROID STIMULATING.*?([0-9]+\.?[0-9]*)"],
            "Blood Pressure Systolic": [r"(\d{2,3})/\d{2,3}\s*mmHg", r"BP.*?(\d{2,3})/\d{2,3}"],
            "Blood Pressure Diastolic": [r"\d{2,3}/(\d{2,3})\s*mmHg", r"BP.*?\d{2,3}/(\d{2,3})"],
            "Heart Rate": [r"Heart Rate.*?(\d{2,3})\s*bpm", r"HR.*?(\d{2,3})"],
            "Temperature": [r"Temperature.*?(\d{2,3}\.\d)\s*°F", r"Temp.*?(\d{2,3}\.\d)"]
        }
        
        # Extract each parameter
        for param, param_patterns in patterns.items():
            for pattern in param_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1))
                        values[param] = value
                        break  # Stop after first match
                    except ValueError:
                        continue
        
        # Special handling for blood pressure
        bp_pattern = r"(\d{2,3})/(\d{2,3})"
        bp_matches = re.findall(bp_pattern, text)
        if bp_matches:
            systolic, diastolic = bp_matches[0]
            values["Blood Pressure Systolic"] = float(systolic)
            values["Blood Pressure Diastolic"] = float(diastolic)
        
        return values
    
    def extract_value_with_keywords(self, text, keywords):
        """Extract numerical value associated with keyword variations"""
        text_lower = text.lower()
        
        for keyword in keywords:
            patterns = [
                rf"{keyword}[:\s\-=]*([0-9]+\.?[0-9]*)",
                rf"{keyword}.*?([0-9]+\.?[0-9]*)",
                rf"([0-9]+\.?[0-9]*)\s*{keyword}",
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    try:
                        return float(matches[0])
                    except:
                        continue
        return None
    
    def parse_medical_report(self, text, selected_test_type=None):
        """Parse medical report text and extract all parameters"""
        print("Parsing extracted text...")
        
        # Initialize data structure with all columns
        data = {col: None for col in EXCEL_COLUMNS}
        
        # Extract patient information
        patient_info = self.extract_patient_info(text)
        data.update(patient_info)
        
        # Set basic info
        data["Date"] = datetime.now().strftime("%Y-%m-%d")
        data["Report Type"] = selected_test_type or self.detect_report_type(text)
        data["Notes"] = ""
        
        # Extract all medical values
        medical_values = self.extract_medical_values(text)
        data.update(medical_values)
        
        # Check if it's an ultrasound report
        if data["Report Type"] == "Ultrasound Report":
            ultrasound_data = self.extract_ultrasound_data(text)
            data.update(ultrasound_data)
            return data
        
        # Calculate derived values
        if data["Albumin"] and data["Total Protein"]:
            if not data["Globulin"]:
                data["Globulin"] = round(data["Total Protein"] - data["Albumin"], 2)
            
            if data["Globulin"] and not data["A/G Ratio"] and data["Globulin"] > 0:
                data["A/G Ratio"] = round(data["Albumin"] / data["Globulin"], 2)
        
        return data
    
    def process_pdf_report(self, pdf_bytes, selected_test_type=None):
        """Main method to process PDF and return structured data"""
        text = self.extract_text_from_pdf(pdf_bytes)
        parsed_data = self.parse_medical_report(text, selected_test_type)
        return parsed_data, text
    
    def get_detected_parameters(self, parsed_data):
        """Get list of parameters that were successfully detected"""
        detected = []
        for key, value in parsed_data.items():
            if key not in ["Date", "Report Type", "Notes", "Patient Name", 
                          "Patient Age", "Patient Gender", "Ultrasound Findings", 
                          "Ultrasound Impression"] and value is not None:
                detected.append(key)
        return detected'''
        
        
        
        
        
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import re
from datetime import datetime
import os
import sys
from config import EXCEL_COLUMNS, TEST_PARAMETERS

class OCRProcessor:
    def __init__(self):
        """Configuration for Streamlit Cloud Deployment"""
        print("Environment:", os.name)
        
        # For Streamlit Cloud/Linux environment
        if os.name == 'posix':  # Linux/Unix
            # Tesseract is installed via system packages in Streamlit Cloud
            try:
                # Try to find tesseract in the system path
                pytesseract.pytesseract.tesseract_cmd = 'tesseract'
                print("✓ Tesseract configured for Linux/Streamlit Cloud")
            except Exception as e:
                print(f"⚠️ Tesseract configuration error: {e}")
                # Fallback - try common paths
                common_paths = [
                    '/usr/bin/tesseract',
                    '/usr/local/bin/tesseract',
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        print(f"✓ Tesseract found at: {path}")
                        break
            
            # Poppler will be installed via system packages
            # pdf2image will automatically find it in Linux
            self.poppler_path = None
            print("✓ Poppler configured for system installation")
            
        else:  # Windows (for local development)
            print("Running on Windows (local development)")
            
            # ===========================================
            # WINDOWS LOCAL DEVELOPMENT PATHS
            # ===========================================
            tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            poppler_path = r"C:\poppler-25.12.0\Library\bin"
            
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                print(f"✓ Tesseract configured: {tesseract_path}")
            else:
                print(f"⚠️ Tesseract not found at: {tesseract_path}")
                print("Please install Tesseract OCR for Windows")
            
            if os.path.exists(poppler_path):
                self.poppler_path = poppler_path
                print(f"✓ Poppler configured: {poppler_path}")
            else:
                print(f"⚠️ Poppler not found at: {poppler_path}")
                print("Please install Poppler for Windows")
                self.poppler_path = None
    
    def create_manual_report(self, report_type, patient_info=None):
        """Create a manual report template for manual data entry"""
        # Initialize data structure with all columns
        data = {col: None for col in EXCEL_COLUMNS}
        
        # Set basic info
        data["Date"] = datetime.now().strftime("%Y-%m-%d")
        data["Report Type"] = report_type
        data["Notes"] = "Manual Entry"
        
        # Add patient info if provided
        if patient_info:
            data.update(patient_info)
        
        return data
    
    def extract_text_from_pdf(self, pdf_bytes):
        """Convert PDF to images and extract text using OCR"""
        try:
            # Check if we're in Streamlit Cloud (Linux) environment
            if os.name == 'posix':
                # On Linux/Streamlit Cloud, don't specify poppler_path
                # It will use the system-installed poppler
                images = convert_from_bytes(
                    pdf_bytes,
                    dpi=300
                )
            else:
                # On Windows, use the poppler_path if available
                if self.poppler_path:
                    images = convert_from_bytes(
                        pdf_bytes,
                        poppler_path=self.poppler_path,
                        dpi=300
                    )
                else:
                    images = convert_from_bytes(
                        pdf_bytes,
                        dpi=300
                    )
            
            text = ""
            for i, img in enumerate(images):
                print(f"Processing page {i+1}/{len(images)}...")
                
                # Configure Tesseract for better medical text recognition
                custom_config = r'--oem 3 --psm 6'
                
                page_text = pytesseract.image_to_string(
                    img,
                    lang="eng",
                    config=custom_config
                )
                
                text += page_text + "\n\n"
            
            return text
        
        except Exception as e:
            # Provide more detailed error information
            error_msg = f"Error processing PDF: {str(e)}"
            
            # Check for common issues
            if "tesseract" in str(e).lower():
                error_msg += "\n\nTesseract OCR is not properly installed or configured."
                error_msg += "\nFor Streamlit Cloud, ensure Tesseract is in your packages.txt"
                error_msg += "\nFor local development, install Tesseract and set the correct path."
            
            if "poppler" in str(e).lower():
                error_msg += "\n\nPoppler is not properly installed or configured."
                error_msg += "\nFor Streamlit Cloud, ensure poppler-utils is in your packages.txt"
                error_msg += "\nFor local development, install Poppler and set the correct path."
            
            raise Exception(error_msg)
    
    def detect_report_type(self, text):
        """Automatically detect the type of medical report"""
        text_lower = text.lower()
        
        # Check for Ultrasound
        if any(keyword in text_lower for keyword in 
               ['ultrasound', 'sonography', 'usg', 'echotexture', 'mm']):
            return "Ultrasound Report"
        
        # Check for Liver Function Test
        elif any(keyword in text_lower for keyword in 
                 ['liver function', 'lft', 'sgot', 'sgpt', 'bilirubin']):
            return "Liver Function Test (LFT)"
        
        # Check for Complete Blood Picture
        elif any(keyword in text_lower for keyword in 
                 ['complete blood', 'cbc', 'cbp', 'hemoglobin', 'wbc', 'rbc']):
            return "Complete Blood Picture (CBP)"
        
        # Check for Thyroid Test
        elif any(keyword in text_lower for keyword in 
                 ['thyroid', 'tsh', 't3', 't4']):
            return "Thyroid Test"
        
        # Check for Vitals
        elif any(keyword in text_lower for keyword in 
                 ['blood pressure', 'heart rate', 'temperature', 'vitals']):
            return "Vitals Check"
        
        else:
            return "Blood Test"
    
    def extract_patient_info(self, text):
        """Extract patient information from report"""
        patient_info = {
            "Patient Name": None,
            "Patient Age": None,
            "Patient Gender": None
        }
        
        # Extract Patient Name - Improved pattern
        name_patterns = [
            r"Patient Name[:\s]*([A-Za-z\s\-]+)",
            r"Name[:\s]*([A-Za-z\s\-]+)",
            r"Patient[:\s]*([A-Za-z\s\-]+)",
            r"Baby\s+([A-Za-z\s\-]+)",
            r"([A-Z][a-z]+\s+[A-Z][a-z]+)"  # Simple name pattern
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2:  # Filter out very short matches
                    patient_info["Patient Name"] = name
                    break
        
        # Extract Age - Improved pattern
        age_patterns = [
            r"Age[:\s]*([0-9]+[YMD\s]*)",
            r"(\d+)[\s]*(?:years|yrs|year|Y|months|month|M|days|day|D)",
            r"(\d+)[YMD]"
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                patient_info["Patient Age"] = match.group(1).strip()
                break
        
        # Extract Gender
        gender_patterns = [
            r"Gender[:\s]*([A-Za-z]+)",
            r"Sex[:\s]*([A-Za-z]+)",
            r"\b(Male|Female)\b"
        ]
        
        for pattern in gender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                patient_info["Patient Gender"] = match.group(1).strip()
                break
        
        return patient_info
    
    def extract_ultrasound_data(self, text):
        """Extract ultrasound specific data"""
        ultrasound_data = {}
        
        # Extract Liver Size
        liver_pattern = r"Liver.*?(\d+)[\s]*mm"
        liver_match = re.search(liver_pattern, text, re.IGNORECASE)
        if liver_match:
            ultrasound_data["Liver Size"] = float(liver_match.group(1))
        
        # Extract Gall Bladder Status
        gb_keywords = ['normal', 'distended', 'calculi', 'wall thickening']
        for keyword in gb_keywords:
            if keyword in text.lower():
                ultrasound_data["Gall Bladder Status"] = keyword.capitalize()
                break
        
        # Extract Spleen Size
        spleen_pattern = r"Spleen.*?(\d+)[\s]*mm"
        spleen_match = re.search(spleen_pattern, text, re.IGNORECASE)
        if spleen_match:
            ultrasound_data["Spleen Size"] = float(spleen_match.group(1))
        
        # Extract Kidney Sizes
        kidney_pattern = r"kidney.*?(\d+)[\s]*x[\s]*(\d+)[\s]*mm"
        kidney_matches = re.findall(kidney_pattern, text, re.IGNORECASE)
        
        if len(kidney_matches) >= 2:
            ultrasound_data["Right Kidney Size"] = f"{kidney_matches[0][0]} x {kidney_matches[0][1]} mm"
            ultrasound_data["Left Kidney Size"] = f"{kidney_matches[1][0]} x {kidney_matches[1][1]} mm"
        
        # Extract Findings
        findings_pattern = r"Findings[:\s]*(.*?)(?:IMPRESSION|Conclusion|$)"
        findings_match = re.search(findings_pattern, text, re.DOTALL | re.IGNORECASE)
        if findings_match:
            ultrasound_data["Ultrasound Findings"] = findings_match.group(1).strip()[:500]
        
        # Extract Impression
        impression_pattern = r"IMPRESSION[:\s]*(.*?)(?:Dr\.|$)"
        impression_match = re.search(impression_pattern, text, re.DOTALL | re.IGNORECASE)
        if impression_match:
            ultrasound_data["Ultrasound Impression"] = impression_match.group(1).strip()[:500]
        
        return ultrasound_data
    
    def extract_medical_values(self, text):
        """Extract medical values with improved parsing"""
        values = {}
        
        # Improved patterns for medical parameters
        patterns = {
            "Hemoglobin": [r"HEMOGLOBIN.*?([0-9]+\.?[0-9]*)\s*g/dL", r"Hb.*?([0-9]+\.?[0-9]*)"],
            "RBC": [r"RBC.*?([0-9]+\.?[0-9]*)\s*10", r"Red Blood Cells.*?([0-9]+\.?[0-9]*)"],
            "WBC": [r"WBC.*?([0-9]+\.?[0-9]*)\s*10", r"White Blood Cells.*?([0-9]+\.?[0-9]*)"],
            "Platelets": [r"PLATELET.*?([0-9]+\.?[0-9]*)\s*10", r"Platelet Count.*?([0-9]+\.?[0-9]*)"],
            "Glucose": [r"GLUCOSE.*?([0-9]+\.?[0-9]*)\s*mg/dL", r"Blood Sugar.*?([0-9]+\.?[0-9]*)"],
            "Cholesterol": [r"CHOLESTEROL.*?([0-9]+\.?[0-9]*)\s*mg/dL"],
            "Total Bilirubin": [r"TOTAL BILIRUBIN.*?([0-9]+\.?[0-9]*)\s*mg/dL"],
            "Conjugated Bilirubin": [r"CONJUGATED BILIRUBIN.*?([0-9]+\.?[0-9]*)\s*mg/dL"],
            "Unconjugated Bilirubin": [r"UNCONJUGATED BILIRUBIN.*?([0-9]+\.?[0-9]*)\s*mg/dL"],
            "SGOT (AST)": [r"SGOT.*?([0-9]+\.?[0-9]*)\s*U/L", r"AST.*?([0-9]+\.?[0-9]*)\s*U/L"],
            "SGPT (ALT)": [r"SGPT.*?([0-9]+\.?[0-9]*)\s*U/L", r"ALT.*?([0-9]+\.?[0-9]*)\s*U/L"],
            "Alkaline Phosphatase": [r"ALKALINE PHOSPHATASE.*?([0-9]+\.?[0-9]*)\s*U/L"],
            "Total Protein": [r"TOTAL PROTEIN.*?([0-9]+\.?[0-9]*)\s*g/dL", r"PROTEIN.*?([0-9]+\.?[0-9]*)\s*g/dL"],
            "Albumin": [r"ALBUMIN.*?([0-9]+\.?[0-9]*)\s*g/dL"],
            "Globulin": [r"GLOBULIN.*?([0-9]+\.?[0-9]*)\s*g/dL"],
            "A/G Ratio": [r"A/G RATIO.*?([0-9]+\.?[0-9]*)"],
            "PCV/HCT": [r"PCV.*?([0-9]+\.?[0-9]*)\s*%", r"HCT.*?([0-9]+\.?[0-9]*)\s*%"],
            "MCV": [r"MCV.*?([0-9]+\.?[0-9]*)\s*fL"],
            "MCH": [r"MCH.*?([0-9]+\.?[0-9]*)\s*pg"],
            "MCHC": [r"MCHC.*?([0-9]+\.?[0-9]*)\s*g/dL"],
            "RDW-CV": [r"RDW.*?([0-9]+\.?[0-9]*)\s*%"],
            "MPV": [r"MPV.*?([0-9]+\.?[0-9]*)\s*fL"],
            "Neutrophils": [r"NEUTROPHILS.*?([0-9]+\.?[0-9]*)\s*%"],
            "Lymphocytes": [r"LYMPHOCYTES.*?([0-9]+\.?[0-9]*)\s*%"],
            "Monocytes": [r"MONOCYTES.*?([0-9]+\.?[0-9]*)\s*%"],
            "Eosinophils": [r"EOSINOPHILS.*?([0-9]+\.?[0-9]*)\s*%"],
            "T3 (Triiodothyronine)": [r"T3.*?([0-9]+\.?[0-9]*)\s*ng/mL", r"TRIIODOTHYRONINE.*?([0-9]+\.?[0-9]*)"],
            "T4 (Thyroxine)": [r"T4.*?([0-9]+\.?[0-9]*)\s*µg/dL", r"THYROXINE.*?([0-9]+\.?[0-9]*)"],
            "TSH": [r"TSH.*?([0-9]+\.?[0-9]*)\s*µIU/mL", r"THYROID STIMULATING.*?([0-9]+\.?[0-9]*)"],
            "Blood Pressure Systolic": [r"(\d{2,3})/\d{2,3}\s*mmHg", r"BP.*?(\d{2,3})/\d{2,3}"],
            "Blood Pressure Diastolic": [r"\d{2,3}/(\d{2,3})\s*mmHg", r"BP.*?\d{2,3}/(\d{2,3})"],
            "Heart Rate": [r"Heart Rate.*?(\d{2,3})\s*bpm", r"HR.*?(\d{2,3})"],
            "Temperature": [r"Temperature.*?(\d{2,3}\.\d)\s*°F", r"Temp.*?(\d{2,3}\.\d)"]
        }
        
        # Extract each parameter
        for param, param_patterns in patterns.items():
            for pattern in param_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1))
                        values[param] = value
                        break  # Stop after first match
                    except ValueError:
                        continue
        
        # Special handling for blood pressure
        bp_pattern = r"(\d{2,3})/(\d{2,3})"
        bp_matches = re.findall(bp_pattern, text)
        if bp_matches:
            systolic, diastolic = bp_matches[0]
            values["Blood Pressure Systolic"] = float(systolic)
            values["Blood Pressure Diastolic"] = float(diastolic)
        
        return values
    
    def extract_value_with_keywords(self, text, keywords):
        """Extract numerical value associated with keyword variations"""
        text_lower = text.lower()
        
        for keyword in keywords:
            patterns = [
                rf"{keyword}[:\s\-=]*([0-9]+\.?[0-9]*)",
                rf"{keyword}.*?([0-9]+\.?[0-9]*)",
                rf"([0-9]+\.?[0-9]*)\s*{keyword}",
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    try:
                        return float(matches[0])
                    except:
                        continue
        return None
    
    def parse_medical_report(self, text, selected_test_type=None):
        """Parse medical report text and extract all parameters"""
        print("Parsing extracted text...")
        
        # Initialize data structure with all columns
        data = {col: None for col in EXCEL_COLUMNS}
        
        # Extract patient information
        patient_info = self.extract_patient_info(text)
        data.update(patient_info)
        
        # Set basic info
        data["Date"] = datetime.now().strftime("%Y-%m-%d")
        data["Report Type"] = selected_test_type or self.detect_report_type(text)
        data["Notes"] = ""
        
        # Extract all medical values
        medical_values = self.extract_medical_values(text)
        data.update(medical_values)
        
        # Check if it's an ultrasound report
        if data["Report Type"] == "Ultrasound Report":
            ultrasound_data = self.extract_ultrasound_data(text)
            data.update(ultrasound_data)
            return data
        
        # Calculate derived values
        if data["Albumin"] and data["Total Protein"]:
            if not data["Globulin"]:
                data["Globulin"] = round(data["Total Protein"] - data["Albumin"], 2)
            
            if data["Globulin"] and not data["A/G Ratio"] and data["Globulin"] > 0:
                data["A/G Ratio"] = round(data["Albumin"] / data["Globulin"], 2)
        
        return data
    
    def process_pdf_report(self, pdf_bytes, selected_test_type=None):
        """Main method to process PDF and return structured data"""
        text = self.extract_text_from_pdf(pdf_bytes)
        parsed_data = self.parse_medical_report(text, selected_test_type)
        return parsed_data, text
    
    def get_detected_parameters(self, parsed_data):
        """Get list of parameters that were successfully detected"""
        detected = []
        for key, value in parsed_data.items():
            if key not in ["Date", "Report Type", "Notes", "Patient Name", 
                          "Patient Age", "Patient Gender", "Ultrasound Findings", 
                          "Ultrasound Impression"] and value is not None:
                detected.append(key)
        return detected