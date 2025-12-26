"""
Chart Generation Service for Tahlil Platform
Automatically detects and generates appropriate charts for data visualization
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ChartData:
    """Chart data structure."""
    chart_type: str
    title: str
    x_axis: str
    y_axis: str
    data: List[Dict[str, Any]]
    config: Dict[str, Any]
    html: str

@dataclass
class ChartConfig:
    """Chart configuration options."""
    width: int = 800
    height: int = 600
    theme: str = 'plotly_white'
    responsive: bool = True
    display_mode_bar: bool = False

class ChartGenerator:
    """Automatic chart generation and detection."""
    
    def __init__(self):
        self.supported_chart_types = [
            'bar', 'line', 'pie', 'scatter', 'histogram', 'area', 'box', 'heatmap'
        ]
    
    def detect_chart_type(self, data: Dict[str, Any], columns: List[str]) -> str:
        """Automatically detect the best chart type for the data."""
        try:
            import pandas as pd
            
            # Convert data to DataFrame for analysis
            if isinstance(data, dict) and 'data' in data:
                df = pd.DataFrame(data['data'])
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame(data)
            
            # Heuristics for chart type detection
            chart_type = self._analyze_data_structure(df, columns)
            logger.info(f"Detected chart type: {chart_type}")
            return chart_type
            
        except Exception as e:
            logger.warning(f"Chart type detection failed: {e}")
            return 'bar'  # Default fallback
    
    def _analyze_data_structure(self, df, columns: List[str]) -> str:
        """Analyze data structure to recommend chart type."""
        if df.empty or len(columns) == 0:
            return 'bar'
        
        # Count data types
        numeric_columns = []
        categorical_columns = []
        datetime_columns = []
        
        for col in columns:
            if col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    numeric_columns.append(col)
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    datetime_columns.append(col)
                else:
                    categorical_columns.append(col)
        
        # Decision tree for chart type
        # If we have datetime and numeric data -> time series
        if len(datetime_columns) >= 1 and len(numeric_columns) >= 1:
            if len(datetime_columns) == 1 and len(numeric_columns) == 1:
                return 'line'  # Classic time series
            else:
                return 'scatter'  # Multiple numeric vs datetime
        
        # If we have categorical and numeric -> bar or pie
        if len(categorical_columns) >= 1 and len(numeric_columns) >= 1:
            # If categorical has few unique values -> pie chart
            cat_col = categorical_columns[0]
            if df[cat_col].nunique() <= 10:
                return 'pie'
            else:
                return 'bar'  # Many categories -> bar chart
        
        # If we have multiple numeric columns -> scatter or histogram
        if len(numeric_columns) >= 2:
            return 'scatter'
        elif len(numeric_columns) == 1:
            return 'histogram'
        
        # Default fallback
        return 'bar'
    
    def generate_chart(self, data: Dict[str, Any], chart_type: str = None, config: ChartConfig = None) -> ChartData:
        """Generate a chart based on data and specified type."""
        try:
            import pandas as pd
            
            # Convert data to DataFrame
            if isinstance(data, dict) and 'data' in data:
                df = pd.DataFrame(data['data'])
                columns = list(df.columns)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
                columns = list(df.columns)
            else:
                df = pd.DataFrame(data)
                columns = list(df.columns)
            
            # Auto-detect chart type if not specified
            if not chart_type:
                chart_type = self.detect_chart_type(data, columns)
            
            # Set default config
            if config is None:
                config = ChartConfig()
            
            # Generate chart based on type
            if chart_type == 'bar':
                return self._generate_bar_chart(df, config)
            elif chart_type == 'line':
                return self._generate_line_chart(df, config)
            elif chart_type == 'pie':
                return self._generate_pie_chart(df, config)
            elif chart_type == 'scatter':
                return self._generate_scatter_chart(df, config)
            elif chart_type == 'histogram':
                return self._generate_histogram_chart(df, config)
            elif chart_type == 'area':
                return self._generate_area_chart(df, config)
            elif chart_type == 'box':
                return self._generate_box_chart(df, config)
            elif chart_type == 'heatmap':
                return self._generate_heatmap_chart(df, config)
            else:
                # Default to bar chart
                return self._generate_bar_chart(df, config)
                
        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            return ChartData(
                chart_type='bar',
                title='Error',
                x_axis='',
                y_axis='',
                data=[],
                config={},
                html=f'<div class="error">Chart generation failed: {str(e)}</div>'
            )
    
    def _generate_bar_chart(self, df, config: ChartConfig) -> ChartData:
        """Generate a bar chart."""
        try:
            import plotly.graph_objects as go
            import plotly.offline as pyo
            
            # Get first categorical and first numeric column
            cat_col = None
            num_col = None
            
            for col in df.columns:
                if cat_col is None and not pd.api.types.is_numeric_dtype(df[col]):
                    cat_col = col
                elif num_col is None and pd.api.types.is_numeric_dtype(df[col]):
                    num_col = cat_col  # Use second numeric if first was categorical
                elif num_col is None and pd.api.types.is_numeric_dtype(df[col]):
                    num_col = col
                elif cat_col and num_col:
                    break
            
            if cat_col is None or num_col is None:
                raise ValueError("Need both categorical and numeric columns for bar chart")
            
            # Aggregate data by categorical column
            grouped = df.groupby(cat_col)[num_col].mean().sort_values(ascending=False)
            
            fig = go.Figure(data=[
                go.Bar(
                    x=grouped.index.tolist(),
                    y=grouped.values.tolist(),
                    marker_color='rgb(55, 83, 109)',  # Orange color
                    marker_line_color='rgb(255, 255, 255)',
                    marker_line_width=2
                )
            ])
            
            fig.update_layout(
                title=f'{num_col.title()} by {cat_col.title()}',
                xaxis_title=cat_col.title(),
                yaxis_title=num_col.title(),
                template=config.theme,
                width=config.width,
                height=config.height,
                showlegend=False
            )
            
            return ChartData(
                chart_type='bar',
                title=f'{num_col.title()} by {cat_col.title()}',
                x_axis=cat_col,
                y_axis=num_col,
                data=[
                    {cat_col: cat, num_col: float(val)} 
                    for cat, val in zip(grouped.index.tolist(), grouped.values.tolist())
                ],
                config=config.__dict__,
                html=pyo.plot(fig, output_type='div', include_plotlyjs=False)
            )
            
        except Exception as e:
            raise Exception(f"Bar chart generation failed: {e}")
    
    def _generate_line_chart(self, df, config: ChartConfig) -> ChartData:
        """Generate a line chart."""
        try:
            import plotly.graph_objects as go
            import plotly.offline as pyo
            
            # Find datetime and numeric columns
            datetime_col = None
            numeric_cols = []
            
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    datetime_col = col
                elif pd.api.types.is_numeric_dtype(df[col]):
                    numeric_cols.append(col)
            
            if datetime_col is None or len(numeric_cols) == 0:
                raise ValueError("Need datetime and numeric columns for line chart")
            
            # Sort by datetime
            df_sorted = df.sort_values(datetime_col)
            
            # Create traces for each numeric column
            traces = []
            for num_col in numeric_cols[:5]:  # Limit to 5 lines
                traces.append(go.Scatter(
                    x=df_sorted[datetime_col],
                    y=df_sorted[num_col],
                    mode='lines',
                    name=num_col.title(),
                    line=dict(width=2)
                ))
            
            fig = go.Figure(data=traces)
            
            fig.update_layout(
                title='Trends Over Time',
                xaxis_title='Time',
                yaxis_title='Values',
                template=config.theme,
                width=config.width,
                height=config.height,
                showlegend=len(numeric_cols) > 1
            )
            
            return ChartData(
                chart_type='line',
                title='Trends Over Time',
                x_axis=datetime_col,
                y_axis=', '.join(numeric_cols),
                data=df_sorted.to_dict('records'),
                config=config.__dict__,
                html=pyo.plot(fig, output_type='div', include_plotlyjs=False)
            )
            
        except Exception as e:
            raise Exception(f"Line chart generation failed: {e}")
    
    def _generate_pie_chart(self, df, config: ChartConfig) -> ChartData:
        """Generate a pie chart."""
        try:
            import plotly.graph_objects as go
            import plotly.offline as pyo
            
            # Get categorical and numeric columns
            cat_col = None
            num_col = None
            
            for col in df.columns:
                if cat_col is None and not pd.api.types.is_numeric_dtype(df[col]):
                    cat_col = col
                elif num_col is None and pd.api.types.is_numeric_dtype(df[col]):
                    num_col = col
                elif cat_col and num_col:
                    break
            
            if cat_col is None or num_col is None:
                raise ValueError("Need both categorical and numeric columns for pie chart")
            
            # Aggregate data
            grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False)
            
            # Limit to top 10 items for readability
            if len(grouped) > 10:
                grouped = grouped.head(10)
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=grouped.index.tolist(),
                    values=grouped.values.tolist(),
                    hole=0.3,
                    marker_colors=[
                        'rgb(55, 83, 109)', 'rgb(255, 127, 80)', 'rgb(78, 205, 196)',
                        'rgb(75, 192, 192)', 'rgb(153, 102, 255)', 'rgb(255, 159, 64)',
                        'rgb(255, 206, 86)', 'rgb(86, 180, 233)', 'rgb(0, 128, 128)',
                        'rgb(240, 128, 128)'
                    ]
                )
            ])
            
            fig.update_layout(
                title=f'{num_col.title()} Distribution by {cat_col.title()}',
                template=config.theme,
                width=config.width,
                height=config.height,
                showlegend=True
            )
            
            return ChartData(
                chart_type='pie',
                title=f'{num_col.title()} Distribution by {cat_col.title()}',
                x_axis=cat_col,
                y_axis=num_col,
                data=[
                    {cat_col: cat, num_col: float(val)} 
                    for cat, val in zip(grouped.index.tolist(), grouped.values.tolist())
                ],
                config=config.__dict__,
                html=pyo.plot(fig, output_type='div', include_plotlyjs=False)
            )
            
        except Exception as e:
            raise Exception(f"Pie chart generation failed: {e}")
    
    def _generate_scatter_chart(self, df, config: ChartConfig) -> ChartData:
        """Generate a scatter plot."""
        try:
            import plotly.graph_objects as go
            import plotly.offline as pyo
            
            # Get numeric columns
            numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
            
            if len(numeric_cols) < 2:
                raise ValueError("Need at least 2 numeric columns for scatter plot")
            
            # Use first two numeric columns
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            
            fig = go.Figure(data=[
                go.Scatter(
                    x=df[x_col],
                    y=df[y_col],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color='rgb(55, 83, 109)',
                        line=dict(width=1, color='white')
                    ),
                    name=f'{y_col} vs {x_col}',
                    text=df.index.tolist() if len(df.index) < 100 else None,
                    hovertemplate='<b>%{text}</b><br>%{x}: %{{x}}<br>%{y}: %{{y}}'
                )
            ])
            
            fig.update_layout(
                title=f'{y_col.title()} vs {x_col.title()}',
                xaxis_title=x_col.title(),
                yaxis_title=y_col.title(),
                template=config.theme,
                width=config.width,
                height=config.height
            )
            
            return ChartData(
                chart_type='scatter',
                title=f'{y_col.title()} vs {x_col.title()}',
                x_axis=x_col,
                y_axis=y_col,
                data=df[[x_col, y_col]].to_dict('records'),
                config=config.__dict__,
                html=pyo.plot(fig, output_type='div', include_plotlyjs=False)
            )
            
        except Exception as e:
            raise Exception(f"Scatter plot generation failed: {e}")
    
    def _generate_histogram_chart(self, df, config: ChartConfig) -> ChartData:
        """Generate a histogram."""
        try:
            import plotly.graph_objects as go
            import plotly.offline as pyo
            import numpy as np
            
            # Get first numeric column
            num_col = None
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    num_col = col
                    break
            
            if num_col is None:
                raise ValueError("Need numeric column for histogram")
            
            # Create histogram data
            data = df[num_col].dropna()
            
            fig = go.Figure(data=[
                go.Histogram(
                    x=data,
                    nbinsx=20,
                    marker_color='rgb(55, 83, 109)',
                    marker_line_color='rgb(255, 255, 255)',
                    marker_line_width=2
                )
            ])
            
            fig.update_layout(
                title=f'Distribution of {num_col.title()}',
                xaxis_title=num_col.title(),
                yaxis_title='Frequency',
                template=config.theme,
                width=config.width,
                height=config.height,
                showlegend=False
            )
            
            return ChartData(
                chart_type='histogram',
                title=f'Distribution of {num_col.title()}',
                x_axis=num_col,
                y_axis='Frequency',
                data=data.to_dict(),
                config=config.__dict__,
                html=pyo.plot(fig, output_type='div', include_plotlyjs=False)
            )
            
        except Exception as e:
            raise Exception(f"Histogram generation failed: {e}")
    
    def _generate_area_chart(self, df, config: ChartConfig) -> ChartData:
        """Generate an area chart."""
        try:
            import plotly.graph_objects as go
            import plotly.offline as pyo
            
            # Similar to line chart but with area fill
            datetime_col = None
            numeric_cols = []
            
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    datetime_col = col
                elif pd.api.types.is_numeric_dtype(df[col]):
                    numeric_cols.append(col)
            
            if datetime_col is None or len(numeric_cols) == 0:
                raise ValueError("Need datetime and numeric columns for area chart")
            
            df_sorted = df.sort_values(datetime_col)
            
            traces = []
            for num_col in numeric_cols[:3]:  # Limit to 3 areas
                traces.append(go.Scatter(
                    x=df_sorted[datetime_col],
                    y=df_sorted[num_col],
                    mode='lines',
                    name=num_col.title(),
                    fill='tonexty',
                    line=dict(width=2),
                    fillcolor=f'rgba(55, 83, 109, 0.3)'
                ))
            
            fig = go.Figure(data=traces)
            
            fig.update_layout(
                title='Cumulative Trends',
                xaxis_title='Time',
                yaxis_title='Values',
                template=config.theme,
                width=config.width,
                height=config.height,
                showlegend=len(numeric_cols) > 1
            )
            
            return ChartData(
                chart_type='area',
                title='Cumulative Trends',
                x_axis=datetime_col,
                y_axis=', '.join(numeric_cols),
                data=df_sorted.to_dict('records'),
                config=config.__dict__,
                html=pyo.plot(fig, output_type='div', include_plotlyjs=False)
            )
            
        except Exception as e:
            raise Exception(f"Area chart generation failed: {e}")
    
    def _generate_box_chart(self, df, config: ChartConfig) -> ChartData:
        """Generate a box plot."""
        try:
            import plotly.graph_objects as go
            import plotly.offline as pyo
            
            # Get numeric columns
            numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
            
            if len(numeric_cols) == 0:
                raise ValueError("Need numeric columns for box plot")
            
            # Create box plots for each numeric column
            traces = []
            for num_col in numeric_cols[:5]:  # Limit to 5 box plots
                data = df[num_col].dropna()
                traces.append(go.Box(
                    y=data,
                    name=num_col.title(),
                    marker_color='rgb(55, 83, 109)',
                    line_color='rgb(255, 255, 255)',
                    line_width=2
                ))
            
            fig = go.Figure(data=traces)
            
            fig.update_layout(
                title='Distribution Summary',
                yaxis_title='Values',
                template=config.theme,
                width=config.width,
                height=config.height,
                showlegend=True
            )
            
            return ChartData(
                chart_type='box',
                title='Distribution Summary',
                x_axis='',
                y_axis=', '.join(numeric_cols),
                data=df[numeric_cols].to_dict('records'),
                config=config.__dict__,
                html=pyo.plot(fig, output_type='div', include_plotlyjs=False)
            )
            
        except Exception as e:
            raise Exception(f"Box plot generation failed: {e}")
    
    def _generate_heatmap_chart(self, df, config: ChartConfig) -> ChartData:
        """Generate a heatmap."""
        try:
            import plotly.graph_objects as go
            import plotly.offline as pyo
            import numpy as np
            
            # For correlation heatmap
            numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
            
            if len(numeric_cols) < 2:
                raise ValueError("Need at least 2 numeric columns for heatmap")
            
            # Calculate correlation matrix
            corr_data = df[numeric_cols].corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_data.values,
                x=corr_data.columns.tolist(),
                y=corr_data.columns.tolist(),
                colorscale='RdYlBu',
                showscale=True
            ))
            
            fig.update_layout(
                title='Correlation Heatmap',
                template=config.theme,
                width=config.width,
                height=config.height,
                xaxis_title='Features',
                yaxis_title='Features'
            )
            
            return ChartData(
                chart_type='heatmap',
                title='Correlation Heatmap',
                x_axis='Features',
                y_axis='Features',
                data=corr_data.to_dict(),
                config=config.__dict__,
                html=pyo.plot(fig, output_type='div', include_plotlyjs=False)
            )
            
        except Exception as e:
            raise Exception(f"Heatmap generation failed: {e}")
    
    def get_supported_chart_types(self) -> List[str]:
        """Get list of supported chart types."""
        return self.supported_chart_types.copy()
    
    def validate_chart_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and provide information about chart data."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            import pandas as pd
            
            # Convert to DataFrame
            if isinstance(data, dict) and 'data' in data:
                df = pd.DataFrame(data['data'])
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame(data)
            
            # Basic validation
            if df.empty:
                validation_result['errors'].append("Data is empty")
                validation_result['is_valid'] = False
            
            # Check data types
            if len(df.columns) == 0:
                validation_result['errors'].append("No columns found in data")
                validation_result['is_valid'] = False
            
            # Check for enough data
            if len(df) < 2:
                validation_result['warnings'].append("Very little data (less than 2 rows)")
                validation_result['suggestions'].append("Consider collecting more data for better visualization")
            
            # Numeric columns check
            numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
            if len(numeric_cols) == 0:
                validation_result['warnings'].append("No numeric columns found")
                validation_result['suggestions'].append("Charts typically work better with numeric data")
            
            # Return data info
            validation_result.update({
                'rows': len(df),
                'columns': list(df.columns),
                'numeric_columns': numeric_cols,
                'data_types': {col: str(df[col].dtype) for col in df.columns}
            })
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Data validation failed: {str(e)}")
        
        return validation_result
