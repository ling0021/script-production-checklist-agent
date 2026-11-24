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

Both supplied reports were generated with the same final program and local
`qwen3:8b`, temperature 0, seed 42, on November 24, 2026. No prerecorded model
responses are used by the runner.

| Case | Model-selected actions | Verified result | Time |
| --- | --- | --- | --- |
| Complete | read_scene, compare_checklist, finish | ready_for_human_review; no questions | 9.44 s |
| Incomplete | read_scene, compare_checklist, finish | needs_clarification; two questions | 13.17 s |

The incomplete scene has no named setting and uses "the item" without identifying
it. The model left locations empty and supplied a prop uncertainty. The tool
returned "Where does this scene take place?" and "What is the item referred to in
this scene?" The model then chose the clarification finish status and preserved
those questions. It did not invent a location or reuse the other scene's blue folder.

The visible order is the same in these two short demonstrations, but the model's
extraction, uncertainty decision and final status differ because of the observations.
The tool gates constrain valid execution; the loop itself does not automatically
invoke either tool or pick the final status for the model.

## Evidence and independent checks

- `evidence/complete_report.json`, `evidence/incomplete_report.json`: raw model
  responses, proposals, tool observations, status, timing and source hashes.
- `evidence/complete_console.txt`, `evidence/incomplete_console.txt`: actual console output.
- `evidence/independent_checks.json`: independent assertions against scene text and
  handwritten case expectations, not just the model's success statement.
- `evidence/unit_tests.txt`: 15 passing offline tests, including invalid input,
  unsupported details, missing information, and premature or mismatched completion.
- `evidence/failure_case.json`: direct invalid-scene rejection with unchanged state.
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

Exact substring matching blocks unsupported wording, but does not prove correct
classification or complete coverage of every scene fact. A real quote can still be
assigned to the wrong category. The independent case checks test the supplied
examples; they are not a general semantic verifier. A human reviews every checklist.

Only two scenes are registered in the allowlist. To try your own fictional material,
replace a sample scene or add an entry to `SCENES` in `tools.py`. Update independent
expectations if the test fixtures change. Do not use private production documents.

One live run per case is a demonstration, not a reliability estimate. Model versions
and machines can change results even with a fixed seed. This project does not
schedule shoots, perform purchases, update model weights, or automatically resolve
missing details. Multi-scene merging and an editor are possible later extensions.

## GitHub submission

Use a separate project repository. Create a personal branch, push it, open a pull
request into `main`, inspect the changes and merge it. The submitted repository's
`main` must contain the final working files. See `GITHUB_STEPS.txt` for commands.
