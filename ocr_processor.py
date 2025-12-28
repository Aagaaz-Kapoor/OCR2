import pytesseract
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
        
        # Extract Patient Name
        name_patterns = [
            r"Patient Name[:\s]*([A-Za-z\s]+)",
            r"Name[:\s]*([A-Za-z\s]+)",
            r"Patient[:\s]*([A-Za-z\s]+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                patient_info["Patient Name"] = match.group(1).strip()
                break
        
        # Extract Age
        age_patterns = [
            r"Age[:\s]*([0-9]+[YMD\s]*)",
            r"Y[:\s]*([0-9]+[YMD\s]*)",
            r"(\d+)[\s]*(?:years|yrs|year|Y)"
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
            r"Male|Female"
        ]
        
        for pattern in gender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                patient_info["Patient Gender"] = match.group(0).strip()
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
    
    def parse_medical_report(self, text):
        """Parse medical report text and extract all parameters"""
        print("Parsing extracted text...")
        
        # Initialize data structure with all columns
        data = {col: None for col in EXCEL_COLUMNS}
        
        # Extract patient information
        patient_info = self.extract_patient_info(text)
        data.update(patient_info)
        
        # Set basic info
        data["Date"] = datetime.now().strftime("%Y-%m-%d")
        data["Report Type"] = self.detect_report_type(text)
        data["Notes"] = ""
        
        # Check if it's an ultrasound report
        if data["Report Type"] == "Ultrasound Report":
            ultrasound_data = self.extract_ultrasound_data(text)
            data.update(ultrasound_data)
            return data
        
        # Regular medical test parameters
        keyword_map = {
            "Total Bilirubin": ["total bilirubin", "bilirubin.*total"],
            "Conjugated Bilirubin": ["direct bilirubin", "conjugated bilirubin"],
            "Unconjugated Bilirubin": ["indirect bilirubin", "unconjugated bilirubin"],
            "SGOT (AST)": ["sgot", "ast"],
            "SGPT (ALT)": ["sgpt", "alt"],
            "Alkaline Phosphatase": ["alkaline phosphatase", "alp"],
            "Total Protein": ["total protein"],
            "Albumin": ["albumin"],
            "Globulin": ["globulin"],
            "A/G Ratio": ["a/g ratio", "ag ratio"],
            "Hemoglobin": ["hemoglobin", "hb"],
            "RBC": ["rbc"],
            "WBC": ["wbc"],
            "Platelets": ["platelet"],
            "PCV/HCT": ["pcv", "hct", "hematocrit"],
            "MCV": ["mcv"],
            "MCH": ["mch"],
            "MCHC": ["mchc"],
            "RDW-CV": ["rdw"],
            "MPV": ["mpv"],
            "Neutrophils": ["neutrophils"],
            "Lymphocytes": ["lymphocytes"],
            "Monocytes": ["monocytes"],
            "Eosinophils": ["eosinophils"],
            "Glucose": ["glucose", "blood sugar"],
            "Cholesterol": ["cholesterol"],
            "T3 (Triiodothyronine)": ["t3", "triiodothyronine"],
            "T4 (Thyroxine)": ["t4", "thyroxine"],
            "TSH": ["tsh", "thyroid stimulating"]
        }
        
        # Extract values for all parameters
        for param_name, keywords in keyword_map.items():
            value = self.extract_value_with_keywords(text, keywords)
            if value is not None:
                data[param_name] = value
        
        # Extract blood pressure
        bp = re.findall(r"(\d{2,3})/(\d{2,3})", text)
        if bp:
            data["Blood Pressure Systolic"] = float(bp[0][0])
            data["Blood Pressure Diastolic"] = float(bp[0][1])
        
        # Calculate derived values
        if data["Albumin"] and data["Total Protein"]:
            if not data["Globulin"]:
                data["Globulin"] = round(data["Total Protein"] - data["Albumin"], 2)
            
            if data["Globulin"] and not data["A/G Ratio"] and data["Globulin"] > 0:
                data["A/G Ratio"] = round(data["Albumin"] / data["Globulin"], 2)
        
        return data
    
    def process_pdf_report(self, pdf_bytes):
        """Main method to process PDF and return structured data"""
        text = self.extract_text_from_pdf(pdf_bytes)
        parsed_data = self.parse_medical_report(text)
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