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
# Existing CURIOUS chart helpers.
# -----------------------------------------------------------------------------

_SUPERSCRIPT_TRANSLATION = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def _power_of_ten_label(exponent: int) -> str:
    """Return a student-facing power-of-ten label such as 10⁻³."""
    return f"10{str(exponent).translate(_SUPERSCRIPT_TRANSLATION)}"


def _log_tick_label(exponent: int) -> str:
    """Use familiar decimals for readable powers and powers for extreme values."""
    if -3 <= exponent <= 3:
        return f"{10 ** exponent:,}"
    return _power_of_ten_label(exponent)


def _scientific_log_ticks(values: pd.Series, max_ticks: int = 9) -> tuple[list[float], list[str]]:
    """Return readable ticks at every power of ten covering positive values.

    Plotly's automatic log-axis labels can switch to engineering prefixes such as
    µ or n. CURIOUS has already introduced powers of ten, so these axes use that
    notation consistently instead. ``max_ticks`` remains for compatibility but
    does not thin the decades: students need every order of magnitude to be visible.
    """
    numeric = pd.to_numeric(values, errors="coerce")
    numeric = numeric[np.isfinite(numeric) & (numeric > 0)]
    if numeric.empty:
        return [], []

    low = int(np.floor(np.log10(numeric.min())))
    high = int(np.ceil(np.log10(numeric.max())))
    exponents = list(range(low, high + 1))

    tick_values = [10.0 ** exponent for exponent in exponents]
    tick_text = [_log_tick_label(exponent) for exponent in exponents]
    return tick_values, tick_text


def _apply_scientific_log_axis(fig, axis: str, values: pd.Series, title: str) -> None:
    """Apply powers-of-ten tick labels to one Plotly logarithmic axis."""
    tick_values, tick_text = _scientific_log_ticks(values)
    axis_settings = dict(
        type="log",
        title=title,
        tickmode="array",
        tickvals=tick_values,
        ticktext=tick_text,
        ticks="outside",
        ticklen=6,
        tickwidth=1,
        tickcolor="rgba(55, 65, 81, 0.85)",
        showgrid=True,
        gridcolor="rgba(55, 65, 81, 0.28)",
        gridwidth=1,
    )
    if axis == "x":
        fig.update_xaxes(**axis_settings)
    elif axis == "y":
        fig.update_yaxes(**axis_settings)
    else:
        raise ValueError("axis must be 'x' or 'y'")


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
        _apply_scientific_log_axis(fig, "x", plot_data[field], field)
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


def body_brain_scatter(
    data: pd.DataFrame,
    *,
    log_x: bool = False,
    log_y: bool = False,
    colour_by_class: bool = False,
    fit: FitResult | None = None,
):
    """Plot body mass against brain size for CURIOUS.

    Axis scale and animal-class colouring are controlled by the calling experience so
    the same underlying relationship can be revealed progressively without duplicating
    chart logic.
    """
    plot_data = with_common_class_names(data)
    x_field = "body mass (kg)"
    y_field = "brain size (kg)"

    for column in [x_field, y_field]:
        plot_data[column] = pd.to_numeric(plot_data[column], errors="coerce")

    required = [x_field, y_field]
    if colour_by_class:
        required.append("Animal class")
    plot_data = plot_data.dropna(subset=required)

    # Plotly cannot display non-positive values on logarithmic axes.
    if log_x:
        plot_data = plot_data[plot_data[x_field] > 0]
    if log_y:
        plot_data = plot_data[plot_data[y_field] > 0]

    common_name = "common name" if "common name" in plot_data.columns else None
    hover_fields = [field for field in ["species"] if field in plot_data.columns]

    if log_x and log_y:
        scale_label = "log–log scale"
    elif log_x:
        scale_label = "logarithmic body-mass axis"
    elif log_y:
        scale_label = "logarithmic brain-size axis"
    else:
        scale_label = "linear scales"

    fig = px.scatter(
        plot_data,
        x=x_field,
        y=y_field,
        color="Animal class" if colour_by_class else None,
        hover_name=common_name,
        hover_data=hover_fields,
        log_x=log_x,
        log_y=log_y,
        title=f"Body mass vs brain size · {scale_label}",
    )
    fig.update_layout(
        xaxis_title="Body mass (kg)",
        yaxis_title="Brain size (kg)",
        legend_title="Animal class" if colour_by_class else None,
    )
    if log_x:
        _apply_scientific_log_axis(fig, "x", plot_data[x_field], "Body mass (kg)")
    if log_y:
        _apply_scientific_log_axis(fig, "y", plot_data[y_field], "Brain size (kg)")
    fig.update_traces(marker=dict(size=7, opacity=0.78))
    if fit is not None:
        fig.add_trace(
            go.Scatter(
                x=fit.x_line,
                y=fit.y_line,
                mode="lines",
                name=fit.model_name,
                line=dict(color="#1f2937", width=3),
            )
        )
    return fig


