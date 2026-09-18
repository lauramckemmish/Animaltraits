"""Focused tests for the Data Exploration Playground dataset inventory."""

import pandas as pd
from pathlib import Path
from streamlit.testing.v1 import AppTest

from charts import playground_count_heatmap, playground_three_variable_scatter
from data import load_data, playground_data

from experiences.data_exploration_playground import (
    KNOW_YOUR_DATA_FIELDS,
    PLAYGROUND_FACILITATION_POTENTIAL,
    PLAYGROUND_CURRICULUM_SUMMARY,
    PLAYGROUND_CURRICULUM_TAGS,
    TAB_LABELS,
    _render_start,
    _render_know_your_data,
    _render_one_variable,
    _render_three_variables,
    _render_two_variables,
    _render_follow_it_further,
    ONE_VARIABLE_CATEGORICAL_OPTIONS,
    ONE_VARIABLE_NUMERICAL_OPTIONS,
    _one_variable_category_counts,
    _know_your_data_inventory,
    _one_variable_numeric_summary,
)


def test_playground_uses_another_angle_rather_than_three_variables_framing():
    assert TAB_LABELS[-2:] == ["Another angle", "Follow it further"]


def test_playground_follow_up_handoff_distinguishes_a_pattern_from_an_explanation():
    import inspect

    source = inspect.getsource(_render_follow_it_further)
    assert "Follow something interesting" in source
    assert "What evidence would you need next?" in source
    assert "does not, by itself, tell you why the pattern exists" in source
    assert "text_area" not in source


def test_playground_has_one_preparation_note_and_three_contextual_facilitator_cues():
    import inspect
    from experiences import data_exploration_playground as playground

    assert "facilitator_preparation" in inspect.getsource(playground._render_start)
    assert "facilitator_live_cue" in inspect.getsource(playground._render_know_your_data)
    assert "facilitator_live_cue" in inspect.getsource(playground._render_two_variables)
    assert "facilitator_live_cue" in inspect.getsource(playground._render_follow_it_further)
    assert "facilitator_live_cue" not in inspect.getsource(playground._render_one_variable)
    assert "facilitator_live_cue" not in inspect.getsource(playground._render_three_variables)


def test_playground_curriculum_summary_is_stage_5_facilitator_support():
    import inspect

    source = inspect.getsource(_render_start)
    assert "curriculum_summary" in source
    assert "NSW curriculum — Stage 5 Data Science 2" in source
    assert '"SC5-DA2-01"' in source
    assert "detailed_content_note=True" in source
    assert "descriptive analysis of large datasets (L3)" in PLAYGROUND_CURRICULUM_SUMMARY
    assert "univariate/bivariate analysis (L5)" in PLAYGROUND_CURRICULUM_SUMMARY
    assert "Stage 4" not in PLAYGROUND_CURRICULUM_SUMMARY


def test_playground_curriculum_tags_are_the_approved_local_stage_mapping():
    import inspect

    assert PLAYGROUND_CURRICULUM_TAGS == {
        "start_here": [("SC5-DA2-01.L2", "◐")],
        "know_your_data": [("SC5-DA2-01.L1", "◐"), ("SC5-WS-05.2", "✓")],
        "one_variable": [("SC5-DA2-01.L3", "✓"), ("L4", "◐"), ("L5", "✓")],
        "two_variables": [("SC5-DA2-01.L5", "✓"), ("L6", "◐"), ("SC5-WS-06.2", "✓")],
        "another_angle": [("SC5-DA2-01.L5", "✓"), ("SC5-WS-06.1", "✓"), ("SC5-WS-06.2", "✓")],
        "follow_it_further": [("SC5-DA2-01.L2", "◐"), ("Q5", "◐"), ("SC5-WS-06.7", "◐")],
    }
    renderers = {
        "start_here": _render_start,
        "know_your_data": _render_know_your_data,
        "one_variable": _render_one_variable,
        "two_variables": _render_two_variables,
        "another_angle": _render_three_variables,
        "follow_it_further": _render_follow_it_further,
    }
    for stage, renderer in renderers.items():
        source = inspect.getsource(renderer)
        assert "curriculum_tags" in source
        assert f'PLAYGROUND_CURRICULUM_TAGS["{stage}"]' in source
        assert "Stage 4" not in source


