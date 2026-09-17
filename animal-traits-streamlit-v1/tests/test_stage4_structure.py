"""Structural contract for the canonical Stage 4 learning journey."""

import inspect

import pandas as pd
import pytest

from experiences import year8
from data import (
    comparison_reference_masses,
    external_comparison_taxonomy,
    load_data,
    load_external_comparison_animals,
)
from experiences.year8 import (
    LESSON_LABELS,
    STAGE4_SCREENS,
    STAGE4_ANIMAL_COLLECTION_MAX_SELECTION,
    STAGE4_ANIMAL_COLLECTION_MIN_SELECTION,
    _format_stage4_mass_kg,
    _stage4_animal_collection_ready,
    _lesson_for_screen,
    _lesson_screen_range,
    _stage4_saved_species_after_adding,
    _stage4_saved_species_after_removing,
    _stage4_mass_in_kg,
    _stage4_body_mass_evidence,
    _stage4_body_mass_ready,
    _stage4_body_brain_ready,
    _stage4_animal_groups_ready,
    _stage4_cat_model_ready,
    _clear_stage4_cat_comparison_state,
    _stage4_elephant_model_ready,
    _clear_stage4_elephant_comparison_state,
    _stage4_mammal_model_ready,
    _stage4_model_ids_for_level,
    _stage4_model_level_for_id,
    _stage4_model_judgement_ready,
    _stage4_prediction_ready,
    _clear_stage4_prediction_downstream_state,
    _stage4_selected_animal_classes,
    _stage4_selected_animal_groups,
    _stage4_usable_species,
)
from charts import histogram
from data import body_brain_orientation, selected_species_body_brain, selected_species_body_mass, species_traits_from_observations
from charts import body_brain_group_scatter, body_brain_scatter
from data import (
    body_brain_animal_groups,
    body_brain_model_comparison_candidates,
    body_brain_model_evidence,
    selected_species_taxonomy,
    taxonomy_group_size_summary,
    usable_body_brain_species,
    stage4_prediction_animal_choices,
    stage4_prediction_model_candidates,
)
from models import (
    fit_relationship,
    power_law_scale_factor,
    predict_power_law,
    prediction_range_status,
)


def test_stage4_has_the_canonical_eleven_screen_sequence():
    assert [screen.title for screen in STAGE4_SCREENS] == [
        "Start with scale", "Find your animals", "Body mass", "Body + brain", "Animal groups",
        "Mammal model", "Test the model: cat", "Test the model: elephant", "Judge model confidence",
        "Predict when the answer is unknown", "Data Science",
    ]


def test_stage4_lesson_boundary_is_after_screen_five():
    assert LESSON_LABELS == ("Lesson 1 — Seeing structure in data", "Lesson 2 — Using and trusting a model")
    assert list(_lesson_screen_range(0)) == [0, 1, 2, 3, 4]
    assert list(_lesson_screen_range(1)) == [5, 6, 7, 8, 9, 10]
    assert [_lesson_for_screen(index) for index in range(11)] == [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1]


def test_stage4_scale_estimates_use_a_common_kilogram_unit():
    assert _stage4_mass_in_kg(32.1, "grams") == pytest.approx(0.0321)
    assert _stage4_mass_in_kg(5.55, "tonnes") == pytest.approx(5550)
    assert _format_stage4_mass_kg(0.0321) == "0.0321 kg"
    assert _format_stage4_mass_kg(5550) == "5,550 kg"


def test_stage4_scale_reuses_the_grounded_mouse_and_external_elephant_references():
    assert comparison_reference_masses(load_data()) == (0.0321, 5550)


