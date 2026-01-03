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
        
        # Group by patient name AND report type to show separate lines for same patient same test type
        groups = []
        if 'Patient Name' in df_filtered.columns and 'Report Type' in df_filtered.columns:
            # Group by both Patient Name and Report Type
            grouped = df_filtered.groupby(['Patient Name', 'Report Type'])
            for (patient, report_type), group_data in grouped:
                groups.append({
                    'patient': patient,
                    'report_type': report_type,
                    'data': group_data
                })
        elif 'Patient Name' in df_filtered.columns:
            # Fallback: group by patient name only
            patients = df_filtered['Patient Name'].unique()
            for patient in patients:
                groups.append({
                    'patient': patient,
                    'report_type': None,
                    'data': df_filtered[df_filtered['Patient Name'] == patient]
                })
        else:
            # No grouping columns available
            groups.append({
                'patient': 'All Tests',
                'report_type': None,
                'data': df_filtered
            })
        
        fig = go.Figure()
        
        # Add a line for each group (patient + report type combination)
        for i, group in enumerate(groups):
            # Get data for this parameter
            patient_data = group['data'][['Date', parameter]].dropna()
            
            if not patient_data.empty:
                # Sort by date (ascending)
                patient_data = patient_data.sort_values('Date')
                
                color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
                
                # Create label for legend
                if group['report_type']:
                    label = f"{group['patient']} - {group['report_type']}"
                else:
                    label = f"{group['patient']}"
                
                fig.add_trace(go.Scatter(
                    x=patient_data['Date'],
                    y=patient_data[parameter],
                    mode='lines+markers',
                    name=label,
                    line=dict(color=color, width=3),
                    marker=dict(size=10, symbol='circle'),
                    hovertemplate=(
                        '<b>Date: %{x|%Y-%m-%d}</b><br>' +
                        f'{parameter}: %{{y}}<br>' +
                        'Patient: ' + str(group['patient']) +
                        (f'<br>Test: {group["report_type"]}' if group['report_type'] else '') +
                        '<extra></extra>'
                    ),
                    text=[f"{label}: {val}" for val in patient_data[parameter]]
                ))
        
        if len(fig.data) == 0:
            print(f"Warning: No valid data points for parameter: {parameter}")
            return None
        
        # Set y-axis range - always start from 0
        try:
            y_min = 0
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
            showlegend=True if len(groups) > 1 else False,
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
        
        # Set y-axis range - always start from 0
        try:
            y_min = 0
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