def test_playground_facilitation_potential_is_adult_facing_and_preserves_app_alignment():
    import inspect

    source = inspect.getsource(_render_start)
    assert "facilitator_preparation" in source
    assert "PLAYGROUND_FACILITATION_POTENTIAL" in source
    assert "intentionally open-ended" in PLAYGROUND_FACILITATION_POTENTIAL
    assert "SC5-DA2-01.L2 ◐" in PLAYGROUND_FACILITATION_POTENTIAL
    assert "SC5-DA2-01.L4 ◐" in PLAYGROUND_FACILITATION_POTENTIAL
    assert "SC5-DA2-01.L6 ◐" in PLAYGROUND_FACILITATION_POTENTIAL
    assert "SC5-DA2-01.Q5 ◐" in PLAYGROUND_FACILITATION_POTENTIAL
    assert "SC5-WS-06.7 ◐" in PLAYGROUND_FACILITATION_POTENTIAL
    assert "repeated-species structure" in PLAYGROUND_FACILITATION_POTENTIAL
    assert "do not change the Playground's own alignment status" in PLAYGROUND_FACILITATION_POTENTIAL


def test_playground_facilitation_potential_does_not_change_learner_navigation_or_copy():
    import inspect

    source = inspect.getsource(_render_start)
    assert TAB_LABELS == [
        "Start here", "Know your data", "One variable", "Two variables", "Another angle", "Follow it further"
    ]
    assert "Explore the animal-trait data" in source
    assert "Know the data, inspect one variable, compare two" in source


def test_playground_renders_its_simultaneous_notice_prompts_with_stable_unique_keys():
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py").run(timeout=30)
    next(button for button in app.sidebar.button if button.label == "Data Exploration Playground").click()
    app.run(timeout=30)

    assert not app.exception
    assert [tab.label for tab in app.tabs] == TAB_LABELS


def test_playground_heatmap_uses_raw_counts_with_visible_annotations_including_zeroes():
    data = pd.DataFrame(
        {
            "Animal class": ["Mammal", "Mammal", "Bird"],
            "phylum": ["Chordata", "Chordata", "Chordata"],
        }
    )
    figure, record_count = playground_count_heatmap(
        data, "Animal class", "phylum", "Animal class", "Phylum"
    )

    assert record_count == 3
    assert figure.data[0].z.tolist() == [[1, 2]]
    annotations = {annotation.text for annotation in figure.layout.annotations}
    assert annotations == {"1", "2"}


def test_playground_heatmap_annotations_preserve_an_absent_combination():
    data = pd.DataFrame(
        {
            "Animal class": ["Mammal", "Bird"],
            "phylum": ["Chordata", "Arthropoda"],
        }
    )
    figure, _ = playground_count_heatmap(
        data, "Animal class", "phylum", "Animal class", "Phylum"
    )

    assert 0 in figure.data[0].z.flatten()
    assert "0" in {annotation.text for annotation in figure.layout.annotations}


def test_playground_animal_class_scatter_uses_shapes_without_changing_colour_groups():
    data = playground_data(load_data())
    figure, _ = playground_three_variable_scatter(
        data,
        "body mass (kg)",
        "brain size (kg)",
        "Animal class",
        "Body mass (kg)",
        "Brain size (kg)",
        "Animal class",
        log_x=True,
        log_y=True,
    )

    assert len(figure.data) > 1
    assert len({trace.name for trace in figure.data}) == len(figure.data)
    assert len({trace.marker.symbol for trace in figure.data}) > 1
    assert all(trace.marker.color is not None for trace in figure.data)


