import pandas as pd
import os
from config import REPORTS_DIR, EXCEL_COLUMNS

class DataManager:
    def __init__(self, username):
        self.username = username
        self.excel_file = os.path.join(REPORTS_DIR, f"{username}_reports.xlsx")
        self._ensure_excel_file()
    
    def _ensure_excel_file(self):
        """Create Excel file if it doesn't exist"""
        if not os.path.exists(self.excel_file):
            df = pd.DataFrame(columns=EXCEL_COLUMNS)
            df.to_excel(self.excel_file, index=False)
    
    def add_report(self, report_data):
        """Add a new report to the Excel file"""
        try:
            df = pd.read_excel(self.excel_file)
            new_row = pd.DataFrame([report_data])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(self.excel_file, index=False)
            return True, "Report added successfully"
        except Exception as e:
            return False, f"Error adding report: {str(e)}"
    
    def get_all_reports(self):
        """Get all reports for the user"""
        try:
            df = pd.read_excel(self.excel_file)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date', ascending=False)
            return df
        except Exception as e:
            return pd.DataFrame(columns=EXCEL_COLUMNS)
    
    def get_latest_report(self):
        """Get the most recent report"""
        df = self.get_all_reports()
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
    
    def get_parameter_history(self, parameter):
        """Get history of a specific parameter"""
        df = self.get_all_reports()
        if parameter in df.columns:
            history = df[['Date', parameter]].dropna()
            return history
        return pd.DataFrame()
    
    def delete_report(self, index):
        """Delete a report by index"""
        try:
            df = pd.read_excel(self.excel_file)
            df = df.drop(index)
            df.to_excel(self.excel_file, index=False)
            return True, "Report deleted successfully"
        except Exception as e:
            return False, f"Error deleting report: {str(e)}"
    
    def update_report(self, index, report_data):
        """Update an existing report"""
        try:
            df = pd.read_excel(self.excel_file)
            for key, value in report_data.items():
                if key in df.columns:
                    df.at[index, key] = value
            df.to_excel(self.excel_file, index=False)
            return True, "Report updated successfully"
        except Exception as e:
            return False, f"Error updating report: {str(e)}"