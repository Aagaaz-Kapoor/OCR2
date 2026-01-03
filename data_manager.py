import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from config import EXCEL_COLUMNS, REPORTS_DIR

class DataManager:
    """Manages Excel file operations for medical reports"""
    def __init__(self, username):
        self.username = username
        self.excel_file = os.path.join(REPORTS_DIR, f"{username}_reports.xlsx")
        self._ensure_excel_file()
    
    def _ensure_excel_file(self):
        """Create Excel file with proper columns if it doesn't exist"""
        if not os.path.exists(self.excel_file):
            df = pd.DataFrame(columns=EXCEL_COLUMNS)
            df.to_excel(self.excel_file, index=False)
    
    def get_all_reports(self):
        """Get all reports as a DataFrame"""
        try:
            if os.path.exists(self.excel_file):
                df = pd.read_excel(self.excel_file)
                # Ensure Date column is datetime
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                return df
            else:
                return pd.DataFrame(columns=EXCEL_COLUMNS)
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return pd.DataFrame(columns=EXCEL_COLUMNS)
    
    def add_report(self, report_data):
        """Add a new report to the Excel file"""
        try:
            # Load existing data
            df = self.get_all_reports()
            
            # Create new row from report_data
            new_row = {}
            for col in EXCEL_COLUMNS:
                new_row[col] = report_data.get(col, None)
            
            # Convert to DataFrame and append
            new_df = pd.DataFrame([new_row])
            df = pd.concat([df, new_df], ignore_index=True)
            
            # Save to Excel
            df.to_excel(self.excel_file, index=False)
            return True, "Report added successfully"
        except Exception as e:
            return False, f"Error adding report: {str(e)}"
    
    def delete_report(self, index):
        """Delete a report by index"""
        try:
            df = self.get_all_reports()
            
            if index < 0 or index >= len(df):
                return False, "Invalid report index"
            
            # Remove the row
            df = df.drop(index=index).reset_index(drop=True)
            
            # Save back to Excel
            df.to_excel(self.excel_file, index=False)
            return True, "Report deleted successfully"
        except Exception as e:
            return False, f"Error deleting report: {str(e)}"

class TrendAnalyzer:
    def __init__(self, data_manager):
        self.dm = data_manager
    
    def get_parameter_history(self, patient_name, test_type, parameter):
        """Get chronological history of a specific parameter for a patient"""
        df = self.dm.get_all_reports()
        
        if df.empty:
            return pd.DataFrame()
        
        # Filter by patient and test type
        filtered = df[
            (df['Patient Name'] == patient_name) & 
            (df['Report Type'] == test_type)
        ].copy()
        
        if filtered.empty:
            return pd.DataFrame()
        
        # Sort by date
        filtered = filtered.sort_values('Date', ascending=True)
        
        # Extract parameter values with dates
        history = filtered[['Date', parameter]].dropna()
        
        if not history.empty:
            # Calculate trend indicators
            history['Trend'] = history[parameter].pct_change() * 100  # Percentage change
            history['Change'] = history[parameter].diff()  # Absolute change
            history['Moving_Avg'] = history[parameter].rolling(window=3, min_periods=1).mean()
        
        return history
    
    def get_test_type_summary(self, patient_name):
        """Get summary of all test types for a patient"""
        df = self.dm.get_all_reports()
        
        if df.empty or patient_name not in df['Patient Name'].values:
            return {}
        
        # Filter by patient
        patient_data = df[df['Patient Name'] == patient_name].copy()
        
        # Group by test type
        summary = {}
        for test_type in patient_data['Report Type'].unique():
            test_reports = patient_data[patient_data['Report Type'] == test_type]
            
            summary[test_type] = {
                'count': len(test_reports),
                'first_date': test_reports['Date'].min(),
                'last_date': test_reports['Date'].max(),
                'frequency_days': self._calculate_frequency(test_reports),
                'parameters': self._get_common_parameters(test_reports)
            }
        
        return summary
    
    def _calculate_frequency(self, test_reports):
        """Calculate average frequency between tests"""
        if len(test_reports) < 2:
            return None
        
        dates = pd.to_datetime(test_reports['Date'].sort_values())
        intervals = []
        
        for i in range(1, len(dates)):
            interval = (dates.iloc[i] - dates.iloc[i-1]).days
            intervals.append(interval)
        
        return np.mean(intervals) if intervals else None
    
    def _get_common_parameters(self, test_reports):
        """Get parameters that appear in multiple reports of same test type"""
        common_params = []
        for col in test_reports.columns:
            if col not in ['Date', 'Report Type', 'Patient Name', 'Notes', 
                          'Patient Age', 'Patient Gender', 'Ultrasound Findings', 
                          'Ultrasound Impression']:
                non_null_count = test_reports[col].notna().sum()
                if non_null_count > 1:  # Appears in at least 2 reports
                    common_params.append(col)
        return common_params
    
    def detect_significant_changes(self, patient_name, test_type, parameter, threshold_percent=10):
        """Detect significant changes in parameter values"""
        history = self.get_parameter_history(patient_name, test_type, parameter)
        
        if history.empty or len(history) < 2:
            return []
        
        significant_changes = []
        
        for i in range(1, len(history)):
            current = history.iloc[i]
            previous = history.iloc[i-1]
            
            if abs(current['Trend']) >= threshold_percent:
                change_info = {
                    'date': current['Date'],
                    'from_value': previous[parameter],
                    'to_value': current[parameter],
                    'change_percent': current['Trend'],
                    'change_absolute': current['Change'],
                    'direction': 'increasing' if current['Trend'] > 0 else 'decreasing'
                }
                significant_changes.append(change_info)
        
        return significant_changes
