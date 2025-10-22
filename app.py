
import io
import math
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import streamlit as st

st.set_page_config(page_title="Yr8 Animal Traits – Black Box", layout="wide")

st.title("Yr8 Animal Traits – Black Box")
st.write("A student-friendly app to explore a real dataset of animal traits, look for patterns, fit a simple model, and record observations. No code is shown.")

# --- Data loading ---
DEFAULT_CSV = "observations.csv"
data = None

data_src = st.sidebar.selectbox("Data source", ["Use bundled observations.csv", "Upload CSV"])
if data_src == "Use bundled observations.csv":
    if Path(DEFAULT_CSV).exists():
        try:
            data = pd.read_csv(DEFAULT_CSV)
        except Exception as e:
            st.error(f"Could not read {DEFAULT_CSV}: {e}")
    else:
        st.warning("observations.csv not found in the app folder. Please upload a CSV instead.")
else:
    up = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])
    if up is not None:
        try:
            data = pd.read_csv(up)
        except Exception as e:
            st.error(f"Could not read uploaded CSV: {e}")

if data is None:
    st.stop()

st.subheader("1) Explore the dataset")
st.caption("Use the tools below to inspect the table and choose the columns to focus on.")
with st.expander("Preview data", expanded=True):
    st.dataframe(data.head(20), use_container_width=True)

# Identify numeric columns for plotting/model
num_cols = [c for c in data.columns if pd.api.types.is_numeric_dtype(data[c])]
cat_cols = [c for c in data.columns if pd.api.types.is_string_dtype(data[c]) or pd.api.types.is_categorical_dtype(data[c])]

col_select = st.multiselect("Pick columns to include in the working table", options=list(data.columns), default=list(num_cols)[:5] or list(data.columns)[:5])
work_df = data[col_select].copy()
st.dataframe(work_df.head(20), use_container_width=True)

st.subheader("2) Visualise relationships")
st.caption("Choose two numeric variables. Try different axis scales and look for linear, curved, or clustered patterns.")
if len(num_cols) < 2:
    st.info("Need at least two numeric columns to plot a relationship.")
else:
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        xcol = st.selectbox("X variable", options=num_cols, index=0)
    with c2:
        ycol = st.selectbox("Y variable", options=[c for c in num_cols if c != xcol], index=min(1, len(num_cols)-1))
    with c3:
        color_col = st.selectbox("Colour by (optional)", options=[None] + cat_cols + [c for c in num_cols if c not in [xcol, ycol]], index=0)

    scale = st.radio("Axis scaling", options=["Linear", "Log X", "Log Y", "Log-Log"], horizontal=True)

    plot_df = work_df[[xcol, ycol]].dropna().copy()
    if scale in ["Log X", "Log-Log"]:
        plot_df = plot_df[plot_df[xcol] > 0]
    if scale in ["Log Y", "Log-Log"]:
        plot_df = plot_df[plot_df[ycol] > 0]

    fig = px.scatter(work_df if color_col else plot_df, x=xcol, y=ycol, color=color_col if color_col else None, opacity=0.8)
    if scale in ["Log X", "Log-Log"]:
        fig.update_xaxes(type="log")
    if scale in ["Log Y", "Log-Log"]:
        fig.update_yaxes(type="log")
    fig.update_layout(height=520, margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("> Write an observation about the shape or pattern you see.")
    obs1 = st.text_area("Observation", placeholder="Describe patterns: linear, curved, clusters, outliers, proportional changes, etc.", key="obs1")

st.subheader("3) Fit a simple linear model and check the fit")
st.caption("This fits y = a + b·x on the chosen variables. If you chose log scales, the model still fits the raw values shown above.")
if len(num_cols) >= 2:
    # Prepare data for linear regression on raw values
    df_fit = work_df[[xcol, ycol]].dropna().copy()
    if not df_fit.empty:
        X = df_fit[[xcol]].values.reshape(-1, 1)
        y = df_fit[ycol].values.reshape(-1, 1)
        model = LinearRegression()
        model.fit(X, y)
        a = float(model.intercept_[0])
        b = float(model.coef_[0][0])
        y_pred = model.predict(X).ravel()
        # R^2
        r2 = float(model.score(X, y))

        st.write(f"Fitted model: **{ycol} = {a:.3g} + {b:.3g} × {xcol}**")
        st.write(f"R² = {r2:.3f}")

        # Overlay line
        xs = np.linspace(df_fit[xcol].min(), df_fit[xcol].max(), 100)
        ys = a + b * xs
        line = go.Scatter(x=xs, y=ys, mode="lines", name="Linear fit")
        fig2 = px.scatter(df_fit, x=xcol, y=ycol, opacity=0.75)
        fig2.add_trace(line)
        fig2.update_layout(height=520, margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("> Does a straight line describe the relationship well or poorly?")
        obs2 = st.text_area("Comment on the fit", placeholder="Consider R², residual spread, outliers, curvature, or distinct groups.", key="obs2")

        st.subheader("4) Make predictions with your fitted model")
        st.caption("Enter one or more X values to predict Y using the model above.")
        pred_x = st.text_input(f"Values of {xcol} (comma separated)", value="")
        if pred_x.strip():
            try:
                xs_in = np.array([float(v) for v in pred_x.split(",")])
                ys_out = a + b * xs_in
                pred_df = pd.DataFrame({xcol: xs_in, f"pred_{ycol}": ys_out})
                st.dataframe(pred_df, use_container_width=True)
                st.download_button("Download predictions as CSV", pred_df.to_csv(index=False).encode("utf-8"), file_name="predictions.csv", mime="text/csv")
            except Exception as e:
                st.error(f"Could not parse input values: {e}")
    else:
        st.info("Not enough data to fit a model.")

st.subheader("5) Save your observations")
st.caption("Download your notes as a CSV to submit or keep.")
student_name = st.text_input("Your name or initials", "")
notes = {
    "name": student_name,
    "x_variable": xcol if len(num_cols) >= 2 else "",
    "y_variable": ycol if len(num_cols) >= 2 else "",
    "obs_plot": st.session_state.get("obs1", ""),
    "obs_fit": st.session_state.get("obs2", ""),
}
notes_df = pd.DataFrame([notes])
st.download_button("Download my observations (CSV)", notes_df.to_csv(index=False).encode("utf-8"), file_name="observations_notes.csv", mime="text/csv")

st.caption("Tip for teachers: ship an 'observations.csv' with the class dataset, or instruct students to upload one. The app hides all code and focuses on exploration, simple modelling, and note taking.")    