def test_stage4_carried_forward_animals_use_bounded_scientific_name_identities():
    saved = _stage4_saved_species_after_adding([], "Mus musculus")
    saved = _stage4_saved_species_after_adding(saved, "Mus musculus")
    saved = _stage4_saved_species_after_adding(saved, "Loxodonta africana")

    assert saved == ["Mus musculus", "Loxodonta africana"]
    assert _stage4_saved_species_after_removing(saved, "Mus musculus") == ["Loxodonta africana"]

    for index in range(10):
        saved = _stage4_saved_species_after_adding(saved, f"Species {index}")
    assert len(saved) == STAGE4_ANIMAL_COLLECTION_MAX_SELECTION


def test_stage4_only_offers_species_with_both_later_graph_measurements():
    matches = pd.DataFrame(
        {
            "Scientific name": ["Both values", "No brain", "No body"],
            "Common name": ["Both", "No brain", "No body"],
            "Body mass (kg)": [2.0, 3.0, None],
            "Brain size (kg)": [0.1, None, 0.2],
        }
    )

    assert _stage4_usable_species(matches)["Scientific name"].tolist() == ["Both values"]


def test_stage4_requires_four_graph_ready_species_before_continuing():
    assert STAGE4_ANIMAL_COLLECTION_MIN_SELECTION == 4
    assert STAGE4_ANIMAL_COLLECTION_MAX_SELECTION == 8
    for count in range(STAGE4_ANIMAL_COLLECTION_MIN_SELECTION):
        assert not _stage4_animal_collection_ready(
            [f"Species {index}" for index in range(count)]
        )
    assert _stage4_animal_collection_ready(
        ["Species 1", "Species 2", "Species 3", "Species 4"]
    )
    for count in range(STAGE4_ANIMAL_COLLECTION_MIN_SELECTION, 9):
        assert _stage4_animal_collection_ready([f"Species {index}" for index in range(count)])
    assert not _stage4_animal_collection_ready([f"Species {index}" for index in range(9)])


def test_stage4_has_no_zero_selection_continuation_path():
    assert not hasattr(year8, "_continue_stage4_without_animals")
    assert not hasattr(year8, "_finish_stage4_animal_collection")


def test_stage4_body_mass_resolves_saved_scientific_names_in_order():
    species_data = species_traits_from_observations(load_data())
    selected = selected_species_body_mass(
        species_data,
        ["Corvus brachyrhynchos", "Mus musculus", "Unknown species", "Corvus brachyrhynchos"],
    )
    assert selected["Scientific name"].tolist() == ["Corvus brachyrhynchos", "Mus musculus"]
    assert selected["body mass (kg)"].gt(0).all()


def test_stage4_body_mass_uses_the_same_evidence_and_selected_anchors_in_both_views():
    evidence = _stage4_body_mass_evidence(load_data())
    selected = selected_species_body_mass(evidence, ["Mus musculus", "Canis familiaris"])
    linear = histogram(evidence, "body mass (kg)", log_x=False, learner_selected_data=selected)
    logarithmic = histogram(evidence, "body mass (kg)", log_x=True, learner_selected_data=selected)

    assert linear.layout.xaxis.type in (None, "linear")
    assert logarithmic.layout.xaxis.type == "log"
    assert linear.data[-1].name == logarithmic.data[-1].name == "Your earlier searches"
    assert linear.data[-1].customdata[:, 1].tolist() == logarithmic.data[-1].customdata[:, 1].tolist()
    assert linear.data[-1].x.tolist() == logarithmic.data[-1].x.tolist()


def test_stage4_body_mass_sequence_requires_linear_graph_furniture_log_and_comparison():
    assert year8.STAGE4_BODY_MASS_SEQUENCE == (
        "linear representation",
        "graph furniture",
        "logarithmic representation",
        "same and changed comparison",
    )
    source = inspect.getsource(year8._render_body_mass)
    assert source.index("ordinary linear scale") < source.index("logarithmic (log) scale")
    assert "variable, units and linear scale" in source
    assert "Stayed the same" in source
    assert "Changed" in source

    assert not _stage4_body_mass_ready(False, True, True, True)
    assert not _stage4_body_mass_ready(True, False, True, True)
    assert not _stage4_body_mass_ready(True, True, False, True)
    assert not _stage4_body_mass_ready(True, True, True, False)
    assert _stage4_body_mass_ready(True, True, True, True)


