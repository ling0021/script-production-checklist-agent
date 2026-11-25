# Script Production Checklist Agent

Individual mini project - Ling Yang - CSYE 7374

A local language model reads a short fictional scene, extracts characters, locations,
props and actions, and compares them with a production checklist. Each item carries
an exact scene quote. Missing or unclear details become questions for a human.

## Requirements

- Python 3.10 or newer. Application and tests need no third-party Python packages.
- Ollama installed locally, with `qwen3:8b` downloaded.
- Internet is needed for the initial model download; scene processing stays local.
- A machine able to run an 8-billion-parameter model. Speed varies with hardware.

## Run

In a terminal, start Ollama (skip if its desktop service is already running):

```sh
ollama serve
```

In another terminal, download the model once:

```sh
ollama pull qwen3:8b
```

Open a terminal in this project folder, then run:

```sh
python3 agent.py --scene complete --output evidence/complete_report.json
python3 agent.py --scene incomplete --output evidence/incomplete_report.json
python3 -m unittest discover -s tests -v
python3 verify_reports.py
```

On Windows, use `python` if `python3` is unavailable. Rerunning a demo replaces
that report; copy the supplied evidence elsewhere first if you want to retain it.

## How the agent works

The program exposes two tools and one finish action. The model chooses one action
per turn; Python does not hard-code a read/compare/finish action sequence.

1. `read_scene({"scene_id": "complete"})` reads an allowed scene and returns text
   plus a content hash. Arbitrary file paths are rejected.
2. `compare_checklist({"extraction": {...}, "uncertainties": [...]})` checks the
   model's extraction against the four required categories and actual scene quotes.
   It returns a checklist, missing/uncertain issues, and clarification questions.
3. `finish({"status": "...", "questions": [...]})` is a control action, not a third
   scene-processing tool. Python accepts it only after comparison succeeds and its
   status and questions exactly match the checked observation.

The model receives the entire previous message history, including actual errors
and tool results. It can revise rejected actions. The loop stops at verified finish,
model-service failure, or eight steps. Stopping at a limit is not success.

### Example of a comparison argument

```json
{
  "tool": "compare_checklist",
  "arguments": {
    "extraction": {
      "characters": [{"value": "EVA", "evidence": "EVA closes the blue folder."}],
      "locations": [],
      "props": [{"value": "blue folder", "evidence": "EVA closes the blue folder."}],
      "actions": [{"value": "closes the blue folder", "evidence": "EVA closes the blue folder."}]
    },
    "uncertainties": []
  }
}
```

This shortened example illustrates the format; it is not the full demonstration output.

## Actual demonstrations

Three reports were generated with the same final program and local `qwen3:8b`,
temperature 0, seed 42, on November 24, 2026 (Pacific time). The JSON timestamps
use UTC. No prerecorded model responses are used by the runner.

| Case | Model turns | Checked status | Time |
| --- | --- | --- | --- |
| complete | 3 | ready_for_human_review | 11.23 s |
| incomplete | 3 | needs_clarification | 11.9 s |
| recovery | 4 | ready_for_human_review | 13.61 s |

The complete case follows read_scene -> compare_checklist -> finish. The incomplete
case has no named setting and uses "the item" without identifying it. Its confirmed
props contain only wooden table and silver camera; ambiguous references are not
confirmed production props. Python supplies the missing-location question from a
template. The model supplies the question about "the item". Python derives the
status from checked issues; finish requests must preserve that result.

The recovery experiment uses the same program with an explicit test flag:

```sh
python3 agent.py --scene complete --test-read-failure --output evidence/recovery_report.json
```

This injects exactly one transient read failure. It is a controlled test, NOT a real
filesystem outage. The model actually receives the error and chooses read_scene
again, then compare_checklist and finish. Python does not insert a retry action or
fabricate model responses. The error itself recommends retrying, so this shows
feedback-following within a constrained task, not independent recovery planning.

