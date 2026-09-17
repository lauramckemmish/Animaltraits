"""Focused tests for the Data Exploration Playground dataset inventory."""

import pandas as pd

from experiences.data_exploration_playground import (
    KNOW_YOUR_DATA_FIELDS,
    _know_your_data_inventory,
)


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
