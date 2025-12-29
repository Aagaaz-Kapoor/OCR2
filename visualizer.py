import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from config import NORMAL_RANGES, COLOR_PALETTE

class Visualizer:
    def __init__(self):
        self.normal_ranges = NORMAL_RANGES
    
    def check_value_status(self, parameter, value):
        """Check if a value is within normal range"""
        if parameter not in self.normal_ranges or value is None or pd.isna(value):
            return "Unknown", "#808080"
        
        ranges = self.normal_ranges[parameter]
        if value < ranges["min"]:
            return "Low", "#FF4444"
        elif value > ranges["max"]:
            return "High", "#FF4444"
        else:
            return "Normal", "#00CC00"
    
    def create_status_table(self, latest_values):
        """Create a status summary table"""
        data = []
        
        for param, value in latest_values.items():
            if param in self.normal_ranges and value is not None and not pd.isna(value):
                status, color = self.check_value_status(param, value)
                ranges = self.normal_ranges[param]
                data.append({
                    "Parameter": param,
                    "Value": f"{value} {ranges['unit']}",
                    "Normal Range": f"{ranges['min']} - {ranges['max']} {ranges['unit']}",
                    "Status": status
                })
        
        return pd.DataFrame(data)
    
    def create_multi_test_trend_chart(self, df, parameter, report_type=None):
        """Create a multi-line trend chart showing all tests of same type"""
        if df.empty or parameter not in df.columns:
            print(f"Warning: Parameter '{parameter}' not found in data or dataframe is empty")
            return None
        
        # Make sure Date column is datetime
        if 'Date' in df.columns:
            df = df.copy()
            try:
                df['Date'] = pd.to_datetime(df['Date'])
            except Exception as e:
                print(f"Error: Could not convert Date column to datetime: {e}")
                return None
        
        # Filter by report type if specified
        if report_type and 'Report Type' in df.columns:
            # Ensure report_type is not a Series or pandas object
            if isinstance(report_type, (pd.Series, pd.DataFrame)):
                report_type = str(report_type.iloc[0]) if not report_type.empty else None
            
            if report_type:
                df_filtered = df[df['Report Type'] == report_type]
                if df_filtered.empty:
                    # If no specific report type, use all data
                    df_filtered = df
            else:
                df_filtered = df
        else:
            df_filtered = df
        
        # Check if we have data for this parameter
        if df_filtered[parameter].dropna().empty:
            print(f"Warning: No data available for parameter: {parameter}")
            return None
        
        # Group by patient name if available
        if 'Patient Name' in df_filtered.columns:
            patients = df_filtered['Patient Name'].unique()
        else:
            patients = ['All Tests']
        
        fig = go.Figure()
        
        # Add a line for each patient
        for i, patient in enumerate(patients):
            if 'Patient Name' in df_filtered.columns:
                patient_data = df_filtered[df_filtered['Patient Name'] == patient]
            else:
                patient_data = df_filtered
            
            # Get data for this parameter
            patient_data = patient_data[['Date', parameter]].dropna()
            
            if not patient_data.empty:
                # Sort by date
                patient_data = patient_data.sort_values('Date')
                
                color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
                
                fig.add_trace(go.Scatter(
                    x=patient_data['Date'],
                    y=patient_data[parameter],
                    mode='lines+markers',
                    name=f"{patient}",
                    line=dict(color=color, width=3),
                    marker=dict(size=10, symbol='circle'),
                    hovertemplate=(
                        '<b>Date: %{x|%Y-%m-%d}</b><br>' +
                        f'{parameter}: %{{y}}<br>' +
                        'Patient: ' + str(patient) +
                        '<extra></extra>'
                    ),
                    text=[f"{patient}: {val}" for val in patient_data[parameter]]
                ))
        
        if len(fig.data) == 0:
            print(f"Warning: No valid data points for parameter: {parameter}")
            return None
        
        # Set y-axis range
        try:
            y_min = df_filtered[parameter].min() * 0.9 if df_filtered[parameter].min() > 0 else 0
            y_max = df_filtered[parameter].max() * 1.1
        except:
            y_min = 0
            y_max = 10
        
        # Format x-axis dates
        fig.update_layout(
            title={
                'text': f"{parameter} Trend Analysis",
                'font': {'size': 20, 'color': 'black'},
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title={
                'text': "Date",
                'font': {'size': 14, 'color': 'black'}
            },
            yaxis_title={
                'text': f"{parameter} ({NORMAL_RANGES.get(parameter, {}).get('unit', '')})",
                'font': {'size': 14, 'color': 'black'}
            },
            hovermode='closest',
            height=500,
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=True if len(patients) > 1 else False,
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                tickfont=dict(color='black', size=12),
                title_font=dict(color='black', size=14),
                zeroline=True,
                zerolinecolor='black',
                tickformat='%Y-%m-%d',
                type='date'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                tickfont=dict(color='black', size=12),
                title_font=dict(color='black', size=14),
                zeroline=True,
                zerolinecolor='black',
                range=[y_min, y_max]
            ),
            legend=dict(
                font=dict(color='black', size=12),
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='black',
                borderwidth=1
            )
        )
        
        return fig
    
    def create_comparison_chart(self, df, parameters, report_type=None):
        """Create comparison chart for multiple parameters"""
        if df.empty:
            print("Warning: No data available for comparison")
            return None
        
        # Make sure Date column is datetime
        if 'Date' in df.columns:
            df = df.copy()
            try:
                df['Date'] = pd.to_datetime(df['Date'])
            except Exception as e:
                print(f"Error: Could not convert Date column to datetime: {e}")
                return None
        
        # Filter by report type if specified
        if report_type and 'Report Type' in df.columns:
            df = df[df['Report Type'] == report_type]
        
        if df.empty:
            print(f"Warning: No data available for report type: {report_type}")
            return None
        
        # Get latest report
        latest_report = df.sort_values('Date', ascending=False).iloc[0] if not df.empty else None
        
        if latest_report is None:
            print("Warning: No latest report found")
            return None
        
        # Get latest values for each parameter
        latest_values = {}
        for param in parameters:
            if param in df.columns:
                # Get the most recent non-null value
                non_null_values = df[['Date', param]].dropna()
                if not non_null_values.empty:
                    latest = non_null_values.sort_values('Date', ascending=False).iloc[0][param]
                    latest_values[param] = latest
        
        if not latest_values:
            print("Warning: No parameter values found for comparison")
            return None
        
        fig = go.Figure()
        
        colors = COLOR_PALETTE[:len(latest_values)]
        
        # Prepare data for display
        param_names = list(latest_values.keys())
        param_values = list(latest_values.values())
        
        # Get units for y-axis labels
        units = []
        for param in param_names:
            unit = NORMAL_RANGES.get(param, {}).get('unit', '')
            units.append(f" ({unit})" if unit else "")
        
        # Create display names with units
        display_names = [f"{name}{units[i]}" for i, name in enumerate(param_names)]
        
        fig.add_trace(go.Bar(
            x=display_names,
            y=param_values,
            marker_color=colors,
            text=[f"{v:.2f}" if isinstance(v, (int, float)) else str(v) for v in param_values],
            textposition='auto',
            textfont=dict(color='black', size=12)
        ))
        
        fig.update_layout(
            title={
                'text': "Latest Values Comparison",
                'font': {'size': 20, 'color': 'black'}
            },
            xaxis_title={
                'text': "Parameters",
                'font': {'size': 14, 'color': 'black'}
            },
            yaxis_title={
                'text': "Values",
                'font': {'size': 14, 'color': 'black'}
            },
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(
                tickfont=dict(color='black', size=12),
                title_font=dict(color='black', size=14),
                tickangle=-45
            ),
            yaxis=dict(
                tickfont=dict(color='black', size=12),
                title_font=dict(color='black', size=14),
                zeroline=True,
                zerolinecolor='black'
            )
        )
        
        return fig
    
    def create_ultrasound_trend_chart(self, df, parameter):
        """Create trend chart for ultrasound parameters"""
        if df.empty or parameter not in df.columns:
            print(f"Warning: Parameter '{parameter}' not found in ultrasound data")
            return None
        
        # Make sure Date column is datetime
        if 'Date' in df.columns:
            df = df.copy()
            try:
                df['Date'] = pd.to_datetime(df['Date'])
            except Exception as e:
                print(f"Error: Could not convert Date column to datetime: {e}")
                return None
        
        # Filter ultrasound reports
        ultrasound_df = df[df['Report Type'] == 'Ultrasound Report']
        
        if ultrasound_df.empty:
            print("Warning: No ultrasound reports found")
            return None
        
        # Extract values
        trend_data = ultrasound_df[['Date', parameter]].dropna()
        
        if trend_data.empty:
            print(f"Warning: No data available for ultrasound parameter: {parameter}")
            return None
        
        # Sort by date
        trend_data = trend_data.sort_values('Date')
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=trend_data['Date'],
            y=trend_data[parameter],
            mode='lines+markers',
            name=parameter,
            line=dict(color=COLOR_PALETTE[0], width=3),
            marker=dict(size=10, symbol='circle'),
            hovertemplate=(
                '<b>Date: %{x|%Y-%m-%d}</b><br>' +
                f'{parameter}: %{{y}}<br>' +
                '<extra></extra>'
            )
        ))
        
        # Set y-axis range
        try:
            y_min = trend_data[parameter].min() * 0.9 if trend_data[parameter].min() > 0 else 0
            y_max = trend_data[parameter].max() * 1.1
        except:
            y_min = 0
            y_max = 10
        
        fig.update_layout(
            title={
                'text': f"{parameter} - Ultrasound Trend",
                'font': {'size': 20, 'color': 'black'}
            },
            xaxis_title={
                'text': "Date",
                'font': {'size': 14, 'color': 'black'}
            },
            yaxis_title={
                'text': parameter,
                'font': {'size': 14, 'color': 'black'}
            },
            height=500,
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                tickfont=dict(color='black', size=12),
                title_font=dict(color='black', size=14),
                tickformat='%Y-%m-%d',
                type='date'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                tickfont=dict(color='black', size=12),
                title_font=dict(color='black', size=14),
                range=[y_min, y_max]
            )
        )
        
        return fig