Normal calls have prerequisites: read before compare; compare before finish. Those
are execution guards, not evidence of unrestricted planning. The model performs
extraction, identifies uncertainty and proposes the next action. Python determines
the checked status and enforces completion. A finish status is not a free model
choice. The normal and recovery traces provide concrete evidence of differing
model-selected action sequences.

During development, the model omitted a stated scene-header location and once
misspelled an evidence quote. The missing-location observation could not by itself
guarantee correct extraction. Instructions now explicitly describe scene headings
and rechecking omissions. This is a development lesson, not a claim of measured
accuracy improvement; the supplied three reports come from the final version.

## Evidence and independent checks

- `evidence/complete_report.json`, `evidence/incomplete_report.json`,
  `evidence/recovery_report.json`: raw model
  responses, proposals, tool observations, status, timing and source hashes.
- `evidence/complete_console.txt`, `evidence/incomplete_console.txt`: actual console output.
- `evidence/independent_checks.json`: independent assertions against scene text and
  handwritten case expectations, not just the model's success statement.
- `evidence/unit_tests.txt`: 19 passing offline tests, including invalid input,
  unsupported details, tiny quotes, unresolved props, invalidated stale comparisons,
  one-shot fault injection, missing information, and premature or mismatched completion.
- `evidence/failure_case.json`: direct invalid-scene rejection with unchanged state;
  a tool unit check, not a live agent experiment. Invalid CLI scene IDs are rejected
  by argparse before the model runs. Use the explicit recovery command for a live failure demo.
- `evidence/*_view.png`: readable evidence views rendered from the saved JSON;
  these are not browser screenshots.

## Files

- `agent.py`: model prompt, structured action schema, local request and bounded loop.
- `tools.py`: two tools, argument/evidence checks, dispatcher and finish guard.
- `scenes/`: fictional complete and incomplete examples.
- `config/checklist.json`: required production categories.
- `tests/test_tools.py`: deterministic normal/failure tests.
- `verify_reports.py`: separate verification of saved live demonstrations.
- `deliverables/Project_Report.pdf`, `deliverables/Project_Presentation.pptx`:
  project explanation and classroom presentation.
- `DEMO_GUIDE.txt`: live demonstration and explanation prompts.

## Limitations

Exact quote matching, minimum lengths and word boundaries reject some unsupported
wording, but do not prove correct
classification or complete coverage of every scene fact. A real quote can still be
assigned to the wrong category. The independent case checks test the supplied
examples; they are not a general semantic verifier. A human reviews every checklist.

Only two scenes are registered in the allowlist. To try your own fictional material,
replace a sample scene or add an entry to `SCENES` in `tools.py`. Update independent
expectations if the test fixtures change. Do not use private production documents.

One final live run per condition is a demonstration, not a reliability estimate. Model versions
and machines can change results even with a fixed seed. This project does not
schedule shoots, perform purchases, update model weights, or automatically resolve
missing details. The "the one" reference is not separately flagged in the saved
incomplete run; human review must check whether it denotes the same item or a
different object. Multi-scene merging and an editor are possible later extensions.

## Course and rubric alignment

- Working task: complete scene checklist and missing-information questions, using fictional inputs.
- Agent behavior: model proposals and observations are visible; the injected read failure
  produces a real model-selected retry rather than an automatically inserted tool action.
- Validation: Python checks arguments/evidence and determines accepted completion.
- Tests: 19 unit checks plus independent verification of three final live reports.
- Demonstration: presentation shows actual JSON-derived views; raw console logs are retained.
- Explainability: distinguish model extraction/uncertainty from Python status rules;
  distinguish a successful tool call, checked finish, and full semantic correctness.

These reflect the saved classroom notes on model/Python roles and observed feedback
(September 16; October 7, 21 and 28; November 4), and the provided mini-project rubric.
Frameworks and browser-specific submission requirements from other assignments are
not added to this project. Human review and limited test coverage remain explicit.

## GitHub submission

Repository: https://github.com/ling0021/script-production-checklist-agent

Implementation and merge record: https://github.com/ling0021/script-production-checklist-agent/pull/1

The personal implementation branch is `project-implementation`. Use `main` for
the final working project. Submit the repository link, presentation and PDF.