def test_stage4_body_brain_orientation_combines_familiar_and_saved_species_without_duplicates():
    orientation = body_brain_orientation(
        species_traits_from_observations(load_data()),
        ["Homo sapiens", "Canis familiaris", "Rattus norvegicus"],
    )
    assert orientation["Scientific name"].is_unique
    assert orientation.loc[orientation["Scientific name"].eq("Homo sapiens"), "Role"].item() == "Familiar example · your animal"
    assert orientation.loc[orientation["Scientific name"].eq("Rattus norvegicus"), "Role"].item() == "Your animal"


def test_stage4_body_brain_graph_highlights_saved_species_without_a_model_line():
    data = species_traits_from_observations(load_data())
    selected = selected_species_body_brain(data, ["Rattus norvegicus", "Canis familiaris"])
    figure = body_brain_scatter(data, log_x=True, log_y=True, learner_selected_data=selected)
    assert figure.layout.xaxis.type == figure.layout.yaxis.type == "log"
    assert figure.data[-1].name == "Your earlier searches"
    assert figure.data[-1].customdata[:, 1].tolist() == ["Rattus norvegicus", "Canis familiaris"]
    assert all(trace.mode != "lines" for trace in figure.data)


def test_stage4_body_brain_gate_requires_prediction_evidence_claim_and_reasoning():
    correct_claim = "Brain mass generally increases as body mass increases."
    correct_reasoning = "Across the cloud, larger bodies generally occur with larger brains, with variation."
    assert not _stage4_body_brain_ready("Generally increase", False, correct_claim, correct_reasoning)
    assert not _stage4_body_brain_ready("Generally increase", True, "Every larger animal has a larger brain.", correct_reasoning)
    assert not _stage4_body_brain_ready("Generally increase", True, correct_claim, "Every point lies on one exact line.")
    assert _stage4_body_brain_ready("Generally increase", True, correct_claim, correct_reasoning)


def test_stage4_animal_groups_use_valid_paired_species_and_established_learner_labels():
    usable = usable_body_brain_species(species_traits_from_observations(load_data()))
    groups = body_brain_animal_groups(usable)

    assert list(groups) == [
        "Mammal", "Bird", "Reptile", "Amphibian", "Insect", "Other invertebrates"
    ]
    assert all(
        group_data[["body mass (kg)", "brain size (kg)"]].gt(0).all().all()
        for group_data in groups.values()
    )
    assert not groups["Mammal"].empty
    assert not groups["Reptile"].empty


def test_stage4_animal_groups_keep_saved_animals_visible_by_scientific_name():
    data = species_traits_from_observations(load_data())
    selected = selected_species_body_brain(data, ["Rattus norvegicus", "Canis familiaris"])
    groups = body_brain_animal_groups(usable_body_brain_species(data))
    saved_groups = _stage4_selected_animal_groups(groups, selected)
    figure = body_brain_group_scatter(groups, learner_selected_data=selected)

    assert saved_groups["Scientific name"].tolist() == ["Rattus norvegicus", "Canis familiaris"]
    assert saved_groups["Group"].tolist() == ["Mammal", "Mammal"]
    assert figure.data[-1].name == "Your earlier searches"
    assert figure.data[-1].customdata[:, 1].tolist() == ["Rattus norvegicus", "Canis familiaris"]


def test_stage4_taxonomy_details_keep_scientific_identity_and_dataset_provided_ranks():
    data = species_traits_from_observations(load_data())
    taxonomy = selected_species_taxonomy(
        data, ["Rattus norvegicus", "Canis familiaris"]
    )
    selected_classes = _stage4_selected_animal_classes(
        data, ["Rattus norvegicus", "Canis familiaris"]
    )

    assert taxonomy["Scientific name"].tolist() == ["Rattus norvegicus", "Canis familiaris"]
    assert taxonomy["Class"].tolist() == ["Mammal", "Mammal"]
    assert taxonomy[["Order", "Family", "Genus"]].notna().all().all()
    assert selected_classes.columns.tolist() == ["Animal", "Scientific name", "Class"]


