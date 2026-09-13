"""Focused checks for CURIOUS's species-level animal-group evidence stage."""

from __future__ import annotations

from charts import body_brain_group_fit_scatter
from data import load_data, species_traits_from_observations
from experiences.curious import (
    CURIOUS_GROUP_CLASSES,
    _curious_animal_groups,
    _curious_group_has_trend,
    _curious_usable_body_brain_species,
)
from models import fit_relationship


def test_curious_learner_groups_use_species_counts_and_trend_rule():
    usable = _curious_usable_body_brain_species(species_traits_from_observations(load_data()))
    groups = _curious_animal_groups(usable)

    assert len(usable) == 1196
    assert {name: len(group_data) for name, group_data in groups.items()} == {
        "Mammal": 501,
        "Bird": 597,
        "Reptile": 37,
        "Amphibian": 10,
        "Insect": 42,
        "Other invertebrates": 9,
    }
    assert CURIOUS_GROUP_CLASSES["Other invertebrates"] == [
        "Arachnid",
        "Centipede",
        "Crustacean",
        "Segmented worm",
        "Snail / slug",
    ]
    assert all(_curious_group_has_trend(name, groups[name]) for name in groups if name != "Other invertebrates")
    assert not _curious_group_has_trend("Other invertebrates", groups["Other invertebrates"])


def test_group_chart_keeps_reference_hideable_and_other_invertebrates_points_only():
    usable = _curious_usable_body_brain_species(species_traits_from_observations(load_data()))
    groups = _curious_animal_groups(usable)
    all_fit = fit_relationship(usable, "body mass (kg)", "brain size (kg)", log_x=True, log_y=True)
    mammal_fit = fit_relationship(groups["Mammal"], "body mass (kg)", "brain size (kg)", log_x=True, log_y=True)
    reptile_fit = fit_relationship(groups["Reptile"], "body mass (kg)", "brain size (kg)", log_x=True, log_y=True)

    comparison = body_brain_group_fit_scatter(
        usable,
        groups={"Mammal": groups["Mammal"], "Reptile": groups["Reptile"]},
        fits={"Mammal": mammal_fit, "Reptile": reptile_fit},
        reference_fit=all_fit,
    )
    assert [trace.name for trace in comparison.data] == [
        "All animals reference",
        "Mammal",
        "Mammal trend",
        "Reptile",
        "Reptile trend",
    ]
    assert comparison.data[0].line.dash == "dot"
    assert comparison.data[0].showlegend is True

    other_invertebrates = body_brain_group_fit_scatter(
        usable,
        groups={"Other invertebrates": groups["Other invertebrates"]},
        fits={},
    )
    assert [trace.name for trace in other_invertebrates.data] == ["Other invertebrates"]
