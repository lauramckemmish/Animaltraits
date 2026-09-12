"""Regression checks for the pinned AnimalTraits classroom extract."""

from __future__ import annotations

import csv
import hashlib
import math

import pandas as pd

from data import (
    CLASS_LABELS,
    load_external_comparison_animals,
    resolve_common_names,
    search_student_animals,
    student_facing_data,
    with_common_class_names,
)
from models import fit_relationship
from scripts.build_classroom_dataset import CLASSROOM_FIELD_MAP, build_classroom_dataset


def _load_classroom_data() -> pd.DataFrame:
    return pd.read_csv("data/animal_traits.csv")


def _usable_class_data(data: pd.DataFrame) -> pd.DataFrame:
    prepared = with_common_class_names(data)
    for column in ["body mass (kg)", "brain size (kg)"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    return prepared[
        prepared["Animal class"].notna()
        & (prepared["body mass (kg)"] > 0)
        & (prepared["brain size (kg)"] > 0)
    ]


def test_classroom_dataset_schema_and_scientific_contract():
    data = _load_classroom_data()
    assert list(data.columns) == [target for _, target in CLASSROOM_FIELD_MAP]
    assert "common name" not in data.columns
    assert len(data) == 3580
    assert data["species"].nunique() == 2032

    usable = _usable_class_data(data)
    assert len(usable) == 1639
    assert data["body mass (kg)"].min() == 4.94e-9
    assert data["body mass (kg)"].max() == 759

    mammal = usable[usable["Animal class"] == "Mammal"]
    reptile = usable[usable["Animal class"] == "Reptile"]
    assert len(mammal) == 754
    assert len(reptile) == 43

    fit = fit_relationship(mammal, "body mass (kg)", "brain size (kg)", log_x=True, log_y=True)
    assert fit is not None
    assert math.isclose(fit.slope, 0.8123596101, rel_tol=0, abs_tol=1e-10)
    assert math.isclose(fit.intercept, -1.9166680102, rel_tol=0, abs_tol=1e-10)
    assert math.isclose(fit.r_squared, 0.8957115981, rel_tol=0, abs_tol=1e-10)
    assert round(100 ** fit.slope) == 42

    cat_prediction_g = 1000 * (10 ** fit.intercept) * 4.0 ** fit.slope
    elephant_prediction_kg = (10 ** fit.intercept) * 5550 ** fit.slope
    assert math.isclose(cat_prediction_g, 37.3612, rel_tol=0, abs_tol=1e-4)
    assert mammal["body mass (kg)"].max() == 759
    assert math.isclose(elephant_prediction_kg, 13.3366, rel_tol=0, abs_tol=1e-4)

    homo = data[(data["species"] == "Homo sapiens") & (data["brain size (kg)"] > 0)]
    assert len(homo) == 44
    assert math.isclose(homo["brain size (kg)"].median(), 1.305, rel_tol=0, abs_tol=1e-12)


def test_common_name_mapping_remains_the_learner_name_source():
    data = _load_classroom_data()
    assert resolve_common_names(pd.Series(["Mus musculus"])).iloc[0] == "House mouse"

    student_data = student_facing_data(data)
    house_mouse = student_data[student_data["Scientific name"] == "Mus musculus"]
    assert set(house_mouse["Common name"]) == {"House mouse"}

    matches = search_student_animals(data, "House mouse")
    assert "Mus musculus" in set(matches["Scientific name"])
    assert set(with_common_class_names(data)["Animal class"].dropna()) == set(CLASS_LABELS.values())


def test_external_comparison_evidence_remains_separate_and_unchanged():
    comparisons = load_external_comparison_animals()
    cat = comparisons.loc[comparisons["scientific_name"] == "Felis catus"].iloc[0]
    elephant = comparisons.loc[comparisons["scientific_name"] == "Loxodonta africana"].iloc[0]
    assert (cat["body_mass_kg"], cat["brain_mass_kg"]) == (4.0, 0.0284)
    assert (elephant["body_mass_kg"], elephant["brain_mass_kg"]) == (5550, 4.871)


def test_extractor_is_deterministic_for_a_verified_source(tmp_path):
    source = tmp_path / "observations.csv"
    source_fields = [field for field, _ in CLASSROOM_FIELD_MAP]
    row = {field: "" for field in source_fields}
    row.update({"phylum": "Chordata", "class": "Mammalia", "species": "Mus musculus", "body mass": "0.02"})
    with source.open("w", newline="", encoding="utf-8") as source_file:
        writer = csv.DictWriter(source_file, fieldnames=source_fields)
        writer.writeheader()
        writer.writerow(row)

    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    first_output = tmp_path / "first.csv"
    second_output = tmp_path / "second.csv"
    assert build_classroom_dataset(source, first_output, expected_sha256=digest) == 1
    assert build_classroom_dataset(source, second_output, expected_sha256=digest) == 1
    assert first_output.read_bytes() == second_output.read_bytes()

    with first_output.open(newline="", encoding="utf-8") as output_file:
        generated = list(csv.DictReader(output_file))
    assert list(generated[0]) == [target for _, target in CLASSROOM_FIELD_MAP]
    assert generated[0]["study sample sex"] == ""
    assert generated[0]["body mass (kg)"] == "0.02"