def test_stage4_taxonomy_summary_uses_the_same_usable_paired_evidence():
    usable = usable_body_brain_species(species_traits_from_observations(load_data()))
    summary = taxonomy_group_size_summary(usable)
    by_rank = summary.set_index("Rank")

    assert len(usable) == 1196
    assert by_rank.loc["Phylum", ["Groups", "Largest group size"]].tolist() == [4, 1145]
    assert by_rank.loc["Class", ["Groups", "Typical group size"]].tolist() == [8, 23.5]
    assert by_rank.loc["Order", ["Groups", "Typical group size"]].tolist() == [64, 4.0]
    assert by_rank.loc["Family", ["Groups", "Typical group size"]].tolist() == [229, 2.0]
    assert by_rank.loc["Genus", ["Groups", "Typical group size"]].tolist() == [668, 1.0]
    assert by_rank.loc["Species", ["Groups", "Typical group size"]].tolist() == [1196, 1.0]


def test_stage4_animal_groups_compare_mammals_and_reptiles_without_a_model_line():
    data = species_traits_from_observations(load_data())
    groups = body_brain_animal_groups(usable_body_brain_species(data))
    figure = body_brain_group_scatter(
        {"Mammal": groups["Mammal"], "Reptile": groups["Reptile"]}
    )

    assert figure.layout.xaxis.type == figure.layout.yaxis.type == "log"
    assert [trace.name.split(" (")[0] for trace in figure.data] == ["Mammal", "Reptile"]
    assert all(trace.mode != "lines" for trace in figure.data)


def test_stage4_animal_groups_gate_requires_grouped_evidence_comparison_and_mammal_evidence():
    correct_comparison = "Mammals tend to have larger brain masses than reptiles."
    assert not _stage4_animal_groups_ready(False, correct_comparison, "Mammal evidence")
    assert not _stage4_animal_groups_ready(True, "Every mammal has a larger brain mass than every reptile.", "Mammal evidence")
    assert not _stage4_animal_groups_ready(True, correct_comparison, "All animal groups together")
    assert _stage4_animal_groups_ready(True, correct_comparison, "Mammal evidence")


def test_stage4_model_candidates_use_stable_ids_and_the_ten_species_display_rule():
    usable = usable_body_brain_species(species_traits_from_observations(load_data()))
    candidates = body_brain_model_comparison_candidates(usable)

    assert candidates.iloc[0]["Model id"] == "all"
    assert candidates.iloc[0]["Rank"] == "Pooled evidence"
    assert "class:Mammalia" not in candidates["Model id"].tolist()
    assert "genus:Lichenostomus" not in candidates["Model id"].tolist()
    assert "genus:Macropus" not in candidates["Model id"].tolist()
    assert candidates.loc[candidates["Model id"].ne("all"), "Usable species"].ge(10).all()
    assert candidates["Label"].str.contains("species").all()
    assert body_brain_model_evidence(usable, "all").equals(usable)
    assert len(body_brain_model_evidence(usable, "order:Primates")) == 86


def test_stage4_model_candidates_are_grouped_by_eligible_evidence_level():
    usable = usable_body_brain_species(species_traits_from_observations(load_data()))
    candidates = body_brain_model_comparison_candidates(usable)

    assert candidates["Rank"].value_counts().to_dict() == {
        "family": 34,
        "order": 24,
        "genus": 5,
        "class": 4,
        "Pooled evidence": 1,
    }
    assert _stage4_model_ids_for_level(candidates, "All animals") == ["all"]
    assert _stage4_model_ids_for_level(candidates, "Class") == [
        "class:Aves", "class:Insecta", "class:Reptilia", "class:Amphibia"
    ]


