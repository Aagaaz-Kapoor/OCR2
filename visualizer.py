import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from config import NORMAL_RANGES

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
    
    def create_trend_chart(self, df, parameter):
        """Create a trend line chart for a parameter"""
        if df.empty or parameter not in df.columns:
            return None
        
        data = df[['Date', parameter]].dropna()
        if data.empty:
            return None
        
        fig = go.Figure()
        
        # Add the trend line
        fig.add_trace(go.Scatter(
            x=data['Date'],
            y=data[parameter],
            mode='lines+markers',
            name=parameter,
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=8)
        ))
        
        # Add normal range bands if available
        if parameter in self.normal_ranges:
            ranges = self.normal_ranges[parameter]
            fig.add_hrect(
                y0=ranges["min"],
                y1=ranges["max"],
                fillcolor="green",
                opacity=0.1,
                line_width=0,
                annotation_text="Normal Range",
                annotation_position="top left"
            )
            
            # Add range lines
            fig.add_hline(
                y=ranges["min"],
                line_dash="dash",
                line_color="green",
                annotation_text=f"Min: {ranges['min']}"
            )
            fig.add_hline(
                y=ranges["max"],
                line_dash="dash",
                line_color="green",
                annotation_text=f"Max: {ranges['max']}"
            )
        
        fig.update_layout(
            title=f"{parameter} Trend Over Time",
            xaxis_title="Date",
            yaxis_title=f"{parameter} ({self.normal_ranges.get(parameter, {}).get('unit', '')})",
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    def create_comparison_chart(self, latest_values):
        """Create a bar chart comparing current values with normal ranges"""
        parameters = []
        values = []
        colors = []
        
        for param, value in latest_values.items():
            if param in self.normal_ranges and value is not None and not pd.isna(value):
                parameters.append(param)
                values.append(value)
                _, color = self.check_value_status(param, value)
                colors.append(color)
        
        if not parameters:
            return None
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=parameters,
            y=values,
            marker_color=colors,
            text=values,
            textposition='auto',
        ))
        
        fig.update_layout(
            title="Current Values vs Normal Ranges",
            xaxis_title="Parameter",
            yaxis_title="Value",
            height=400,
            showlegend=False
        )
        
        return fig
    
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