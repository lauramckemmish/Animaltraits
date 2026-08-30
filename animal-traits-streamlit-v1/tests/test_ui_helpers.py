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
    def columns(self, *_args, **_kwargs): return [Context(), Context(), Context()]
    def container(self, **_kwargs): return Context()
    def expander(self, label, **_kwargs): self.expanders.append(label); return Context()
    def button(self, label, **_kwargs): self.buttons.append(label); return False
    def info(self, *_args, **_kwargs): pass
    def success(self, *_args, **_kwargs): pass
    def write(self, *_args, **_kwargs): pass
    def markdown(self, *_args, **_kwargs): pass
    def caption(self, *_args, **_kwargs): pass
    def text_area(self, _label, *, key, **_kwargs): return self.session_state.setdefault(key, "")


class SharedContractTests(unittest.TestCase):
    def nav(self, stub, step=0):
        ui_helpers.step_buttons(["One", "Two"], "tab", "step", "scroll", step, "test")
        return stub.buttons

    def test_hard_reveal_persists_and_caller_can_withhold_content(self):
        stub = StreamlitStub()
        with patch.object(ui_helpers, "st", stub):
            revealed = ui_helpers.hard_reveal("Predict", "evidence", reveal_label="Reveal")
            self.assertFalse(revealed)
            self.assertNotIn("downstream", "downstream" if revealed else "")
            stub.session_state["evidence"] = True
            self.assertTrue(ui_helpers.hard_reveal("Predict", "evidence", reveal_label="Reveal"))
            self.assertTrue(ui_helpers.hard_reveal("Predict", "evidence", reveal_label="Reveal"))

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
