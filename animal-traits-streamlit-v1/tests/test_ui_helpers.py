"""Focused acceptance tests for Animal Traits shared UI contracts."""

import inspect
import unittest
from unittest.mock import patch

import ui_helpers


class Context:
    def __enter__(self): return self
    def __exit__(self, *args): return False


class StreamlitStub:
    def __init__(self):
        self.session_state = {}
        self.buttons = []
        self.containers = []
        self.expanders = []
        self.expander_kwargs = []
        self.markdowns = []
        self.captions = []
        self.images = []
        self.writes = []
        self.column_args = []
        self.toggles = []
    def columns(self, *args, **kwargs):
        self.column_args.append((args, kwargs))
        count = len(args[0]) if args and isinstance(args[0], list) else (args[0] if args else 3)
        return [Context() for _ in range(count)]
    def container(self, **kwargs): self.containers.append(kwargs); return Context()
    def expander(self, label, **kwargs): self.expanders.append(label); self.expander_kwargs.append(kwargs); return Context()
    def button(self, label, **_kwargs): self.buttons.append(label); return False
    def info(self, *_args, **_kwargs): pass
    def success(self, *_args, **_kwargs): pass
    def write(self, body, **_kwargs): self.writes.append(body)
    def markdown(self, body, **_kwargs): self.markdowns.append(body)
    def caption(self, body, **_kwargs): self.captions.append(body)
    def image(self, image, **kwargs): self.images.append((image, kwargs))
    def text_area(self, _label, *, key, **_kwargs): return self.session_state.setdefault(key, "")
    def toggle(self, label, *, key, **_kwargs):
        self.toggles.append((label, key))
        return self.session_state.setdefault(key, False)


