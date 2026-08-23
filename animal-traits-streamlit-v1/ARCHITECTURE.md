# Animal Traits V1 architecture contract

The app is developed **one experience at a time**. A change to one experience should not trigger opportunistic redesign of another experience.

## Layer responsibilities

### `data.py` — dataset knowledge
Owns:
- loading and light preparation of the Animal Traits dataset
- field names and student-facing variable metadata
- animal-class labels
- reusable filters and row preparation

Does not own:
- Streamlit page layout
- lesson wording
- Plotly figures
- regression/model fitting

### `models.py` — quantitative modelling
Owns:
- reusable fitting/model calculations
- model equations and fit statistics
- coordinates required to display a fitted model

Does not own:
- Streamlit controls
- decisions about when a student should fit a model
- Plotly figure construction

### `charts.py` — visualisation
Owns:
- Plotly figure construction
- axis scale presentation
- optional visual overlay of a model result supplied by `models.py`

Does not own:
- Streamlit controls
- session state
- lesson sequence
- dataset loading

### `experiences/*.py` — interface and pedagogy
Each experience owns:
- its Streamlit controls
- its layout and wording
- its learning sequence
- decisions about which shared data/chart/model functions to call

An experience should not contain reusable regression mathematics or general dataset-cleaning code.

## V1 experience boundaries

1. **CURIOUS** — existing guided workshop. Do not change while implementing another experience.
2. **Year 8** — route/shell only until explicitly selected for development.
3. **Year 10** — route/shell only until explicitly selected for development.
4. **Data Exploration Playground** — current implementation slice. Uses one-, two- and three-variable exploration, an animal-class-only filter, and optional fitting in the two-variable view.
5. **Find Your Animal** — separate route only. Do not implement until it becomes the active slice.

## Change discipline

For each development pass:
1. Name exactly one active experience.
2. Change that experience file plus only the shared modules genuinely required by it.
3. Do not rewrite other experience files for consistency or style.
4. Preserve shared function interfaces already used by other experiences unless a deliberate shared refactor is the task.
5. Run syntax/tests and manually smoke-test the active experience plus navigation before starting the next experience.
6. Stop after the bounded slice and review it in the deployed Streamlit app.

## Current slice: Data Exploration Playground V1

The playground mirrors the Exoplanets exploratory mental model:
- **One variable:** distribution/histogram
- **Two variables:** scatter plot, independent log-axis choices, optional best-fit model
- **Three variables:** x + y + colour variable
- **Filter:** animal class only, applied across the playground

Fitting is deliberately stronger here than in Exoplanets. It is implemented in `models.py` so it can later be reused in Year 10 or other experiences without coupling those experiences to the playground UI.
