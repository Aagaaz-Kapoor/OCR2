# Medical Report OCR System 🏥

A comprehensive Python-based system for managing medical reports with OCR capabilities, user authentication, data storage, and visualization.

## Features

- 🔐 **User Authentication**: Secure login and signup with password hashing
- 📄 **PDF OCR Processing**: Automatically extract medical data from PDF reports
- 💾 **Data Storage**: Store reports in Excel format for each user
- 📊 **Data Visualization**: Interactive charts showing health trends over time
- ⚠️ **Alert System**: Automatic highlighting of abnormal values
- 📈 **Historical Tracking**: Monitor health parameters across multiple reports
- 📥 **Export Functionality**: Download reports as Excel files

## Installation

### Prerequisites

1. **Python 3.8+**
2. **Tesseract OCR** (Required for PDF text extraction)

#### Installing Tesseract OCR:

**Windows:**
```bash
# Download installer from:
https://github.com/UB-Mannheim/tesseract/wiki
# Run installer and note installation path
# Default: C:\Program Files\Tesseract-OCR\tesseract.exe
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### Setup

1. **Clone or download the project**

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure Tesseract path (Windows only):**
   - Open `ocr_processor.py`
   - Uncomment and set the correct path:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

## Project Structure

```
medical_ocr_system/
├── app.py                 # Main Streamlit application
├── auth.py                # User authentication
├── ocr_processor.py       # PDF processing and OCR
├── data_manager.py        # Excel data management
├── visualizer.py          # Data visualization
├── config.py              # Configuration and constants
├── requirements.txt       # Python dependencies
├── README.md             # Documentation
└── data/                 # Auto-created data directory
    ├── users.json        # User credentials
    └── reports/          # User medical reports
```

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### Workflow

1. **Sign Up / Login**
   - Create a new account or login with existing credentials
   - Passwords are securely hashed using bcrypt

2. **Upload Medical Report**
   - Navigate to "Upload Report"
   - Upload a PDF medical report
   - Review and edit extracted data
   - Save the report

3. **View Dashboard**
   - See latest health metrics
   - View status indicators (Normal/High/Low)
   - Monitor trends over time with interactive charts

4. **Browse All Reports**
   - View complete history of reports
   - Download data as Excel file

## Supported Medical Parameters

The system automatically extracts and tracks:

- **Hemoglobin** (12.0-17.0 g/dL)
- **RBC** (4.0-6.0 million/µL)
- **WBC** (4000-11000 /µL)
- **Platelets** (150000-400000 /µL)
- **Glucose** (70-100 mg/dL)
- **Cholesterol** (0-200 mg/dL)
- **Blood Pressure** (Systolic: 90-120, Diastolic: 60-80 mmHg)
- **Heart Rate** (60-100 bpm)
- **Temperature** (97.0-99.0 °F)

## Configuration

Edit `config.py` to:
- Modify normal ranges for medical parameters
- Add new parameters
- Change data storage locations

## Data Security

- Passwords are hashed using bcrypt
- Each user's data is stored separately
- Local file storage (no cloud dependency)

## Troubleshooting

### "Tesseract not found" Error
- Install Tesseract OCR (see Prerequisites)
- Set correct path in `ocr_processor.py` for Windows

### Poor OCR Accuracy
- Ensure PDF is high quality and not scanned at low resolution
- Check that text in PDF is clear and readable
- Try pre-processing PDF with image enhancement tools

### Data Not Saving
- Check write permissions in project directory
- Ensure `data/` directory is created
- Check Excel file is not open in another program

## Future Enhancements

- [ ] Image file support (JPEG, PNG)
- [ ] Multi-language OCR support
- [ ] Machine learning for better data extraction
- [ ] Email notifications for abnormal values
- [ ] Doctor/patient sharing functionality
- [ ] Mobile responsive design improvements
- [ ] PDF report generation
- [ ] Integration with health APIs

## Dependencies

- **streamlit**: Web interface
- **pytesseract**: OCR engine wrapper
- **pdf2image**: PDF to image conversion
- **pandas**: Data manipulation
- **openpyxl**: Excel file handling
- **plotly**: Interactive visualizations
- **bcrypt**: Password hashing
- **Pillow**: Image processing

## License

This project is open source and available for educational and personal use.

## Support

For issues or questions:
1. Check Troubleshooting section
2. Verify all prerequisites are installed
3. Ensure file permissions are correct

## Contributing

Contributions are welcome! Areas for improvement:
- Enhanced OCR accuracy
- Additional medical parameters
- Better PDF parsing algorithms
- UI/UX improvements
- Additional export formats

---

**Note**: This system is for personal health tracking only and should not replace professional medical advice.