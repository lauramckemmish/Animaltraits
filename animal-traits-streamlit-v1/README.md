# Animal Traits Streamlit — Version 1

A multi-experience Streamlit app for exploring the Animal Traits teaching dataset.

## Experiences

- CURIOUS — guided workshop (existing first-pass content)
- Year 8 — two-lesson route/shell
- Year 10 — two-lesson route/shell
- Data Exploration Playground — implemented V1
- Find Your Animal — route/placeholder for later development

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Development rule

Build one experience at a time. See `ARCHITECTURE.md` before making changes.

## Classroom concurrency release readiness

Before release, run a lightweight browser smoke test for **1 → 20 → 30**
independent learner sessions. It reaches **Data Exploration Playground → Two
variables** through the normal learner sidebar, then synchronizes three toggles
of the existing **Show best-fit model** control. This is a real data-science
interaction that recalculates the displayed model, making it representative of
a facilitated whole-class burst without adding a test-only pathway.

```bash
python tools/classroom_concurrency.py
```

The generic runner owns independent sessions, error detection and shutdown;
`classroom_smoke_adapter.py` owns this repository's learner route and
interaction. It is a release-readiness smoke test, not a profiling or load-test
framework: if the 30-session level passes comfortably, record the result and
stop. If it fails or is marginal, reproduce the smallest failing level before
investigating further.
