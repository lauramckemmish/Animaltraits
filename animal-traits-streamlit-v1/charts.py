"""Shared Animal Traits chart helpers.

This module owns figure construction. It does not render Streamlit widgets and does
not decide which experience should show a chart.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data import with_common_class_names
from models import FitResult


# -----------------------------------------------------------------------------
# Existing CURIOUS chart helpers. Keep these stable while another experience is
# being developed.
# -----------------------------------------------------------------------------

def histogram(data: pd.DataFrame, field: str, log_x: bool = False, bins: int = 25):
    values = pd.to_numeric(data[field], errors="coerce")
    plot_data = pd.DataFrame({field: values}).dropna()
    plot_data = plot_data[plot_data[field] > 0]

    if log_x and not plot_data.empty:
        low = np.log10(plot_data[field].min())
        high = np.log10(plot_data[field].max())
        edges = np.logspace(low, high, bins + 1)
        counts, edges = np.histogram(plot_data[field], bins=edges)
        centres = np.sqrt(edges[:-1] * edges[1:])
        fig = go.Figure(go.Bar(x=centres, y=counts, width=np.diff(edges)))
        fig.update_xaxes(type="log", title=field)
        fig.update_yaxes(title="Number of animals")
        fig.update_layout(title=f"Distribution of {field} · logarithmic scale", bargap=0.02)
        return fig

    fig = px.histogram(plot_data, x=field, nbins=bins, title=f"Distribution of {field} · linear scale")
    fig.update_yaxes(title="Number of animals")
    return fig


def class_comparison(data: pd.DataFrame, field: str = "body mass (kg)", graph_type: str = "Individual points", log_y: bool = True):
    plot_data = with_common_class_names(data)
    plot_data[field] = pd.to_numeric(plot_data[field], errors="coerce")
    plot_data = plot_data.dropna(subset=[field, "Animal class"])
    plot_data = plot_data[plot_data[field] > 0]

    if graph_type == "Box plot":
        fig = px.box(plot_data, x="Animal class", y=field, points="outliers")
    elif graph_type == "Violin plot":
        fig = px.violin(plot_data, x="Animal class", y=field, box=True, points=False)
    elif graph_type == "Average ± spread":
        summary = plot_data.groupby("Animal class", as_index=False)[field].agg(["mean", "std"]).reset_index()
        fig = go.Figure(
            go.Scatter(
                x=summary["Animal class"],
                y=summary["mean"],
                error_y=dict(type="data", array=summary["std"], visible=True),
                mode="markers",
            )
        )
    else:
        fig = px.strip(plot_data, x="Animal class", y=field)

    fig.update_layout(title="Body mass by animal class", xaxis_title="Animal class", yaxis_title=field)
    if log_y:
        fig.update_yaxes(type="log")
    return fig


def body_brain_scatter(data: pd.DataFrame):
    plot_data = with_common_class_names(data)
    needed = ["body mass (kg)", "brain size (kg)"]
    for column in needed:
        plot_data[column] = pd.to_numeric(plot_data[column], errors="coerce")
    plot_data = plot_data.dropna(subset=[*needed, "Animal class"])
    plot_data = plot_data[(plot_data[needed[0]] > 0) & (plot_data[needed[1]] > 0)]

    fig = px.scatter(
        plot_data,
        x="body mass (kg)",
        y="brain size (kg)",
        color="Animal class",
        hover_name="common name",
        hover_data=["species"],
        log_x=True,
        log_y=True,
        title="Body mass vs brain size · log–log scale",
    )
    fig.update_traces(marker=dict(size=7, opacity=0.8))
    return fig


# -----------------------------------------------------------------------------
# Data Exploration Playground charts.
# -----------------------------------------------------------------------------

def playground_histogram(
    data: pd.DataFrame,
    field: str,
    label: str,
    *,
    bins: int = 25,
    log_x: bool = False,
):
    plot_data = data[[field]].copy()
    plot_data[field] = pd.to_numeric(plot_data[field], errors="coerce")
    plot_data = plot_data.dropna()
    if log_x:
        plot_data = plot_data[plot_data[field] > 0]

    if log_x and not plot_data.empty:
        low = np.log10(plot_data[field].min())
        high = np.log10(plot_data[field].max())
        edges = np.logspace(low, high, bins + 1)
        counts, edges = np.histogram(plot_data[field], bins=edges)
        centres = np.sqrt(edges[:-1] * edges[1:])
        fig = go.Figure(go.Bar(x=centres, y=counts, width=np.diff(edges)))
        fig.update_xaxes(type="log", title=label)
        fig.update_yaxes(title="Number of animal records")
        fig.update_layout(title=f"Distribution of {label} · logarithmic scale", bargap=0.02)
        return fig, len(plot_data)

    fig = px.histogram(plot_data, x=field, nbins=bins, title=f"Distribution of {label}")
    fig.update_layout(xaxis_title=label, yaxis_title="Number of animal records")
    return fig, len(plot_data)


def playground_two_variable_scatter(
    data: pd.DataFrame,
    x: str,
    y: str,
    x_label: str,
    y_label: str,
    *,
    log_x: bool = False,
    log_y: bool = False,
    fit: FitResult | None = None,
):
    positive = [field for field, use_log in [(x, log_x), (y, log_y)] if use_log]
    plot_data = data.copy()
    for field in [x, y]:
        plot_data[field] = pd.to_numeric(plot_data[field], errors="coerce")
    plot_data = plot_data.dropna(subset=[x, y])
    for field in positive:
        plot_data = plot_data[plot_data[field] > 0]

    hover_data = [field for field in ["species", "Animal class"] if field in plot_data.columns]
    hover_name = "common name" if "common name" in plot_data.columns else None
    fig = px.scatter(
        plot_data,
        x=x,
        y=y,
        hover_name=hover_name,
        hover_data=hover_data,
        title=f"{y_label} and {x_label}",
    )
    fig.update_layout(xaxis_title=x_label, yaxis_title=y_label)
    fig.update_traces(marker=dict(size=7, opacity=0.75))
    if log_x:
        fig.update_xaxes(type="log")
    if log_y:
        fig.update_yaxes(type="log")

    if fit is not None:
        fig.add_trace(
            go.Scatter(
                x=fit.x_line,
                y=fit.y_line,
                mode="lines",
                name=fit.model_name,
            )
        )
    return fig, len(plot_data)


def playground_three_variable_scatter(
    data: pd.DataFrame,
    x: str,
    y: str,
    colour: str,
    x_label: str,
    y_label: str,
    colour_label: str,
    *,
    log_x: bool = False,
    log_y: bool = False,
):
    plot_data = data.copy()
    numeric_fields = [x, y]
    if colour != "Animal class":
        numeric_fields.append(colour)
    for field in numeric_fields:
        plot_data[field] = pd.to_numeric(plot_data[field], errors="coerce")

    plot_data = plot_data.dropna(subset=[x, y, colour])
    if log_x:
        plot_data = plot_data[plot_data[x] > 0]
    if log_y:
        plot_data = plot_data[plot_data[y] > 0]

    hover_data = [field for field in ["species", "Animal class"] if field in plot_data.columns and field != colour]
    hover_name = "common name" if "common name" in plot_data.columns else None
    fig = px.scatter(
        plot_data,
        x=x,
        y=y,
        color=colour,
        hover_name=hover_name,
        hover_data=hover_data,
        title=f"{y_label} and {x_label}, coloured by {colour_label}",
    )
    fig.update_layout(xaxis_title=x_label, yaxis_title=y_label, legend_title=colour_label)
    fig.update_traces(marker=dict(size=7, opacity=0.8))
    if log_x:
        fig.update_xaxes(type="log")
    if log_y:
        fig.update_yaxes(type="log")
    return fig, len(plot_data)