def test_stage4_model_candidate_labels_orient_without_changing_source_identity():
    usable = usable_body_brain_species(species_traits_from_observations(load_data()))
    labels = body_brain_model_comparison_candidates(usable).set_index("Model id")["Label"]

    assert labels["order:Passeriformes"] == "Passeriformes — perching birds · 275 species"
    assert labels["family:Phyllostomatidae"] == "Phyllostomidae — leaf-nosed bats · 12 species"
    assert labels["genus:Corvus"] == "Corvus — crows and ravens · 16 species"


def test_stage4_model_level_change_keeps_stable_valid_ids_and_prevents_duplicates():
    usable = usable_body_brain_species(species_traits_from_observations(load_data()))
    candidates = body_brain_model_comparison_candidates(usable)

    assert _stage4_model_level_for_id(candidates, "family:Phyllostomatidae") == "Family"
    assert _stage4_model_level_for_id(candidates, "order:Primates") == "Order"
    assert _stage4_model_ids_for_level(candidates, "Order", "order:Primates")[0] == "order:Passeriformes"
    assert "order:Primates" not in _stage4_model_ids_for_level(
        candidates, "Order", "order:Primates"
    )


def test_stage4_mammal_model_scaling_comes_from_the_shared_power_law_fit():
    usable = usable_body_brain_species(species_traits_from_observations(load_data()))
    mammal_fit = fit_relationship(
        usable[usable["class"].eq("Mammalia")],
        "body mass (kg)",
        "brain size (kg)",
        log_x=True,
        log_y=True,
    )

    assert mammal_fit is not None
    assert power_law_scale_factor(mammal_fit, 10) == pytest.approx(10 ** mammal_fit.slope)
    assert power_law_scale_factor(mammal_fit, 100) == pytest.approx(100 ** mammal_fit.slope)
    assert power_law_scale_factor(mammal_fit, 100) > 10


def test_stage4_mammal_model_gate_requires_model_meaning_distinct_comparisons_and_interpretation():
    correct_interpretation = (
        "Changing which animals are used as evidence can change the fitted relationship and prediction."
    )
    assert not _stage4_mammal_model_ready(False, "More than 10×", "all", "order:Primates", True, correct_interpretation)
    assert not _stage4_mammal_model_ready(True, "About 10×", "all", "order:Primates", True, correct_interpretation)
    assert not _stage4_mammal_model_ready(True, "More than 10×", "all", "all", True, correct_interpretation)
    assert not _stage4_mammal_model_ready(True, "More than 10×", "all", "order:Primates", False, correct_interpretation)
    assert _stage4_mammal_model_ready(True, "More than 10×", "all", "order:Primates", True, correct_interpretation)


def test_stage4_cat_uses_the_external_comparison_record_and_model_specific_ranges():
    usable = usable_body_brain_species(species_traits_from_observations(load_data()))
    cat = load_external_comparison_animals().query("scientific_name == 'Felis catus'").iloc[0]
    mammal_fit = fit_relationship(
        usable[usable["class"].eq("Mammalia")],
        "body mass (kg)",
        "brain size (kg)",
        log_x=True,
        log_y=True,
    )

    assert (cat["body_mass_kg"], cat["brain_mass_kg"]) == (4.0, 0.0284)
    assert mammal_fit is not None
    assert predict_power_law(mammal_fit, float(cat["body_mass_kg"])) > 0
    assert prediction_range_status(mammal_fit, float(cat["body_mass_kg"])) == "interpolation"


def test_stage4_cat_model_changes_invalidate_only_the_changed_comparison_state():
    state = {
        "stage4_cat_comparison_1_judgement": "Better",
        "stage4_cat_comparison_1_reason": "It is more biologically similar.",
        "stage4_cat_comparison_1_revealed": True,
        "stage4_cat_comparison_2_judgement": "Worse",
        "stage4_cat_comparison_2_reason": "It has different evidence.",
        "stage4_cat_comparison_2_revealed": True,
    }

    _clear_stage4_cat_comparison_state(state, 1)

    assert state["stage4_cat_comparison_1_judgement"] is None
    assert state["stage4_cat_comparison_1_reason"] == ""
    assert state["stage4_cat_comparison_1_revealed"] is False
    assert state["stage4_cat_comparison_2_judgement"] == "Worse"
    assert state["stage4_cat_comparison_2_revealed"] is True


