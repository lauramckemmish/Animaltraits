# Animal Traits Streamlit — Repository Guidelines

## Purpose

This repository contains the Animal Traits educational data-science resource.

It is a topic-specific learning application built around real animal-traits data. Its scientific question, dataset, pedagogy, learner journey, provenance and experience-specific decisions belong to this repository.

Work in the order:

**learning → scientific/data experience → interaction → software**

Technology supports the learning experience rather than determining it.

Do not redesign pedagogy merely to make the code more generic or reusable.

## Repository layout

The application lives in `animal-traits-streamlit-v1/`.

Run development commands from that directory.

Important layers:

- `app.py` — application shell and routing;
- `experiences/` — local learning sequences, learner-facing wording, Streamlit controls and experience-specific pedagogy;
- `data.py` — shared data loading and preparation;
- `models.py` — quantitative modelling;
- `charts.py` — reusable visualisation logic;
- `ui_helpers.py` — reusable interface components;
- `data/` — Animal Traits datasets;
- `assets/` — images, video and media attribution;
- `scripts/` — one-off data utilities.

Read `animal-traits-streamlit-v1/ARCHITECTURE.md` before structural changes.

## Current experience structure

Currently enabled:

- CURIOUS — guided workshop, “Who’s the Smartest Animal?”
- Data Exploration Playground

Currently defined but disabled:

- Year 8
- Year 10
- Find Your Animal

Do not enable, remove, merge or substantially redesign experiences unless the task explicitly requires it.

Treat mature existing experiences as working reference implementations, not as automatic templates for other experiences.

## Local pedagogy is authoritative

Animal Traits owns its own:

- audience and prior knowledge;
- motivating scientific questions;
- dataset and provenance;
- scientific and data-science concepts;
- learning intentions;
- learner reasoning journey;
- sequence and scaffolding;
- wording and facilitation assumptions;
- contributor history and intellectual lineage;
- local design decisions.

Do not mechanically copy pedagogy, provenance or contributor decisions from Exoplanets or another resource.

Shared patterns may be adopted when they genuinely improve this resource, but their suitability must be considered in the Animal Traits context.

## Development approach

Before substantial development, establish:

- who the experience is for;
- what learners should learn;
- what they will actually do with data or evidence;
- what reasoning the activity should elicit;
- what would count as evidence of successful learning;
- only then, what interaction or software change is appropriate.

A useful heuristic is:

**one screen = one main cognitive job**

Do not force every experience into the same sequence.

For implementation work use:

**inspect → bounded change → run locally → visually inspect → iterate → inspect diff → commit when coherent**

Work on one experience or one shared concern at a time.

Do not opportunistically redesign other experiences.

Change shared modules only when the change genuinely belongs at the shared level.

## Local-first visual development

For learner-facing, visual or interactive work:

1. Start the app locally from `animal-traits-streamlit-v1/` using `python -m streamlit run app.py`.
2. Keep the Streamlit server running during iteration where practical.
3. Open the reported localhost URL in the Codex in-app browser so the maintainer can inspect the result without leaving Codex.
4. Reuse that browser tab during subsequent iterations where practical.
5. Let Streamlit auto-reload after edits when possible.
6. Do not open Chrome or another external browser unless explicitly requested or the in-app browser cannot perform the required check.
7. Do not deploy publicly merely for visual inspection.

The localhost port may vary. Use the URL reported by the running Streamlit process rather than assuming a fixed port.

## Git checkpoints

Git is the safety net and durable history, not a required step after every micro-edit.

- Make multiple local iterations when they form one coherent change.
- Commit when the work reaches a useful, inspectable checkpoint.
- Push when that checkpoint is worth preserving remotely or sharing.
- Do not commit or push merely to make visual inspection possible.
- Keep commits bounded and understandable.
- Always inspect the diff before committing.

Public deployment, when relevant, is a separate verification step from local visual review.

## Architecture boundaries

Keep reusable data preparation in `data.py`.

Keep quantitative modelling in `models.py`.

Keep reusable chart construction in `charts.py`; do not put Streamlit controls there.

Keep reusable interface components in `ui_helpers.py`.

Keep learner-facing wording, controls, sequencing and local pedagogy in the relevant `experiences/*.py` file.

Prefer ordinary readable Python and established libraries over clever abstractions.

A pedagogical change to one experience should ideally remain local to that experience.

## Scientific and data integrity

Prefer authentic use of the Animal Traits data.

Distinguish what the data directly show from interpretation or modelling.

Do not overstate what the dataset demonstrates.

Treat missing data, uncertainty, bias and limitations as potentially meaningful parts of the learning experience rather than automatically hiding them.

Add analysis techniques because they help learners answer a scientific or data-science question, not merely because the software supports them.

Review asset licensing and update `assets/MEDIA_SOURCES.md` when adding media.

## Testing and verification

Use the smallest relevant check for the change.

Examples:

- documentation-only change: inspect the diff; no Streamlit run required;
- isolated Python/data/model logic: run the smallest relevant check;
- learner-facing/UI change: run Streamlit locally and inspect the affected experience in the Codex browser;
- shared navigation or shell change: inspect the relevant routes locally;
- deployment-related change: verify the deployed environment separately when appropriate.

`python -m compileall .` may be used as a lightweight syntax check when Python code changes.

Do not require broad manual regression testing after every small local iteration.

If substantial reusable logic is introduced, consider focused automated tests. Do not introduce a test framework for an unrelated small task.

Always inspect the final diff for unrelated changes.

## Commands

From `animal-traits-streamlit-v1/`:

Install dependencies:

`python -m pip install -r requirements.txt`

Run locally:

`python -m streamlit run app.py`

Optional syntax check after Python changes:

`python -m compileall .`

Do not run `scripts/build_common_name_mapping.py` as a routine verification step. It is a data utility and should only be run when the task genuinely requires rebuilding that mapping.

## Shared design knowledge

Cross-resource design guidance may live in the `data-experience-streamlit-starter` shared playbook.

Treat that material as reusable guidance, not automatic local authority.

When applying a shared design decision to Animal Traits:

1. identify what the shared decision is trying to solve;
2. check whether the same problem exists here;
3. preserve Animal Traits-specific science and pedagogy;
4. record deliberate deviations when useful.

If the shared pattern does not fit this resource, do not force compliance.

## Security and configuration

Do not commit secrets, local environment files, generated caches or private datasets.

Keep dataset provenance and media attribution accurate.

## Commit style

Use short, imperative commit messages consistent with repository history.

Before committing:

- inspect the diff;
- confirm no unrelated files changed;
- run the smallest relevant verification.

For this single-maintainer project, do not add enterprise-style process or precautions unless there is a concrete need.