def body_brain_representative_scatter(
    representative_data: pd.DataFrame,
    *,
    title: str = "A few familiar animals",
):
    """Plot labelled representative body/brain points for orientation."""
    x_field = "body mass (kg)"
    y_field = "brain size (kg)"
    plot_data = representative_data.copy()
    plot_data[x_field] = pd.to_numeric(plot_data[x_field], errors="coerce")
    plot_data[y_field] = pd.to_numeric(plot_data[y_field], errors="coerce")
    plot_data = plot_data.dropna(subset=[x_field, y_field, "Animal"])
    scientific_names = plot_data.get("Scientific name", pd.Series("", index=plot_data.index)).astype(str)
    fig = go.Figure(
        go.Scatter(
            x=plot_data[x_field],
            y=plot_data[y_field],
            mode="markers+text",
            text=plot_data["Animal"],
            textposition="top center",
            name="Selected familiar animals",
            marker=dict(size=11, color="#2563eb", line=dict(color="#1e3a8a", width=1)),
            customdata=np.column_stack([plot_data["Animal"].astype(str), scientific_names]),
            hovertemplate=(
                "Animal: %{customdata[0]}<br>"
                "Scientific name: %{customdata[1]}<br>"
                "Body mass: %{x}<br>Brain mass: %{y}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Body mass (kg)",
        yaxis_title="Brain size (kg)",
        showlegend=False,
    )
    fig.update_xaxes(type="linear")
    fig.update_yaxes(type="linear")
    return fig


def body_brain_highlight_scatter(
    data: pd.DataFrame,
    selected_data: pd.DataFrame,
    *,
    log_x: bool = False,
    log_y: bool = False,
    selected_label: str = "Selected animal",
    title: str | None = None,
):
    """Plot all body/brain records with selected records highlighted.

    ``selected_data`` is supplied by the calling experience; this helper does not
    perform search or filtering. Selected rows remain at record level, so repeated
    measurements and their variation are preserved in the highlighted trace.
    """
    x_field = "body mass (kg)"
    y_field = "brain size (kg)"

    plot_data = with_common_class_names(data).copy()
    selected_plot_data = selected_data.copy()

    for frame in [plot_data, selected_plot_data]:
        x_column = next((column for column in [x_field, "Body mass (kg)"] if column in frame), None)
        y_column = next(
            (column for column in [y_field, "Brain size (kg)", "Brain mass (kg)"] if column in frame),
            None,
        )
        if x_column is not None and x_column != x_field:
            frame[x_field] = frame[x_column]
        if y_column is not None and y_column != y_field:
            frame[y_field] = frame[y_column]
        frame[x_field] = pd.to_numeric(frame.get(x_field), errors="coerce")
        frame[y_field] = pd.to_numeric(frame.get(y_field), errors="coerce")

    plot_data = plot_data.dropna(subset=[x_field, y_field])
    selected_plot_data = selected_plot_data.dropna(subset=[x_field, y_field])
    if log_x:
        plot_data = plot_data[plot_data[x_field] > 0]
        selected_plot_data = selected_plot_data[selected_plot_data[x_field] > 0]
    if log_y:
        plot_data = plot_data[plot_data[y_field] > 0]
        selected_plot_data = selected_plot_data[selected_plot_data[y_field] > 0]

    if title is None:
        title = f"Body mass vs brain size · {selected_label}"
    fig = go.Figure()
    if not plot_data.empty:
        fig.add_trace(
            go.Scatter(
                x=plot_data[x_field],
                y=plot_data[y_field],
                mode="markers",
                name="All animals (context)",
                marker=dict(size=6, color="rgba(107, 114, 128, 0.16)"),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    def _hover_column(frame: pd.DataFrame, candidates: list[str]) -> pd.Series:
        for column in candidates:
            if column in frame:
                return frame[column].fillna("").astype(str)
        return pd.Series("", index=frame.index, dtype="string")

    common_names = _hover_column(selected_plot_data, ["common name", "Common name"])
    scientific_names = _hover_column(selected_plot_data, ["species", "Scientific name"])
    customdata = np.column_stack([common_names.to_numpy(), scientific_names.to_numpy()])
    fig.add_trace(
        go.Scatter(
            x=selected_plot_data[x_field],
            y=selected_plot_data[y_field],
            mode="markers",
            name=selected_label,
            marker=dict(size=11, color="#d95f02", line=dict(color="#7f2704", width=1)),
            customdata=customdata,
            hovertemplate=(
                "Common name: %{customdata[0]}<br>"
                "Scientific name: %{customdata[1]}<br>"
                "Body mass: %{x}<br>Brain mass: %{y}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Body mass (kg)",
        yaxis_title="Brain size (kg)",
        legend_title="Highlighted records",
    )
    axis_values = plot_data if not plot_data.empty else selected_plot_data
    if log_x:
        _apply_scientific_log_axis(fig, "x", axis_values[x_field], "Body mass (kg)")
    else:
        fig.update_xaxes(type="linear")
    if log_y:
        _apply_scientific_log_axis(fig, "y", axis_values[y_field], "Brain size (kg)")
    else:
        fig.update_yaxes(type="linear")
    return fig


def body_brain_class_sample_size_bar(
    data: pd.DataFrame,
    *,
    title: str = "Usable body-and-brain records by animal class",
):
    """Count usable body/brain records for each student-facing animal class."""
    plot_data = with_common_class_names(data).copy()
    for column in ["body mass (kg)", "brain size (kg)"]:
        plot_data[column] = pd.to_numeric(plot_data[column], errors="coerce")
    plot_data = plot_data.dropna(subset=["Animal class", "body mass (kg)", "brain size (kg)"])
    plot_data = plot_data[
        (plot_data["body mass (kg)"] > 0) & (plot_data["brain size (kg)"] > 0)
    ]
    counts = (
        plot_data.groupby("Animal class", as_index=False)
        .size()
        .rename(columns={"size": "Usable records"})
        .sort_values("Usable records", ascending=True)
    )
    fig = px.bar(
        counts,
        x="Usable records",
        y="Animal class",
        orientation="h",
        text="Usable records",
        title=title,
    )
    fig.update_traces(marker_color="#4c78a8", textposition="outside", cliponaxis=False)
    fig.update_layout(
        xaxis_title="Number of usable records",
        yaxis_title="Animal class",
        showlegend=False,
    )
    return fig



def body_brain_class_fit_scatter(
    data: pd.DataFrame,
    *,
    highlighted_classes: list[str],
    fits: dict[str, FitResult] | None = None,
    highlighted_records: pd.DataFrame | None = None,
    highlighted_label: str = "Selected records",
    log_x: bool = True,
    log_y: bool = True,
    show_background: bool = True,
    title: str | None = None,
):
    """Compare selected animal classes against the full body-mass/brain-size dataset.

    All animals can remain as a faint background for context. Selected classes are
    drawn more clearly, and optional per-class fitted models are overlaid using the
    same colour as the corresponding class.

    Model fitting remains the responsibility of ``models.py`` / the calling
    experience; this helper only constructs the figure.
    """
    plot_data = with_common_class_names(data)
    x_field = "body mass (kg)"
    y_field = "brain size (kg)"

    for column in [x_field, y_field]:
        plot_data[column] = pd.to_numeric(plot_data[column], errors="coerce")

    plot_data = plot_data.dropna(subset=[x_field, y_field, "Animal class"])

    if log_x:
        plot_data = plot_data[plot_data[x_field] > 0]
    if log_y:
        plot_data = plot_data[plot_data[y_field] > 0]

    available_classes = sorted(plot_data["Animal class"].dropna().unique().tolist())
    selected_classes = [
        class_name
        for class_name in highlighted_classes
        if class_name in available_classes
    ]

    # Build a stable class-colour mapping from all classes in the dataset. This means
    # Mammal, for example, keeps the same colour in a Mammal-only view and in a
    # Mammal + Reptile comparison.
    palette = px.colors.qualitative.Plotly
    class_colours = {
        class_name: palette[index % len(palette)]
        for index, class_name in enumerate(available_classes)
    }

    fig = go.Figure()

    if show_background and not plot_data.empty:
        fig.add_trace(
            go.Scatter(
                x=plot_data[x_field],
                y=plot_data[y_field],
                mode="markers",
                name="All animals (context)",
                marker=dict(size=6, color="rgba(107, 114, 128, 0.14)"),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    common_name = "common name" if "common name" in plot_data.columns else None
    hover_fields = [field for field in ["species"] if field in plot_data.columns]

    for class_name in selected_classes:
        class_data = plot_data[plot_data["Animal class"] == class_name]
        colour = class_colours[class_name]

        class_figure = px.scatter(
            class_data,
            x=x_field,
            y=y_field,
            hover_name=common_name,
            hover_data=hover_fields,
            color_discrete_sequence=[colour],
        )
        if class_figure.data:
            class_trace = class_figure.data[0]
            class_trace.name = class_name
            class_trace.legendgroup = class_name
            class_trace.showlegend = True
            class_trace.marker.update(size=8, opacity=0.48)
            fig.add_trace(class_trace)

        fit = (fits or {}).get(class_name)
        if fit is not None:
            fig.add_trace(
                go.Scatter(
                    x=fit.x_line,
                    y=fit.y_line,
                    mode="lines",
                    name=f"{class_name} fit",
                    showlegend=False,
                    legendgroup=class_name,
                    line=dict(color="#1f2937", width=5),
                    hoverinfo="skip",
                )
            )

    if highlighted_records is not None:
        selected_data = highlighted_records.copy()
        for column in [x_field, y_field]:
            selected_data[column] = pd.to_numeric(selected_data[column], errors="coerce")
        selected_data = selected_data.dropna(subset=[x_field, y_field])
        if log_x:
            selected_data = selected_data[selected_data[x_field] > 0]
        if log_y:
            selected_data = selected_data[selected_data[y_field] > 0]

        def _selected_hover_column(candidates: list[str]) -> pd.Series:
            for column in candidates:
                if column in selected_data:
                    return selected_data[column].fillna("").astype(str)
            return pd.Series("", index=selected_data.index, dtype="string")

        common_names = _selected_hover_column(["common name", "Common name"])
        scientific_names = _selected_hover_column(["species", "Scientific name"])
        fig.add_trace(
            go.Scatter(
                x=selected_data[x_field],
                y=selected_data[y_field],
                mode="markers",
                name=highlighted_label,
                showlegend=True,
                marker=dict(size=12, color="#d95f02", line=dict(color="#7f2704", width=1.5)),
                customdata=np.column_stack([common_names.to_numpy(), scientific_names.to_numpy()]),
                hovertemplate=(
                    "Common name: %{customdata[0]}<br>"
                    "Scientific name: %{customdata[1]}<br>"
                    "Body mass: %{x}<br>Brain mass: %{y}<extra></extra>"
                ),
            )
        )

    if title is None:
        comparison_label = " + ".join(selected_classes) if selected_classes else "Selected classes"
        title = f"Body mass vs brain size · {comparison_label}"

    fig.update_layout(
        title=title,
        xaxis_title="Body mass (kg)",
        yaxis_title="Brain size (kg)",
        legend_title="Animal class",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            title=None,
        ),
    )
    if log_x:
        _apply_scientific_log_axis(fig, "x", plot_data[x_field], "Body mass (kg)")
    else:
        fig.update_xaxes(type="linear")
    if log_y:
        _apply_scientific_log_axis(fig, "y", plot_data[y_field], "Brain size (kg)")
    else:
        fig.update_yaxes(type="linear")
    return fig


# -----------------------------------------------------------------------------
# Data Exploration Playground charts. Unchanged by the CURIOUS refinement.
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
