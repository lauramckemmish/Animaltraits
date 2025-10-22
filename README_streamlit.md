
# Yr8 Animal Traits – Black Box (Streamlit App, no code shown)

This Streamlit app replicates the classroom workflow from the notebook without showing code.
Students can:
- load the dataset,
- explore columns and preview a table,
- build a scatter plot with optional colour grouping and axis scaling,
- fit a simple linear model (y = a + b·x),
- make predictions,
- record and download their observations.

## Files
- `app.py` – the Streamlit app
- `observations.csv` – optional dataset file shipped with the app
- `requirements.txt` – dependencies

## Local run
```bash
pip install -r requirements.txt
streamlit run app.py
```
