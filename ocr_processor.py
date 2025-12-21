''' import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import re
from datetime import datetime
import os
from config import EXCEL_COLUMNS, TEST_PARAMETERS

class OCRProcessor:
    def __init__(self):
        # Set tesseract path on Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Set poppler path
        self.poppler_path = r'C:\poppler-25.12.0\Library\bin'
        
        # Verify paths exist
        if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
            print(f"⚠️ WARNING: Tesseract not found at: {pytesseract.pytesseract.tesseract_cmd}")
        
        if not os.path.exists(self.poppler_path):
            print(f"⚠️ WARNING: Poppler not found at: {self.poppler_path}")
            self.poppler_path = None
    
    def extract_text_from_pdf(self, pdf_bytes):
        """Convert PDF to images and extract text using OCR"""
        try:
            if self.poppler_path:
                images = convert_from_bytes(
                    pdf_bytes, 
                    poppler_path=self.poppler_path,
                    dpi=400,  # Increased DPI for better quality
                    fmt='jpeg',
                    grayscale=True  # Better for text extraction
                )
            else:
                raise Exception(
                    "Poppler not found. Please install Poppler and update the path in ocr_processor.py"
                )
            
            text = ""
            for i, img in enumerate(images):
                print(f"Processing page {i+1}/{len(images)}...")
                # Use different OCR configurations
                page_text = pytesseract.image_to_string(
                    img, 
                    lang='eng',
                    config='--psm 6 --oem 3'  # Assume uniform block of text
                )
                text += page_text
                text += "\n\n"
                
                # Save image for debugging
                img.save(f"debug_page_{i+1}.jpg")
                print(f"Saved debug_page_{i+1}.jpg")
            
            # Save extracted text to file
            with open("debug_ocr_output.txt", "w", encoding="utf-8") as f:
                f.write(text)
            
            return text
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def detect_report_type(self, text):
        """Automatically detect the type of medical report"""
        text_lower = text.lower()
        
        print(f"DEBUG: Text sample for detection: {text_lower[:500]}")
        
        # Check for specific test indicators
        if any(keyword in text_lower for keyword in ['liver function', 'lft', 'sgot', 'sgpt', 'bilirubin']):
            print("DEBUG: Detected Liver Function Test")
            return "Liver Function Test (LFT)"
        elif any(keyword in text_lower for keyword in ['complete blood', 'cbc', 'cbp', 'mcv', 'mch', 'mchc', 'hemoglobin', 'rbc', 'wbc']):
            print("DEBUG: Detected Complete Blood Picture")
            return "Complete Blood Picture (CBP)"
        elif any(keyword in text_lower for keyword in ['thyroid', 'tsh', 't3', 't4', 'triiodothyronine', 'thyroxine']):
            return "Thyroid Test"
        elif any(keyword in text_lower for keyword in ['blood pressure', 'heart rate', 'temperature', 'vitals']):
            return "Vitals Check"
        else:
            return "Blood Test"
    
    def extract_value_with_keywords(self, text, keywords, allow_decimal=True):
        """Extract numerical value associated with multiple keyword variations"""
        text_lower = text.lower()
        
        for keyword in keywords:
            # More flexible pattern matching
            patterns = [
                rf"{keyword}[:\s\-=]*([0-9]+\.?[0-9]*)\s*[mg/dlµl%]?",
                rf"{keyword}.*?([0-9]+\.?[0-9]*)\s*[mg/dlµl%]?",
                rf"([0-9]+\.?[0-9]*)\s*[mg/dlµl%]?\s*{keyword}",
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    try:
                        value = float(matches[0])
                        print(f"DEBUG: Found {keyword} = {value}")
                        return value
                    except:
                        continue
        return None
    
    def parse_medical_report(self, text):
        """Parse medical report text and extract all parameters"""
        print("=" * 80)
        print("DEBUG: Starting parse_medical_report")
        print(f"DEBUG: Text length: {len(text)} chars")
        print(f"DEBUG: First 1000 chars: {text[:1000]}")
        print("=" * 80)
        
        # Initialize data structure with all columns
        data = {col: None for col in EXCEL_COLUMNS}
        
        # Set basic info
        data["Date"] = datetime.now().strftime("%Y-%m-%d")
        data["Report Type"] = self.detect_report_type(text)
        data["Notes"] = ""
        
        # Enhanced keyword mapping with better patterns
        keyword_map = {
            # Liver Function Test
            "Total Bilirubin": ["total bilirubin", "bilirubin.*total", "t\.?\s*bilirubin"],
            "Conjugated Bilirubin": ["conjugated bilirubin", "direct bilirubin", "d\.?\s*bilirubin"],
            "Unconjugated Bilirubin": ["unconjugated bilirubin", "indirect bilirubin", "i\.?\s*bilirubin"],
            "SGOT (AST)": ["sgot", "ast", "aspartate", "sgot.*ast", "ast.*sgot"],
            "SGPT (ALT)": ["sgpt", "alt", "alanine", "sgpt.*alt", "alt.*sgpt"],
            "Alkaline Phosphatase": ["alkaline phosphatase", "alp", "alk\.?\s*phosphatase"],
            "Total Protein": ["total protein", "protein.*total", "serum protein"],
            "Albumin": ["albumin", "serum albumin"],
            "Globulin": ["globulin", "serum globulin"],
            "A/G Ratio": ["a/g ratio", "a:g ratio", "albumin.*globulin", "ag ratio"],
            
            # Complete Blood Picture
            "Hemoglobin": ["hemoglobin", "hb", "haemoglobin"],
            "RBC": ["rbc", "red blood", "rbc count", "red cell"],
            "WBC": ["wbc", "white blood", "wbc count", "leucocyte", "leukocyte"],
            "Platelets": ["platelet", "platelets", "platelet count"],
            "PCV/HCT": ["pcv", "hct", "hematocrit", "haematocrit", "packed cell"],
            "MCV": ["mcv", "mean corpuscular volume"],
            "MCH": ["mch", "mean corpuscular hemoglobin"],
            "MCHC": ["mchc", "mean corpuscular hemoglobin concentration"],
            "RDW-CV": ["rdw", "rdw-cv", "red cell distribution"],
            "MPV": ["mpv", "mean platelet volume"],
            "Neutrophils": ["neutrophils", "neutrophil"],
            "Lymphocytes": ["lymphocytes", "lymphocyte"],
            "Monocytes": ["monocytes", "monocyte"],
            "Eosinophils": ["eosinophils", "eosinophil"],
            
            # Gamma GT
            "Gamma Glutamyl Transferase": ["gamma glutamyl", "ggt", "gamma.*gt"],
            
            # Additional
            "Glucose": ["glucose", "blood sugar"],
            "Cholesterol": ["cholesterol", "total cholesterol"],
        }
        
        # Extract values for all parameters
        extracted_count = 0
        for param_name, keywords in keyword_map.items():
            value = self.extract_value_with_keywords(text, keywords)
            if value is not None:
                data[param_name] = value
                extracted_count += 1
        
        print(f"DEBUG: Extracted {extracted_count} parameters")
        
        # Special handling for structured table format
        lines = text.split('\n')
        print(f"DEBUG: Analyzing {len(lines)} lines")
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Look for patterns like "Hemoglobin 11.3 g/dL"
            if any(param_word in line_lower for param_word in ['hemoglobin', 'rbc', 'wbc', 'platelet', 'bilirubin', 'sgot', 'sgpt', 'albumin']):
                print(f"DEBUG Line {i}: {line}")
                
                # Try to extract number from line
                numbers = re.findall(r'([0-9]+\.?[0-9]*)', line)
                if numbers:
                    print(f"DEBUG: Found numbers in line: {numbers}")
            
            # Look for colon format: "Hemoglobin: 11.3"
            match = re.search(r'([a-z/\s]+):\s*([0-9]+\.?[0-9]*)', line_lower)
            if match:
                param = match.group(1).strip()
                value = float(match.group(2))
                print(f"DEBUG: Colon format: {param} = {value}")
        
        # Extract blood pressure
        bp_pattern = r"(\d{2,3})/(\d{2,3})"
        bp_matches = re.findall(bp_pattern, text)
        if bp_matches:
            data["Blood Pressure Systolic"] = float(bp_matches[0][0])
            data["Blood Pressure Diastolic"] = float(bp_matches[0][1])
            print(f"DEBUG: Found BP: {bp_matches[0][0]}/{bp_matches[0][1]}")
        
        # Calculate derived values
        if data["Albumin"] and data["Total Protein"]:
            if data["Globulin"] is None:
                data["Globulin"] = round(data["Total Protein"] - data["Albumin"], 2)
                print(f"DEBUG: Calculated Globulin: {data['Globulin']}")
            
            if data["A/G Ratio"] is None and data["Globulin"] and data["Globulin"] > 0:
                data["A/G Ratio"] = round(data["Albumin"] / data["Globulin"], 2)
                print(f"DEBUG: Calculated A/G Ratio: {data['A/G Ratio']}")
        
        # Print summary
        print("=" * 80)
        print("DEBUG: EXTRACTED PARAMETERS SUMMARY:")
        for key, value in data.items():
            if value is not None:
                print(f"  {key}: {value}")
        print("=" * 80)
        
        return data
    
    def process_pdf_report(self, pdf_bytes):
        """Main method to process PDF and return structured data"""
        print("=" * 80)
        print("DEBUG: STARTING PDF PROCESSING")
        print("=" * 80)
        
        text = self.extract_text_from_pdf(pdf_bytes)
        
        # Show OCR output summary
        print(f"OCR extracted {len(text)} characters")
        print(f"Sample of OCR text (first 1500 chars):")
        print(text[:1500])
        
        parsed_data = self.parse_medical_report(text)
        
        print("=" * 80)
        print("DEBUG: PROCESSING COMPLETE")
        print("=" * 80)
        
        return parsed_data, text
    
    def get_detected_parameters(self, parsed_data):
        """Get list of parameters that were successfully detected"""
        detected = []
        for key, value in parsed_data.items():
            if key not in ["Date", "Report Type", "Notes"] and value is not None:
                detected.append(key)
        return detected '''

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import re
from datetime import datetime
import os
from config import EXCEL_COLUMNS, TEST_PARAMETERS