def test_stage4_external_test_animal_taxonomy_is_identity_tied_and_compact():
    assert external_comparison_taxonomy("Felis catus") == {
        "Class": "Mammalia",
        "Order": "Carnivora",
        "Family": "Felidae",
        "Genus": "Felis",
    }
    assert external_comparison_taxonomy("Loxodonta africana") == {
        "Class": "Mammalia",
        "Order": "Proboscidea",
        "Family": "Elephantidae",
        "Genus": "Loxodonta",
    }


def test_stage4_elephant_uses_the_checked_in_external_record_and_extrapolates_mammal_fit():
    usable = usable_body_brain_species(species_traits_from_observations(load_data()))
    elephant = load_external_comparison_animals().query(
        "scientific_name == 'Loxodonta africana'"
    ).iloc[0]
    mammal_fit = fit_relationship(
        usable[usable["class"].eq("Mammalia")],
        "body mass (kg)",
        "brain size (kg)",
        log_x=True,
        log_y=True,
    )

    assert (elephant["body_mass_kg"], elephant["brain_mass_kg"]) == (5550, 4.871)
    assert mammal_fit is not None
    assert prediction_range_status(mammal_fit, float(elephant["body_mass_kg"])) == "extrapolation"


def test_stage4_elephant_model_changes_invalidate_only_the_changed_comparison_state():
    state = {
        "stage4_elephant_comparison_1_judgement": "Better",
        "stage4_elephant_comparison_1_reason": "It includes large mammals.",
        "stage4_elephant_comparison_1_revealed": True,
        "stage4_elephant_comparison_2_judgement": "Worse",
        "stage4_elephant_comparison_2_reason": "It is a narrow group.",
        "stage4_elephant_comparison_2_revealed": True,
    }

    _clear_stage4_elephant_comparison_state(state, 2)

    assert state["stage4_elephant_comparison_1_revealed"] is True
    assert state["stage4_elephant_comparison_2_judgement"] is None
    assert state["stage4_elephant_comparison_2_reason"] == ""
    assert state["stage4_elephant_comparison_2_revealed"] is False


def test_stage4_cat_gate_requires_both_current_comparison_reveals_and_takeaway():
    assert not _stage4_cat_model_ready(True, False, True, True)
    assert not _stage4_cat_model_ready(True, True, True, False)
    assert _stage4_cat_model_ready(True, True, True, True)


def test_stage4_elephant_gate_requires_both_current_comparison_reveals_and_takeaway():
    assert not _stage4_elephant_model_ready(True, True, False, True)
    assert not _stage4_elephant_model_ready(True, True, True, False)
    assert _stage4_elephant_model_ready(True, True, True, True)


def test_stage4_screen_five_is_lesson_one_endpoint_and_screen_nine_is_implemented():
    screen_five = inspect.getsource(year8._render_animal_groups)
    render_source = inspect.getsource(year8.render)

    assert "broadly similar body masses" in screen_five
    assert "does not establish a cause" in screen_five
    assert "We have not made a model yet" in screen_five
    assert "useful analytical choice here, not a universal best grouping level" in screen_five
    assert "not a taxonomic class" in screen_five
    assert "elif screen_index == 4:" in render_source
    assert "elif screen_index == 5:\n        _render_mammal_model(data)" in render_source
    assert "elif screen_index == 6:\n        _render_cat_model_testing(data)" in render_source
    assert "elif screen_index == 7:\n        _render_elephant_model_testing(data)" in render_source
    assert "elif screen_index == 8:\n        _render_model_judgement()" in render_source
    assert "st.info(\"Lesson 1 ends here.\")" in render_source


