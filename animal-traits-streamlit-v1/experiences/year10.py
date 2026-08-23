from __future__ import annotations

import pandas as pd

from experiences.classroom_shell import render as render_classroom


def render(data: pd.DataFrame) -> None:
    render_classroom("Year 10", data)
