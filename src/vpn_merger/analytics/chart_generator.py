"""
Chart Generator for Analytics Dashboard
=====================================

Generates various types of charts and visualizations for the analytics dashboard.
"""

import logging
from datetime import datetime
from typing import Any

# Optional charting libraries
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from .models import COLOR_SCHEMES, DEFAULT_CHART_HEIGHT, DEFAULT_CHART_WIDTH, ChartData

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generates various types of charts for analytics dashboard."""

    def __init__(self):
        """Initialize the chart generator."""
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available, chart generation disabled")

    def create_line_chart(
        self,
        chart_id: str,
        title: str,
        x_data: list,
        y_data: list,
        x_label: str = "Time",
        y_label: str = "Value",
    ) -> ChartData | None:
        """Create a line chart.

        Args:
            chart_id: Unique chart identifier
            title: Chart title
            x_data: X-axis data
            y_data: Y-axis data
            x_label: X-axis label
            y_label: Y-axis label

        Returns:
            ChartData object or None if Plotly unavailable
        """
        if not PLOTLY_AVAILABLE:
            return None

        try:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode="lines+markers",
                    name=title,
                    line=dict(color=COLOR_SCHEMES["primary"][0]),
                )
            )

            fig.update_layout(
                title=title,
                xaxis_title=x_label,
                yaxis_title=y_label,
                height=DEFAULT_CHART_HEIGHT,
                width=DEFAULT_CHART_WIDTH,
                showlegend=True,
            )

            return ChartData(
                chart_id=chart_id,
                chart_type="line",
                title=title,
                data=fig.to_dict(),
                layout=fig.layout,
                last_updated=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Error creating line chart: {e}")
            return None

    def create_bar_chart(
        self,
        chart_id: str,
        title: str,
        categories: list[str],
        values: list[float],
        color_scheme: str = "primary",
    ) -> ChartData | None:
        """Create a bar chart.

        Args:
            chart_id: Unique chart identifier
            title: Chart title
            categories: Category labels
            values: Values for each category
            color_scheme: Color scheme to use

        Returns:
            ChartData object or None if Plotly unavailable
        """
        if not PLOTLY_AVAILABLE:
            return None

        try:
            colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["primary"])

            fig = go.Figure(
                data=[go.Bar(x=categories, y=values, marker_color=colors[: len(categories)])]
            )

            fig.update_layout(
                title=title,
                height=DEFAULT_CHART_HEIGHT,
                width=DEFAULT_CHART_WIDTH,
                showlegend=False,
            )

            return ChartData(
                chart_id=chart_id,
                chart_type="bar",
                title=title,
                data=fig.to_dict(),
                layout=fig.layout,
                last_updated=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Error creating bar chart: {e}")
            return None

    def create_pie_chart(
        self, chart_id: str, title: str, labels: list[str], values: list[float]
    ) -> ChartData | None:
        """Create a pie chart.

        Args:
            chart_id: Unique chart identifier
            title: Chart title
            labels: Label for each slice
            values: Values for each slice

        Returns:
            ChartData object or None if Plotly unavailable
        """
        if not PLOTLY_AVAILABLE:
            return None

        try:
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3)])

            fig.update_layout(title=title, height=DEFAULT_CHART_HEIGHT, width=DEFAULT_CHART_WIDTH)

            return ChartData(
                chart_id=chart_id,
                chart_type="pie",
                title=title,
                data=fig.to_dict(),
                layout=fig.layout,
                last_updated=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Error creating pie chart: {e}")
            return None

    def create_gauge_chart(
        self, chart_id: str, title: str, value: float, min_val: float = 0, max_val: float = 100
    ) -> ChartData | None:
        """Create a gauge chart.

        Args:
            chart_id: Unique chart identifier
            title: Chart title
            value: Current value
            min_val: Minimum value
            max_val: Maximum value

        Returns:
            ChartData object or None if Plotly unavailable
        """
        if not PLOTLY_AVAILABLE:
            return None

        try:
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=value,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": title},
                    delta={"reference": (max_val + min_val) / 2},
                    gauge={
                        "axis": {"range": [min_val, max_val]},
                        "bar": {"color": COLOR_SCHEMES["primary"][0]},
                        "steps": [
                            {"range": [min_val, max_val * 0.6], "color": "lightgray"},
                            {"range": [max_val * 0.6, max_val * 0.8], "color": "gray"},
                            {"range": [max_val * 0.8, max_val], "color": "darkgray"},
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": max_val * 0.9,
                        },
                    },
                )
            )

            fig.update_layout(height=DEFAULT_CHART_HEIGHT, width=DEFAULT_CHART_WIDTH)

            return ChartData(
                chart_id=chart_id,
                chart_type="gauge",
                title=title,
                data=fig.to_dict(),
                layout=fig.layout,
                last_updated=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Error creating gauge chart: {e}")
            return None

    def create_scatter_plot(
        self,
        chart_id: str,
        title: str,
        x_data: list,
        y_data: list,
        x_label: str = "X",
        y_label: str = "Y",
    ) -> ChartData | None:
        """Create a scatter plot.

        Args:
            chart_id: Unique chart identifier
            title: Chart title
            x_data: X-axis data
            y_data: Y-axis data
            x_label: X-axis label
            y_label: Y-axis label

        Returns:
            ChartData object or None if Plotly unavailable
        """
        if not PLOTLY_AVAILABLE:
            return None

        try:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode="markers",
                    name=title,
                    marker=dict(color=COLOR_SCHEMES["primary"][0], size=8, opacity=0.7),
                )
            )

            fig.update_layout(
                title=title,
                xaxis_title=x_label,
                yaxis_title=y_label,
                height=DEFAULT_CHART_HEIGHT,
                width=DEFAULT_CHART_WIDTH,
                showlegend=True,
            )

            return ChartData(
                chart_id=chart_id,
                chart_type="scatter",
                title=title,
                data=fig.to_dict(),
                layout=fig.layout,
                last_updated=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Error creating scatter plot: {e}")
            return None

    def create_dashboard_layout(
        self, charts: list[ChartData], rows: int = 2, cols: int = 2
    ) -> dict[str, Any] | None:
        """Create a dashboard layout with multiple charts.

        Args:
            charts: List of ChartData objects
            rows: Number of rows in the layout
            cols: Number of columns in the layout

        Returns:
            Dashboard layout dictionary or None if Plotly unavailable
        """
        if not PLOTLY_AVAILABLE or not charts:
            return None

        try:
            fig = make_subplots(
                rows=rows,
                cols=cols,
                subplot_titles=[chart.title for chart in charts[: rows * cols]],
                specs=[[{"secondary_y": False} for _ in range(cols)] for _ in range(rows)],
            )

            for i, chart in enumerate(charts[: rows * cols]):
                row = (i // cols) + 1
                col = (i % cols) + 1

                if chart.chart_type == "line":
                    fig.add_trace(
                        go.Scatter(
                            x=chart.data["data"][0]["x"],
                            y=chart.data["data"][0]["y"],
                            mode="lines+markers",
                            name=chart.title,
                        ),
                        row=row,
                        col=col,
                    )
                elif chart.chart_type == "bar":
                    fig.add_trace(
                        go.Bar(
                            x=chart.data["data"][0]["x"],
                            y=chart.data["data"][0]["y"],
                            name=chart.title,
                        ),
                        row=row,
                        col=col,
                    )

            fig.update_layout(
                height=DEFAULT_CHART_HEIGHT * rows,
                width=DEFAULT_CHART_WIDTH * cols,
                showlegend=True,
            )

            return fig.to_dict()
        except Exception as e:
            logger.error(f"Error creating dashboard layout: {e}")
            return None
