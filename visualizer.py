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
            return None
        
        # Filter by report type if specified
        if report_type and 'Report Type' in df.columns:
            df = df[df['Report Type'] == report_type]
        
        if df.empty:
            return None
        
        # Group by patient name if available
        if 'Patient Name' in df.columns:
            patients = df['Patient Name'].unique()
        else:
            patients = ['All Tests']
        
        fig = go.Figure()
        
        # Add a line for each patient
        for i, patient in enumerate(patients):
            if 'Patient Name' in df.columns:
                patient_data = df[df['Patient Name'] == patient]
            else:
                patient_data = df
            
            patient_data = patient_data[['Date', parameter]].dropna()
            
            if not patient_data.empty:
                color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
                
                fig.add_trace(go.Scatter(
                    x=patient_data['Date'],
                    y=patient_data[parameter],
                    mode='lines+markers',
                    name=f"{patient}",
                    line=dict(color=color, width=3),
                    marker=dict(size=10, symbol='circle'),
                    hovertemplate=(
                        '<b>%{text}</b><br>' +
                        'Date: %{x}<br>' +
                        f'{parameter}: %{{y}}<br>' +
                        'Patient: ' + str(patient) +
                        '<extra></extra>'
                    ),
                    text=patient_data['Date'].dt.strftime('%Y-%m-%d')
                ))
        
        # Set y-axis to start from 0
        y_min = 0
        y_max = df[parameter].max() * 1.1 if not df[parameter].empty else 10
        
        fig.update_layout(
            title={
                'text': f"{parameter} Trend Analysis",
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
            hovermode='closest',
            height=500,
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                tickfont=dict(color='black', size=12),
                title_font=dict(color='black', size=14),
                zeroline=True,
                zerolinecolor='black'
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
            return None
        
        # Filter by report type if specified
        if report_type and 'Report Type' in df.columns:
            df = df[df['Report Type'] == report_type]
        
        # Get latest values for each parameter
        latest_values = {}
        for param in parameters:
            if param in df.columns:
                latest = df[param].dropna().iloc[-1] if not df[param].dropna().empty else None
                latest_values[param] = latest
        
        if not latest_values:
            return None
        
        fig = go.Figure()
        
        colors = COLOR_PALETTE[:len(latest_values)]
        
        fig.add_trace(go.Bar(
            x=list(latest_values.keys()),
            y=list(latest_values.values()),
            marker_color=colors,
            text=[f"{v:.2f}" if isinstance(v, (int, float)) else str(v) for v in latest_values.values()],
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
                title_font=dict(color='black', size=14)
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
            return None
        
        # Filter ultrasound reports
        ultrasound_df = df[df['Report Type'] == 'Ultrasound Report']
        
        if ultrasound_df.empty:
            return None
        
        # Extract values
        trend_data = ultrasound_df[['Date', parameter]].dropna()
        
        if trend_data.empty:
            return None
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=trend_data['Date'],
            y=trend_data[parameter],
            mode='lines+markers',
            name=parameter,
            line=dict(color=COLOR_PALETTE[0], width=3),
            marker=dict(size=10, symbol='circle')
        ))
        
        # Set y-axis to start from 0
        y_min = 0
        y_max = trend_data[parameter].max() * 1.1
        
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
                title_font=dict(color='black', size=14)
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