class AdvancedVisualizer(Visualizer):
    def __init__(self):
        super().__init__()
    
    def create_comprehensive_trend_dashboard(self, history_data):
        """Create comprehensive dashboard for multiple parameters"""
        if history_data.empty:
            return None
        
        fig = go.Figure()
        
        # Add line for each parameter
        for i, param in enumerate(history_data.columns):
            if param not in ['Date', 'Trend', 'Change', 'Moving_Avg']:
                fig.add_trace(go.Scatter(
                    x=history_data['Date'],
                    y=history_data[param],
                    mode='lines+markers',
                    name=param,
                    line=dict(color=COLOR_PALETTE[i % len(COLOR_PALETTE)], width=3),
                    marker=dict(size=8),
                    hovertemplate=f'<b>{param}</b>: %{{y}}<br>Date: %{{x|%Y-%m-%d}}<extra></extra>'
                ))
        
        fig.update_layout(
            title='Multi-Parameter Trend Analysis',
            xaxis_title='Date',
            yaxis_title='Values',
            hovermode='x unified',
            height=600,
            showlegend=True,
            plot_bgcolor='white'
        )
        
        return fig
    
    def create_trend_analysis_card(self, parameter, history, normal_range=None):
        """Create a summary card for parameter trend"""
        if history.empty:
            return None
        
        latest = history.iloc[-1]
        first = history.iloc[0]
        
        # Calculate overall trend
        overall_change = ((latest[parameter] - first[parameter]) / first[parameter] * 100 
                         if first[parameter] != 0 else 0)
        
        # Determine status
        if normal_range:
            status, color = self.check_value_status(parameter, latest[parameter])
        else:
            status = "No reference"
            color = "#808080"
        
        # Create card HTML/visual
        card_data = {
            'parameter': parameter,
            'latest_value': latest[parameter],
            'first_value': first[parameter],
            'change_percent': overall_change,
            'change_direction': 'up' if overall_change > 0 else 'down',
            'status': status,
            'color': color,
            'data_points': len(history),
            'time_span_days': (latest['Date'] - first['Date']).days
        }
        
        return card_data
    
    def create_parameter_comparison_matrix(self, df, test_type):
        """Create a matrix comparing multiple parameters across time"""
        if df.empty:
            return None
        
        # Filter by test type
        test_data = df[df['Report Type'] == test_type].copy()
        
        if test_data.empty:
            return None
        
        # Get numeric parameters
        numeric_params = []
        for col in test_data.columns:
            if col not in ['Date', 'Report Type', 'Patient Name', 'Notes', 
                          'Patient Age', 'Patient Gender']:
                # Check if numeric
                try:
                    pd.to_numeric(test_data[col], errors='coerce')
                    numeric_params.append(col)
                except:
                    continue
        
        # Create heatmap-like matrix
        fig = go.Figure(data=go.Heatmap(
            z=test_data[numeric_params].T.values,
            x=test_data['Date'],
            y=numeric_params,
            colorscale='RdYlGn',
            zmin=test_data[numeric_params].min().min(),
            zmax=test_data[numeric_params].max().max(),
            colorbar=dict(title="Value"),
            hoverongaps=False,
            hovertemplate='<b>%{y}</b><br>Date: %{x}<br>Value: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'{test_type} - Parameter Value Matrix',
            xaxis_title='Date',
            yaxis_title='Parameters',
            height=400,
            plot_bgcolor='white'
        )
        
        return fig
    
    def create_timeline_visualization(self, patient_data):
        """Create a timeline visualization of medical reports"""
        if patient_data.empty:
            return None
        
        # Ensure Date is datetime
        if 'Date' not in patient_data.columns:
            return None
        
        patient_data = patient_data.copy()
        patient_data['Date'] = pd.to_datetime(patient_data['Date'], errors='coerce')
        # Remove rows with invalid dates
        patient_data = patient_data[patient_data['Date'].notna()].copy()
        if patient_data.empty:
            return None
        patient_data = patient_data.sort_values('Date', ascending=True)
        
        # Create timeline chart
        fig = go.Figure()
        
        # Get unique report types for color coding
        report_types = patient_data['Report Type'].unique() if 'Report Type' in patient_data.columns else ['Report']
        colors = COLOR_PALETTE[:len(report_types)]
        color_map = {rt: colors[i % len(colors)] for i, rt in enumerate(report_types)}
        
        # Track which report types we've already added to legend
        seen_report_types = set()
        
        # Add markers for each report
        for idx, row in patient_data.iterrows():
            report_type = row.get('Report Type', 'Report')
            date = row['Date']
            
            if pd.notna(date):
                # Only show legend for first occurrence of each report type
                show_legend = report_type not in seen_report_types
                if show_legend:
                    seen_report_types.add(report_type)
                
                fig.add_trace(go.Scatter(
                    x=[date],
                    y=[0],
                    mode='markers+text',
                    name=report_type,
                    marker=dict(
                        size=15,
                        color=color_map.get(report_type, COLOR_PALETTE[0]),
                        symbol='circle',
                        line=dict(width=2, color='white')
                    ),
                    text=[report_type],
                    textposition='top center',
                    textfont=dict(size=10),
                    hovertemplate=(
                        f'<b>{report_type}</b><br>' +
                        f'Date: %{{x|%Y-%m-%d}}<br>' +
                        f'Patient: {row.get("Patient Name", "Unknown")}<br>' +
                        '<extra></extra>'
                    ),
                    showlegend=show_legend
                ))
        
        # Add timeline line
        if len(patient_data) > 1:
            dates = patient_data['Date'].dropna()
            if len(dates) > 1:
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=[0] * len(dates),
                    mode='lines',
                    name='Timeline',
                    line=dict(color='gray', width=2, dash='dash'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
        
        fig.update_layout(
            title={
                'text': 'Medical Test Timeline',
                'font': {'size': 20, 'color': 'black'}
            },
            xaxis_title={
                'text': 'Date',
                'font': {'size': 14, 'color': 'black'}
            },
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-0.5, 0.5]
            ),
            height=300,
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='closest',
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                tickfont=dict(color='black', size=12),
                title_font=dict(color='black', size=14),
                tickformat='%Y-%m-%d',
                type='date'
            )
        )
        
        return fig