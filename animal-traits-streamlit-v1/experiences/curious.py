"""Guided CURIOUS Animal Traits experience."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from charts import body_brain_scatter, class_comparison, histogram
from ui_helpers import (
    graph_guide,
    key_idea,
    page_header,
    response_box,
    scroll_to_top_if_requested,
    step_buttons,
    step_tabs,
    teacher_note,
)

STEP_LABELS = [
    "Welcome",
    "1 · Meet the data",
    "2 · How big are animals?",
    "3 · Compare groups",
    "4 · Body mass & brain size",
    "5 · Compare relationships",
    "Conclusion",
]


def render(data: pd.DataFrame) -> None:
    part = int(st.session_state.get("curious_part", 0))
    part = max(0, min(part, len(STEP_LABELS) - 1))
    page_header("CURIOUS · Animal Traits")
    _, selected = step_tabs(STEP_LABELS, "curious_step_selector", part)
    if selected != part:
        part = selected
        st.session_state["curious_part"] = part
        st.session_state["curious_scroll_to_top"] = True
    scroll_to_top_if_requested("curious_scroll_to_top")

    if part == 0:
        teacher_note(
            "Welcome",
            "Introduce the scientific dataset, its terrestrial scope and the idea that real datasets are incomplete before students begin analysing it.",
            "Keep this conversational. The activity will focus on two traits only: body mass and brain size. Missing animals or missing measurements are expected features of real scientific data.",
            "5 min",
        )
        st.header("Welcome")
        st.write(
            "Animals are incredibly different. Some weigh a tiny fraction of a gram, while others weigh thousands of kilograms. "
            "Their brains also vary enormously. In this activity, you’ll use **real scientific measurements** to look for patterns in those differences."
        )
        st.info("**Today's challenge:** What can data reveal about how animal body size and brain size vary and relate to each other?")

        st.subheader("About the dataset")
        st.write(
            "We are using **AnimalTraits**, a curated scientific database built from measurements reported in peer-reviewed research. "
            "It focuses on **terrestrial animals** — animals that live primarily on land — across many different groups, including mammals, birds, reptiles, amphibians, insects, spiders, molluscs and annelids."
        )

        trait_cols = st.columns(2)
        trait_cols[0].markdown("**Body mass**  \nHow much an animal weighs")
        trait_cols[1].markdown("**Brain size**  \nRecorded brain mass or volume")

        key_idea(
            "Real scientific datasets are incomplete.",
            "If an animal or measurement is missing, that does not mean the animal does not exist. It may be outside this dataset's scope, or the measurement may not have been published or included.",
        )
        st.caption(
            "AnimalTraits was compiled from original scientific publications. Full source information, the raw classroom dataset and citation are available in the sidebar."
        )
        with st.expander("Dataset source & citation"):
            st.markdown(
                "**Herberstein, M. E., McLean, D. J., Lowe, E. et al. (2022).** "
                "*AnimalTraits – a curated animal trait database for body mass, metabolic rate and brain size.* "
                "Scientific Data, 9, 265. "
                "[DOI: 10.1038/s41597-022-01364-9](https://doi.org/10.1038/s41597-022-01364-9)"
            )
            st.markdown(
                "[AnimalTraits website](https://animaltraits.org) · "
                "[GitHub source and raw data](https://github.com/animaltraits/animaltraits.github.io)"
            )

    elif part == 1:
        teacher_note(
            "Meet the data",
            "Use a familiar animal to introduce records, variables and missing data.",
            "Have students search for an animal they know. If it is absent, treat that as useful evidence about dataset scope or missing measurements rather than a failed task. Then connect the search result back to rows and columns.",
            "8 min",
        )
        st.header("1 · Meet the data")
        st.write("Each **row** is an animal observation from the source database. Each **column** is a variable or descriptor.")

        st.markdown("### Find an animal")
        st.write("Search for an animal you know. Try a common name or a scientific name.")
        query = st.text_input("Animal search", placeholder="Try: human, elephant, kangaroo, Canis…", key="curious_animal_search")
        if query.strip():
            mask = pd.Series(False, index=data.index)
            searchable = [column for column in ["common name", "species", "genus"] if column in data.columns]
            for column in searchable:
                mask = mask | data[column].astype(str).str.contains(query.strip(), case=False, na=False, regex=False)
            matches = data.loc[mask]
            useful = [c for c in ["common name", "species", "class", "body mass (kg)", "brain size (kg)"] if c in data.columns]
            if matches.empty:
                st.warning(
                    "No matching record was found in this dataset. That is useful information: the animal may be outside AnimalTraits' terrestrial scope, or the relevant measurements may not be present in this curated database."
                )
            else:
                st.success(f"Found {len(matches):,} matching record(s).")
                st.dataframe(matches[useful].head(25), use_container_width=True, hide_index=True)
                if len(matches) > 25:
                    st.caption("Showing the first 25 matches.")

        with st.expander("Preview the dataset"):
            useful = [c for c in ["common name", "species", "class", "body mass (kg)", "brain size (kg)"] if c in data.columns]
            st.dataframe(data[useful].head(20), use_container_width=True, hide_index=True)
            st.caption("The full raw-data viewer and CSV download are available in the sidebar.")

        response_box("What does one row represent? Which variables look most useful for investigating animal traits?", "animal_q1")
        response_box("What animal did you search for? Was it present, and what did you learn from the result?", "animal_q2")

    elif part == 2:
        teacher_note(
            "How big are animals?",
            "Use body mass as the first quantitative variable, then introduce logarithmic scales because animal masses span many orders of magnitude.",
            "Start with the range and the linear histogram. Let students notice that most values are compressed before switching to the logarithmic view. Emphasise that the data have not changed — only the spacing on the axis has changed.",
            "12 min",
        )
        st.header("2 · How big are animals?")
        st.write(
            "We’ll begin with just **one variable: body mass**. Animal body masses cover an enormous range, from tiny invertebrates to very large mammals."
        )

        body = pd.to_numeric(data["body mass (kg)"], errors="coerce").dropna()
        body = body[body > 0]
        if not body.empty:
            smallest, largest = st.columns(2)
            smallest.metric("Smallest recorded body mass", f"{body.min():,.3g} kg")
            largest.metric("Largest recorded body mass", f"{body.max():,.3g} kg")

        bins = st.slider("Histogram bins", 5, 80, 25, key="curious_body_bins")
        scale = st.radio(
            "Horizontal-axis scale",
            ["Linear", "Logarithmic"],
            horizontal=True,
            key="curious_body_scale",
        )
        is_log = scale == "Logarithmic"
        st.plotly_chart(
            histogram(data, "body mass (kg)", log_x=is_log, bins=bins),
            use_container_width=True,
        )

        if not is_log:
            st.info(
                "**Look at the linear graph first.** Are most animal records easy to distinguish, or are they crowded into one part of the graph? "
                "When you are ready, switch the axis to **Logarithmic** and compare."
            )
        else:
            graph_guide(
                "On a logarithmic axis, equal distances represent multiplicative changes such as ×10 rather than equal additions.",
                "What became easier to see when you changed the scale?",
            )
            key_idea(
                "The animals did not change — only the axis did.",
                "Logarithmic scales are useful when values span many orders of magnitude.",
            )

        response_box("What changed when you switched from a linear to a logarithmic scale?", "animal_q3")

    elif part == 3:
        teacher_note(
            "Compare groups",
            "Use animal class as the first categorical variable and compare body-mass distributions between broad groups.",
            "Keep this visually constrained. We retain a logarithmic body-mass axis because students have just established why it is useful. Focus discussion on biological differences between groups rather than introducing extra graph types.",
            "8 min",
        )
        st.header("3 · Compare animal groups")
        st.write(
            "Now keep the same variable — **body mass** — but separate the animals into broad classes such as mammals, birds, reptiles and insects."
        )
        st.plotly_chart(
            class_comparison(data, graph_type="Individual points", log_y=True),
            use_container_width=True,
        )
        st.caption("Body mass stays on a logarithmic scale so very small and very large animals can be compared on the same graph.")
        response_box("Which animal groups tend to contain larger animals? Which contain smaller animals? What overlap can you see?", "animal_q4")

    elif part == 4:
        teacher_note(
            "Body mass and brain size",
            "Introduce the first two-variable relationship and scaffold the move from linear-linear to log-log axes.",
            "Show all animals together with no class colouring. Begin on linear axes and let students identify the compression problem. Then switch both axes to logarithmic and ask what relationship becomes visible. Explicitly state that the underlying data are unchanged.",
            "12 min",
        )
        st.header("4 · Body mass and brain size")
        st.write(
            "So far we have looked at body mass by itself. Now we’ll add a **second variable: brain size**. Each point on the scatter plot is one animal record with both measurements available."
        )

        scale = st.radio(
            "Axis scale",
            ["Linear–linear", "Log–log"],
            horizontal=True,
            key="curious_body_brain_scale",
        )
        is_log = scale == "Log–log"
        st.plotly_chart(
            body_brain_scatter(
                data,
                log_x=is_log,
                log_y=is_log,
                colour_by_class=False,
            ),
            use_container_width=True,
        )

        if not is_log:
            st.info(
                "**Start with the linear–linear graph.** What can you see clearly? What is difficult to see? "
                "Notice how many points are compressed near the lower-left corner, then switch to **Log–log**."
            )
        else:
            graph_guide(
                "Both axes are now logarithmic. The points are the same animals with the same measurements; only the axis spacing has changed.",
                "As body mass increases, does brain size tend to increase, decrease or show no overall relationship?",
            )
            key_idea(
                "Changing the representation can reveal a relationship that was difficult to see before.",
                "A log–log plot is especially useful when both variables span very large ranges.",
            )

        response_box("Describe the overall relationship between body mass and brain size. How did changing the axes affect what you could see?", "animal_q5")

    elif part == 5:
        teacher_note(
            "Compare relationships",
            "Add animal class only after students understand the overall body-mass/brain-size relationship.",
            "Use the same log–log relationship and colour by animal class. Keep the task guided: ask whether classes occupy different regions or appear to follow different patterns. Do not add open-ended variable selection here.",
            "10 min",
        )
        st.header("5 · Does the relationship look the same for every animal group?")
        st.write(
            "The overall pattern is useful, but different kinds of animals may not behave in exactly the same way. Now add **animal class** to the same body-mass and brain-size graph."
        )
        st.plotly_chart(
            body_brain_scatter(
                data,
                log_x=True,
                log_y=True,
                colour_by_class=True,
            ),
            use_container_width=True,
        )
        graph_guide(
            "Body mass and brain size remain on logarithmic axes. Colour now identifies animal class.",
            "Do different classes occupy different parts of the graph? Do they appear to follow similar or different relationships?",
        )
        response_box("What changes when you separate the body-mass/brain-size relationship by animal class?", "animal_q6")
        with st.expander("Advanced prompts"):
            st.write("Can you find humans? What does their position suggest about brain mass relative to body mass?")
            st.write("Why might there be multiple records for the same species? What does one row in the source database represent?")

    else:
        teacher_note(
            "Conclusion",
            "Consolidate the progression from one variable to groups, two-variable relationships and an additional explanatory variable.",
            "Return to the opening challenge. Ask students for one biological pattern and one data-science idea they now understand better.",
            "5 min",
        )
        st.header("Conclusion")
        st.success(
            "**Take-away:** The way we represent data changes what patterns are visible. We can start with one variable, compare groups, add a second variable to look for a relationship, and then ask whether that relationship changes across animal groups."
        )
        st.write(
            "You also worked with a real scientific dataset, where missing animals, missing measurements and biological variation are part of the evidence rather than mistakes to hide."
        )
        response_box("What is one pattern about animals you noticed, and one data-science choice that helped you see it?", "animal_conclusion")

    step_buttons(STEP_LABELS, "curious_step_selector", "curious_part", "curious_scroll_to_top", part, "curious")
