"""Focused tests for the Data Exploration Playground dataset inventory."""

import pandas as pd

from data import playground_data

from experiences.data_exploration_playground import (
    KNOW_YOUR_DATA_FIELDS,
    TAB_LABELS,
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
