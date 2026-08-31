"""Focused acceptance tests for Animal Traits shared UI contracts."""

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
        self.expanders = []
        self.markdowns = []
        self.captions = []
    def columns(self, *_args, **_kwargs): return [Context(), Context(), Context()]
    def container(self, **_kwargs): return Context()
    def expander(self, label, **_kwargs): self.expanders.append(label); return Context()
    def button(self, label, **_kwargs): self.buttons.append(label); return False
    def info(self, *_args, **_kwargs): pass
    def success(self, *_args, **_kwargs): pass
    def write(self, *_args, **_kwargs): pass
    def markdown(self, body, **_kwargs): self.markdowns.append(body)
    def caption(self, body, **_kwargs): self.captions.append(body)
    def text_area(self, _label, *, key, **_kwargs): return self.session_state.setdefault(key, "")


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

    def test_think_is_a_non_blocking_labeled_cue(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            ui_helpers.think_prompt("What do you notice?")
            self.assertIn("Think", stub.markdowns[0])
            self.assertIn("Continue →", self.nav(stub))

    def test_completion_gate_blocks_continue_but_keeps_back(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            ui_helpers.completion_gate(False)
            buttons = self.nav(stub, step=1)
            self.assertIn("← Back", buttons)
            self.assertNotIn("Continue →", buttons)

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

    def test_response_and_teacher_toggle_preserve_caller_state(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            self.assertEqual(ui_helpers.response_box("Respond", "stage_response"), "")
            stub.session_state["stage_response"] = "An observation"
            ui_helpers.teacher_guidance("Stage", "Listen for evidence")
            self.assertEqual(stub.expanders, [])
            stub.session_state["teacher_view"] = True
            ui_helpers.teacher_guidance("Stage", "Listen for evidence")
            self.assertEqual(stub.expanders, ["Teacher guidance: Stage"])
            self.assertEqual(ui_helpers.response_box("Respond", "stage_response"), "An observation")

    def test_gate_is_transient_between_stage_renders(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            ui_helpers.completion_gate(False)
            self.assertNotIn("Continue →", self.nav(stub))
            stub.buttons.clear()
            self.assertIn("Continue →", self.nav(stub))


if __name__ == "__main__":
    unittest.main()
