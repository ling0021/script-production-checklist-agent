"""Deterministic checks: invalid inputs never become successful completion."""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import read_scene, compare_checklist, dispatch, validate_proposal


def complete_extraction():
    return {"characters": [{"value": "EVA", "evidence": "EVA closes the blue folder."},
                           {"value": "NOAH", "evidence": "NOAH lifts a silver camera and photographs the blue folder."}],
            "locations": [{"value": "COMMUNITY STUDIO", "evidence": "INT. COMMUNITY STUDIO - DAY"}],
            "props": [{"value": "blue folder", "evidence": "EVA closes the blue folder."},
                      {"value": "wooden table", "evidence": "EVA places a blue folder on the wooden table."},
                      {"value": "silver camera", "evidence": "NOAH lifts a silver camera and photographs the blue folder."}],
            "actions": [{"value": "closes the blue folder", "evidence": "EVA closes the blue folder."}]}


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.state = {"requested_scene": "complete", "finished": False}

    def test_read_success(self):
        observation = read_scene({"scene_id": "complete"}, self.state)
        self.assertTrue(observation["ok"])
        self.assertIn("COMMUNITY STUDIO", observation["data"]["text"])

    def test_unknown_scene_leaves_state_unchanged(self):
        before = copy.deepcopy(self.state)
        self.assertFalse(read_scene({"scene_id": "../../private"}, self.state)["ok"])
        self.assertEqual(before, self.state)

    def test_extra_arguments_rejected(self):
        self.assertFalse(read_scene({"scene_id": "complete", "path": "elsewhere"}, self.state)["ok"])

    def test_wrong_requested_scene(self):
        self.assertFalse(dispatch({"tool": "read_scene", "arguments": {"scene_id": "incomplete"}}, self.state)["ok"])

    def test_compare_before_read(self):
        self.assertFalse(compare_checklist({}, self.state)["ok"])

    def test_supported_comparison(self):
        read_scene({"scene_id": "complete"}, self.state)
        result = compare_checklist({"extraction": complete_extraction(), "uncertainties": []}, self.state)
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["status"], "ready_for_human_review")

    def test_invented_prop_rejected(self):
        read_scene({"scene_id": "complete"}, self.state)
        extraction = complete_extraction()
        extraction["props"].append({"value": "red umbrella", "evidence": "EVA carries a red umbrella."})
        self.assertFalse(compare_checklist({"extraction": extraction, "uncertainties": []}, self.state)["ok"])
        self.assertNotIn("comparison", self.state)

    def test_value_not_in_evidence_rejected(self):
        read_scene({"scene_id": "complete"}, self.state)
        extraction = complete_extraction()
        extraction["props"][0]["value"] = "green folder"
        self.assertFalse(compare_checklist({"extraction": extraction, "uncertainties": []}, self.state)["ok"])

    def test_missing_category_rejected(self):
        read_scene({"scene_id": "complete"}, self.state)
        extraction = complete_extraction()
        del extraction["locations"]
        self.assertFalse(compare_checklist({"extraction": extraction, "uncertainties": []}, self.state)["ok"])

    def test_incomplete_scene_flags_and_questions(self):
        read_scene({"scene_id": "incomplete"}, self.state)
        extraction = {"characters": [{"value": "EVA", "evidence": "EVA places the item on a wooden table."}],
                      "locations": [], "props": [{"value": "wooden table", "evidence": "EVA places the item on a wooden table."}],
                      "actions": [{"value": "places the item", "evidence": "EVA places the item on a wooden table."}]}
        uncertainty = {"category": "props", "evidence": "the item", "question": "What is the item?"}
        result = compare_checklist({"extraction": extraction, "uncertainties": [uncertainty]}, self.state)
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["status"], "needs_clarification")
        self.assertIn("Where does this scene take place?", result["data"]["questions"])
        self.assertIn("What is the item?", result["data"]["questions"])

    def test_premature_finish_blocked(self):
        self.assertFalse(dispatch({"tool": "finish", "arguments": {"status": "ready_for_human_review", "questions": []}}, self.state)["ok"])
        self.assertFalse(self.state["finished"])

    def test_finish_must_match_observation(self):
        read_scene({"scene_id": "complete"}, self.state)
        compare_checklist({"extraction": complete_extraction(), "uncertainties": []}, self.state)
        self.assertFalse(dispatch({"tool": "finish", "arguments": {"status": "needs_clarification", "questions": []}}, self.state)["ok"])
        self.assertTrue(dispatch({"tool": "finish", "arguments": {"status": "ready_for_human_review", "questions": []}}, self.state)["ok"])

    def test_tiny_quote_rejected(self):
        read_scene({"scene_id": "complete"}, self.state)
        extraction = complete_extraction()
        extraction["characters"] = [{"value": "E", "evidence": "E"}]
        self.assertFalse(compare_checklist({"extraction": extraction, "uncertainties": []}, self.state)["ok"])

    def test_uncertain_prop_is_separate(self):
        read_scene({"scene_id": "incomplete"}, self.state)
        extraction = complete_extraction()
        extraction = {key: [] for key in extraction}
        extraction["props"] = [{"value": "the item", "evidence": "EVA places the item on a wooden table."}]
        result = compare_checklist({"extraction": extraction, "uncertainties": [{"category": "props", "evidence": "the item", "question": "What is the item?"}]}, self.state)
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["checklist"]["props"], [])
        self.assertEqual(result["data"]["unresolved_references"][0]["value"], "the item")

    def test_transient_failure_does_not_fake_read(self):
        self.state["test_read_failures_remaining"] = 1
        self.assertFalse(read_scene({"scene_id": "complete"}, self.state)["ok"])
        self.assertNotIn("scene", self.state)
        self.assertTrue(read_scene({"scene_id": "complete"}, self.state)["ok"])

    def test_rejected_comparison_invalidates_previous_result(self):
        read_scene({"scene_id": "complete"}, self.state)
        compare_checklist({"extraction": complete_extraction(), "uncertainties": []}, self.state)
        self.assertFalse(compare_checklist({}, self.state)["ok"])
        self.assertNotIn("comparison", self.state)

    def test_unknown_tool(self):
        self.assertFalse(validate_proposal({"tool": "delete_files", "arguments": {}})[0])

    def test_multiple_actions_blocked(self):
        self.assertFalse(validate_proposal([{"tool": "read_scene", "arguments": {}}])[0])

    def test_invalid_question_rejected(self):
        read_scene({"scene_id": "complete"}, self.state)
        issue = {"category": "props", "evidence": "blue folder", "question": ""}
        self.assertFalse(compare_checklist({"extraction": complete_extraction(), "uncertainties": [issue]}, self.state)["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