class OCRProcessor:
    def __init__(self):
        """
        Cloud Safe Configuration
        - Do NOT hardcode poppler / tesseract paths
        - On Streamlit Cloud, system packages from packages.txt handle everything
        """
        print("Environment:", os.name)

        # Optional Windows Support (Only if installed normally)
        if os.name == "nt":
            try:
                win_tess = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                if os.path.exists(win_tess):
                    pytesseract.pytesseract.tesseract_cmd = win_tess
                    print("Using Windows Tesseract")
                else:
                    print("Windows Tesseract not found — relying on PATH")
            except:
                pass

        # Poppler path NOT required anymore
        self.poppler_path = None

    def extract_text_from_pdf(self, pdf_bytes):
        """Convert PDF to images and extract text using OCR"""
        try:
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
        text_lower = text.lower()

        if any(keyword in text_lower for keyword in
               ['liver function', 'lft', 'sgot', 'sgpt', 'bilirubin']):
            return "Liver Function Test (LFT)"
        elif any(keyword in text_lower for keyword in
                 ['complete blood', 'cbc', 'cbp', 'hemoglobin', 'wbc']):
            return "Complete Blood Picture (CBP)"
        elif any(keyword in text_lower for keyword in
                 ['thyroid', 'tsh', 't3', 't4']):
            return "Thyroid Test"
        elif any(keyword in text_lower for keyword in
                 ['blood pressure', 'heart rate', 'temperature']):
            return "Vitals Check"
        else:
            return "Blood Test"

    def extract_value_with_keywords(self, text, keywords):
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
        print("Parsing extracted text...")

        data = {col: None for col in EXCEL_COLUMNS}

        data["Date"] = datetime.now().strftime("%Y-%m-%d")
        data["Report Type"] = self.detect_report_type(text)
        data["Notes"] = ""

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
            "MCV": ["mcv"],
            "MCH": ["mch"],
            "MCHC": ["mchc"],
            "Glucose": ["glucose", "blood sugar"],
            "Cholesterol": ["cholesterol"]
        }

        for name, keys in keyword_map.items():
            value = self.extract_value_with_keywords(text, keys)
            if value is not None:
                data[name] = value

        bp = re.findall(r"(\d{2,3})/(\d{2,3})", text)
        if bp:
            data["Blood Pressure Systolic"] = float(bp[0][0])
            data["Blood Pressure Diastolic"] = float(bp[0][1])

        if data["Albumin"] and data["Total Protein"]:
            if not data["Globulin"]:
                data["Globulin"] = round(data["Total Protein"] - data["Albumin"], 2)

            if data["Globulin"] and not data["A/G Ratio"]:
                data["A/G Ratio"] = round(data["Albumin"] / data["Globulin"], 2)

        return data

    def process_pdf_report(self, pdf_bytes):
        text = self.extract_text_from_pdf(pdf_bytes)
        parsed_data = self.parse_medical_report(text)
        return parsed_data, text

    def get_detected_parameters(self, parsed_data):
        detected = []
        for key, value in parsed_data.items():
            if key not in ["Date", "Report Type", "Notes"] and value is not None:
                detected.append(key)
        return detected