def test_stage4_model_judgement_requires_three_intended_responses():
    assert not _stage4_model_judgement_ready("The cat prediction", "It depends", "Not by itself")
    assert not _stage4_model_judgement_ready("The elephant prediction", "No", "Not by itself")
    assert not _stage4_model_judgement_ready("The elephant prediction", "It depends", "No")
    assert _stage4_model_judgement_ready(
        "The elephant prediction", "It depends", "Not by itself"
    )


def test_stage4_model_judgement_is_sequential_and_later_stage4_screens_are_implemented():
    source = inspect.getsource(year8._render_model_judgement)

    assert source.index("Which prediction gives you more reason to be cautious?") < source.index(
        "A model uses more animals than another model"
    ) < source.index("One of your models happened to predict the cat very closely")
    assert source.index("So what makes a prediction more defensible?") > source.index(
        "One of your models happened to predict the cat very closely"
    )
    assert "elif screen_index == 9:\n        _render_predict_when_unknown(data)" in inspect.getsource(year8.render)
    assert "elif screen_index == 10:\n        _render_data_science_closure()" in inspect.getsource(year8.render)


def test_stage4_data_science_closure_reuses_the_transfer_infographic_without_a_gate():
    source = inspect.getsource(year8._render_data_science_closure)

    assert "You’ve just done data science." in source
    assert "DATA_SCIENCE_INFOGRAPHIC_PATH" in source
    assert "Sometimes we can test a prediction" in source
    assert "A prediction is not the end of the story." in source
    assert "completion_gate" not in source


def test_stage4_unknown_prediction_choices_use_stable_names_and_display_platypus():
    choices = stage4_prediction_animal_choices(species_traits_from_observations(load_data()))
    platypus = choices.set_index("Scientific name").loc["Ornithorhynchus anatinus"]

    assert choices["Scientific name"].is_unique
    assert platypus["Common name"] == "Platypus"
    assert choices["body mass (kg)"].gt(0).all()


def test_stage4_unknown_prediction_only_offers_applicable_live_models():
    species_data = species_traits_from_observations(load_data())
    choices = stage4_prediction_animal_choices(species_data)
    fennec = choices.set_index("Scientific name").loc["Vulpes zerda"]
    candidates = stage4_prediction_model_candidates(usable_body_brain_species(species_data), fennec)

    assert candidates["Model id"].tolist() == [
        "all", "class:Mammalia", "order:Carnivora", "family:Canidae"
    ]
    assert candidates["Usable species"].ge(10).all()


def test_stage4_unknown_prediction_gate_and_reset_are_bounded_to_screen_ten():
    assert not _stage4_prediction_ready("Vulpes zerda", "all", "Some confidence", [])
    assert _stage4_prediction_ready(
        "Vulpes zerda", "all", "Some confidence", ["The available evidence is broad or less specific."]
    )
    state = {
        "stage4_prediction_model": "all",
        "stage4_prediction_confidence": "High confidence",
        "stage4_prediction_reasons": ["The body mass is inside the evidence range."],
        "stage4_prediction_revealed": True,
        "stage4_saved_species": ["Mus musculus"],
    }
    _clear_stage4_prediction_downstream_state(state)

    assert state["stage4_prediction_model"] == ""
    assert state["stage4_prediction_revealed"] is False
    assert state["stage4_saved_species"] == ["Mus musculus"]


def test_stage4_unknown_prediction_chooser_is_a_compact_grid_before_taxonomy_context():
    chooser_source = inspect.getsource(year8._render_stage4_prediction_animal_cards)
    screen_source = inspect.getsource(year8._render_predict_when_unknown)

    assert "st.columns(3)" in chooser_source
    assert "width=\"stretch\"" in chooser_source
    assert "breadcrumb" not in chooser_source
    assert "← Choose a different animal" in screen_source
