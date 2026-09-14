"""Focused checks for CURIOUS's cat and elephant model-testing presentation."""

from __future__ import annotations

from charts import body_brain_class_fit_scatter
from data import load_data, species_traits_from_observations, with_common_class_names
from models import fit_relationship, predict_power_law


def test_mammal_test_chart_quiets_mammal_points_but_keeps_prediction_prominent():
    species_traits = species_traits_from_observations(load_data())
    class_data = with_common_class_names(species_traits)
    mammal_data = class_data[class_data["Animal class"].eq("Mammal")]
    mammal_fit = fit_relationship(
        mammal_data,
        "body mass (kg)",
        "brain size (kg)",
        log_x=True,
        log_y=True,
    )
    assert mammal_fit is not None

    cat_prediction = predict_power_law(mammal_fit, 4.0)
    figure = body_brain_class_fit_scatter(
        species_traits,
        highlighted_classes=["Mammal"],
        fits={"Mammal": mammal_fit},
        comparison_points=[
            {
                "label": "Cat model prediction",
                "body_mass_kg": 4.0,
                "brain_mass_kg": cat_prediction,
                "colour": "#2563eb",
                "symbol": "diamond",
            }
        ],
        highlighted_class_opacity=0.34,
    )

    traces = {trace.name: trace for trace in figure.data}
    assert traces["Mammal"].marker.opacity == 0.34
    assert traces["Mammal fit"].line.width == 5
    assert traces["Cat model prediction"].marker.size == 14
    assert traces["Cat model prediction"].marker.symbol == "diamond"


def test_curious_model_testing_uses_one_prediction_helper_and_no_cat_choice_gate():
    with open("experiences/curious.py", encoding="utf-8") as source_file:
        source = source_file.read()

    assert source.count("predict_power_law(mammal_fit, cat_body_mass)") == 1
    assert source.count("predict_power_law(mammal_fit, elephant_body_mass)") == 1
    assert "curious_cat_prediction_choice" not in source
    assert "Select the displayed model prediction" not in source
