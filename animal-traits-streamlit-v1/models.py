"""Reusable quantitative models for Animal Traits.

Model fitting is separated from plotting and Streamlit UI so it can later be reused
by classroom experiences without duplicating regression logic.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FitResult:
    model_name: str
    equation: str
    slope: float
    intercept: float
    r_squared: float
    n: int
    x_line: np.ndarray
    y_line: np.ndarray


def _transform(values: np.ndarray, use_log: bool) -> np.ndarray:
    return np.log10(values) if use_log else values


def _inverse(values: np.ndarray, use_log: bool) -> np.ndarray:
    return np.power(10.0, values) if use_log else values


def fit_relationship(
    data: pd.DataFrame,
    x: str,
    y: str,
    *,
    log_x: bool = False,
    log_y: bool = False,
) -> FitResult | None:
    """Fit a straight line in the coordinate system selected by the user.

    linear-linear -> y = m x + b
    log-linear    -> y = m log10(x) + b
    linear-log    -> log10(y) = m x + b
    log-log       -> y = 10^b x^m (power law)
    """
    needed = data[[x, y]].copy()
    needed[x] = pd.to_numeric(needed[x], errors="coerce")
    needed[y] = pd.to_numeric(needed[y], errors="coerce")
    needed = needed.dropna()
    if log_x:
        needed = needed[needed[x] > 0]
    if log_y:
        needed = needed[needed[y] > 0]
    if len(needed) < 3:
        return None

    x_raw = needed[x].to_numpy(dtype=float)
    y_raw = needed[y].to_numpy(dtype=float)
    x_fit = _transform(x_raw, log_x)
    y_fit = _transform(y_raw, log_y)

    slope, intercept = np.polyfit(x_fit, y_fit, 1)
    predicted = slope * x_fit + intercept
    residual = np.sum((y_fit - predicted) ** 2)
    total = np.sum((y_fit - np.mean(y_fit)) ** 2)
    r_squared = 1.0 - residual / total if total > 0 else float("nan")

    x_line_fit = np.linspace(x_fit.min(), x_fit.max(), 200)
    y_line_fit = slope * x_line_fit + intercept
    x_line = _inverse(x_line_fit, log_x)
    y_line = _inverse(y_line_fit, log_y)

    if log_x and log_y:
        coefficient = 10 ** intercept
        model_name = "Power-law fit"
        equation = f"y = {coefficient:.3g} × x^{slope:.3f}"
    elif log_x:
        model_name = "Log-x linear fit"
        equation = f"y = {slope:.3f} × log10(x) + {intercept:.3f}"
    elif log_y:
        model_name = "Exponential-style fit"
        equation = f"log10(y) = {slope:.3f} × x + {intercept:.3f}"
    else:
        model_name = "Linear fit"
        equation = f"y = {slope:.3f} × x + {intercept:.3f}"

    return FitResult(
        model_name=model_name,
        equation=equation,
        slope=float(slope),
        intercept=float(intercept),
        r_squared=float(r_squared),
        n=len(needed),
        x_line=x_line,
        y_line=y_line,
    )