class SharedContractTests(unittest.TestCase):
    def nav(self, stub, step=0):
        ui_helpers.step_buttons(["One", "Two"], "tab", "step", "scroll", step, "test")
        return stub.buttons

    def test_hard_reveal_persists_and_blocks_continue_until_revealed(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            self.assertFalse(ui_helpers.hard_reveal("Predict", "evidence", reveal_label="Reveal"))
            self.assertNotIn("Continue →", self.nav(stub))
            stub.session_state["evidence"] = True
            self.assertTrue(ui_helpers.hard_reveal("Predict", "evidence", reveal_label="Reveal"))
            self.assertTrue(ui_helpers.hard_reveal("Predict", "evidence", reveal_label="Reveal"))

    def test_hard_reveal_leaves_cognitive_choreography_to_the_experience(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            ui_helpers.hard_reveal("Compare the two groups.", "evidence", reveal_label="Reveal")
            self.assertEqual(stub.markdowns, [])
            self.assertEqual(stub.captions, [])

            ui_helpers.hard_reveal(
                "Compare the two groups.",
                "labelled_evidence",
                reveal_label="Reveal",
                pre_reveal_label="Compare first",
                pre_reveal_guidance="Agree on a comparison before revealing the evidence.",
            )
            self.assertIn("Compare first", stub.markdowns[0])
            self.assertEqual(stub.captions, ["Agree on a comparison before revealing the evidence."])

    def test_semantic_prompts_name_the_cognitive_job_without_gating(self):
        stub = StreamlitStub()
        prompts = (
            (ui_helpers.notice_prompt, "Notice"),
            (ui_helpers.compare_prompt, "Compare"),
            (ui_helpers.predict_prompt, "Predict"),
            (ui_helpers.explain_prompt, "Explain"),
            (ui_helpers.conclude_prompt, "Conclude"),
            (ui_helpers.revise_prompt, "Revise"),
            (ui_helpers.recall_prompt, "Recall"),
        )
        with patch.object(ui_helpers, "st", stub):
            for render_prompt, label in prompts:
                render_prompt(f"{label} this evidence.")
            self.assertIn("Continue →", self.nav(stub))

        self.assertEqual(len(stub.markdowns), len(prompts))
        for (_, label), markdown in zip(prompts, stub.markdowns):
            self.assertIn(label, markdown)
        self.assertEqual(
            stub.writes[: len(prompts)],
            [f"{label} this evidence." for _, label in prompts],
        )

    def test_self_check_is_collapsed_and_never_blocks_continue(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            with ui_helpers.self_check("Check your reading"):
                stub.write("Compare this with your own observation.")
            self.assertIn("Continue →", self.nav(stub))

        self.assertEqual(stub.expanders, ["Self-check: Check your reading"])
        self.assertEqual(stub.expander_kwargs, [{"expanded": False}])

    def test_completion_gate_blocks_continue_but_keeps_back(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            ui_helpers.completion_gate(False)
            buttons = self.nav(stub, step=1)
            self.assertIn("← Back", buttons)
            self.assertNotIn("Continue →", buttons)

    def test_terminal_action_is_rendered_on_final_step(self):
        stub = StreamlitStub()
        terminal = lambda: None
        with patch.object(ui_helpers, "st", stub):
            ui_helpers.step_buttons(
                ["One", "Two"], "tab", "step", "scroll", 1, "test",
                terminal_action=terminal, terminal_label="Back to experiences",
            )
        self.assertEqual(stub.buttons, ["← Back", "Back to experiences"])

    def test_terminal_action_requires_a_label(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            with self.assertRaisesRegex(ValueError, "terminal_label"):
                ui_helpers.step_buttons(
                    ["One", "Two"], "tab", "step", "scroll", 1, "test",
                    terminal_action=lambda: None,
                )

    def test_completing_gate_enables_continue(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            ui_helpers.completion_gate(True)
            self.assertIn("Continue →", self.nav(stub))

    def test_multiple_gates_require_all_requirements(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            ui_helpers.completion_gate(False)
            ui_helpers.completion_gate(False)
            self.assertNotIn("Continue →", self.nav(stub))
            stub.buttons.clear()
            ui_helpers.completion_gate(True)
            ui_helpers.completion_gate(False)
            self.assertNotIn("Continue →", self.nav(stub))
            stub.buttons.clear()
            ui_helpers.completion_gate(True)
            ui_helpers.completion_gate(True)
            self.assertIn("Continue →", self.nav(stub))

    def test_facilitator_preparation_is_visibility_only_and_collapsed(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            self.assertEqual(ui_helpers.response_box("Respond", "stage_response"), "")
            stub.session_state["stage_response"] = "An observation"
            ui_helpers.facilitator_preparation("Listen for evidence")
            self.assertEqual(stub.expanders, [])
            stub.session_state[ui_helpers.FACILITATOR_NOTES_KEY] = True
            ui_helpers.facilitator_preparation("Listen for evidence")
            self.assertEqual(stub.expanders, ["For facilitators"])
            self.assertEqual(stub.expander_kwargs, [{"expanded": False}])
            self.assertEqual(ui_helpers.response_box("Respond", "stage_response"), "An observation")

    def test_facilitator_control_and_live_cues_use_canonical_labels(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            ui_helpers.facilitator_notes_control()
            self.assertEqual(stub.toggles, [("Facilitator notes", ui_helpers.FACILITATOR_NOTES_KEY)])
            self.assertFalse(ui_helpers.facilitator_notes_enabled())
            stub.session_state[ui_helpers.FACILITATOR_NOTES_KEY] = True
            for label in ui_helpers.FACILITATOR_LIVE_LABELS:
                ui_helpers.facilitator_live_cue(label, "A delivery decision.")
            with self.assertRaisesRegex(ValueError, "Unknown facilitator live cue"):
                ui_helpers.facilitator_live_cue("SKIP", "Not a canonical label.")

        self.assertEqual(len(stub.containers), 4)
        self.assertEqual(stub.writes[-4:], ["A delivery decision."] * 4)

    def test_facilitator_orientation_is_conditional_and_student_safe(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            ui_helpers.facilitator_orientation()
            self.assertEqual(stub.markdowns, [])
            self.assertEqual(stub.writes, [])
            stub.session_state[ui_helpers.FACILITATOR_NOTES_KEY] = True
            ui_helpers.facilitator_orientation()

        self.assertEqual(stub.markdowns, ["**Facilitator notes**"])
        orientation = stub.writes[-1]
        self.assertIn("walk through the learner experience", orientation)
        self.assertIn("Facilitator notes on", orientation)
        self.assertNotIn("answer", orientation.lower())

    def test_facilitator_notes_persist_across_routes_without_touching_learner_state(self):
        from experiences import router

        stub = StreamlitStub()
        stub.session_state.update(
            {
                ui_helpers.FACILITATOR_NOTES_KEY: True,
                "stage_response": "An observation",
                "curious_context_evidence": True,
                "curious_scientific_choice": "A careful interpretation",
            }
        )
        with patch.object(router, "st", stub):
            router.open_experience("Home")
            router.open_experience("CURIOUS")
            router.open_experience("Data Exploration Playground")
            router.open_experience("Home")

        self.assertTrue(stub.session_state[ui_helpers.FACILITATOR_NOTES_KEY])
        self.assertEqual(stub.session_state["stage_response"], "An observation")
        self.assertTrue(stub.session_state["curious_context_evidence"])
        self.assertEqual(stub.session_state["curious_scientific_choice"], "A careful interpretation")

    def test_visual_system_uses_one_navy_facilitator_family(self):
        import visual_system

        self.assertEqual(visual_system.SEMANTIC_TOKENS["facilitator"], "#294C70")
        self.assertNotIn("facilitator_prep", visual_system.SEMANTIC_TOKENS)
        self.assertNotIn("facilitator_live", visual_system.SEMANTIC_TOKENS)
        styles = inspect.getsource(visual_system.apply_visual_system)
        self.assertIn("--unsw-facilitator", styles)
        self.assertIn("st-key-facilitator_preparation", styles)
        self.assertIn("st-key-facilitator_live_", styles)
        self.assertIn("overflow-wrap:anywhere", styles)

    def test_gate_is_transient_between_stage_renders(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            ui_helpers.completion_gate(False)
            self.assertNotIn("Continue →", self.nav(stub))
            stub.buttons.clear()
            self.assertIn("Continue →", self.nav(stub))

    def test_sample_note_uses_the_callers_stable_instance_key(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            ui_helpers.sample_note(8, 10, key="playground_two_sample_note")

        self.assertIn({"key": "playground_two_sample_note"}, stub.containers)

    def test_role_image_accepts_shared_roles_and_rejects_unknown_roles(self):
        stub = StreamlitStub()
        roles = ("context", "evidence", "graph", "support", "hero")
        with patch.object(ui_helpers, "st", stub):
            for role in roles:
                ui_helpers.role_image("image.png", role=role, caption="Context", key=role)
            with self.assertRaisesRegex(ValueError, "Unknown image role"):
                ui_helpers.role_image("image.png", role="thumbnail")

        self.assertEqual(len(stub.images), 5)
        self.assertTrue(all(kwargs == {"caption": "Context", "width": "stretch"} for _, kwargs in stub.images))
        self.assertEqual(
            [container["key"] for container in stub.containers[-5:]],
            [f"role_image_{role}_{role}" for role in roles],
        )

    def test_media_text_pair_uses_role_specific_ratios_and_rejects_non_pair_roles(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            with ui_helpers.media_text_pair("context.png", role="context", caption="Context", key="context_pair"):
                stub.write("Associated explanation")
            with ui_helpers.media_text_pair("support.png", role="support", key="support_pair"):
                stub.write("Associated support")
            with self.assertRaisesRegex(ValueError, "context or support"):
                with ui_helpers.media_text_pair("graph.png", role="graph", key="invalid_pair"):
                    pass

        self.assertEqual(stub.column_args, [(([1, 1],), {"gap": "medium"}), (([1, 2],), {"gap": "medium"})])
        self.assertEqual(
            stub.images,
            [("context.png", {"caption": "Context", "width": "stretch"}), ("support.png", {"caption": None, "width": "stretch"})],
        )
        self.assertEqual(stub.writes[-2:], ["Associated explanation", "Associated support"])

    def test_visual_system_defines_responsive_media_pair_structure(self):
        import visual_system

        styles = inspect.getsource(visual_system.apply_visual_system)
        self.assertIn('class*="st-key-media_text_"', styles)
        self.assertIn("@media (max-width:700px)", styles)
        self.assertIn("flex-direction:column", styles)

    def test_visual_system_covers_shared_button_tab_and_focus_states(self):
        import visual_system

        styles = inspect.getsource(visual_system.apply_visual_system)
        self.assertIn('button[kind="secondary"]', styles)
        self.assertIn('stFormSubmitButton', styles)
        self.assertIn('stBaseButton-primaryFormSubmit', styles)
        self.assertIn('role="tablist"', styles)
        self.assertIn("flex-wrap:wrap", styles)


if __name__ == "__main__":
    unittest.main()