def test_playground_numerical_colour_scatter_keeps_its_single_symbol_encoding():
    data = pd.DataFrame(
        {
            "body": [1.0, 2.0, 3.0],
            "brain": [0.1, 0.2, 0.3],
            "third": [10.0, 20.0, 30.0],
            "species": ["one", "two", "three"],
            "Animal class": ["Mammal", "Bird", "Mammal"],
        }
    )
    figure, _ = playground_three_variable_scatter(
        data, "body", "brain", "third", "Body", "Brain", "Third"
    )

    assert len(figure.data) == 1
    assert figure.data[0].marker.symbol == "circle"


def test_know_your_data_inventory_includes_every_classroom_dataset_field():
    fields = [field for field, *_ in KNOW_YOUR_DATA_FIELDS]
    data = pd.DataFrame({field: [1, None] for field in fields})

    inventory = _know_your_data_inventory(data)

    assert inventory["Variable"].tolist() == fields
    assert len(inventory) == 13
    assert inventory.loc[inventory["Variable"].eq("species"), "Type"].item() == "Identifier / categorical label"
    assert inventory.loc[inventory["Variable"].eq("study sample size"), "Unit"].item() == "Count"


def test_know_your_data_inventory_calculates_missingness_from_its_input_data():
    fields = [field for field, *_ in KNOW_YOUR_DATA_FIELDS]
    data = pd.DataFrame({field: [1, None, None, 1] for field in fields})

    inventory = _know_your_data_inventory(data)

    assert set(inventory["Missing data"]) == {"2 (50.0%)"}


def test_one_variable_options_keep_the_settled_plotting_subset():
    assert list(ONE_VARIABLE_NUMERICAL_OPTIONS) == ["Body mass (kg)", "Metabolic rate (W)", "Mass-specific metabolic rate (W/kg)", "Brain size (kg)", "Study sample size"]
    assert list(ONE_VARIABLE_CATEGORICAL_OPTIONS) == ["Animal class", "Phylum", "Study sample sex", "Brain size method"]
    assert not {"order", "family", "genus", "species"} & set(ONE_VARIABLE_CATEGORICAL_OPTIONS.values())


def test_one_variable_numeric_summary_uses_raw_values_and_missingness():
    summary = _one_variable_numeric_summary(pd.DataFrame({"value": [1, 2, 10, None]}), "value")
    assert summary == {"usable": 3, "missing": 1, "mean": 13 / 3, "median": 2.0, "min": 1.0, "max": 10.0}


def test_one_variable_numeric_summary_does_not_depend_on_display_scale():
    data = pd.DataFrame({"value": [0.01, 1, 100, None]})
    assert _one_variable_numeric_summary(data, "value") == _one_variable_numeric_summary(data, "value")


def test_one_variable_animal_class_counts_use_existing_learner_facing_mapping():
    prepared = playground_data(pd.DataFrame({"class": ["Mammalia", "Aves"], "species": ["Mus musculus", "Homo sapiens"]}))
    counts = _one_variable_category_counts(prepared, "Animal class")
    assert counts.set_index("Category")["Count"].to_dict() == {"Mammal": 1, "Bird": 1}


def test_one_variable_category_counts_do_not_make_missing_a_category_or_merge_sex():
    sex = _one_variable_category_counts(pd.DataFrame({"study sample sex": ["male", "both", "male and female", None]}), "study sample sex")
    assert sex.set_index("Category")["Count"].to_dict() == {"male": 1, "both": 1, "male and female": 1}


def test_one_variable_method_counts_correct_the_known_display_spelling_variant_only():
    counts = _one_variable_category_counts(pd.DataFrame({"brain size - method": ["histological reconstruction", "immunostaining and histological recontruction", None]}), "brain size - method")
    assert counts.set_index("Category")["Count"].to_dict() == {"histological reconstruction": 1, "immunostaining and histological reconstruction": 1}
