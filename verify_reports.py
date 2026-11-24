"""Independent Python checks against the actual scenes and handwritten expectations."""
import hashlib
import json
from pathlib import Path
from tools import ROOT, CATEGORIES


def verify(scene_id):
    report = json.loads((ROOT / "evidence" / (scene_id + "_report.json")).read_text())
    text = (ROOT / "scenes" / (scene_id + ".txt")).read_text()
    assert report["verified_completion"] is True, "Agent did not reach verified finish"
    assert report["stop_reason"] == "finish_verified"
    assert report["program_sha256"] == hashlib.sha256((ROOT / "agent.py").read_bytes()).hexdigest()
    assert report["tools_sha256"] == hashlib.sha256((ROOT / "tools.py").read_bytes()).hexdigest()
    assert report["checklist_sha256"] == hashlib.sha256((ROOT / "config" / "checklist.json").read_bytes()).hexdigest()
    result = report["result"]
    assert result["scene_sha256"] == hashlib.sha256(text.encode()).hexdigest()
    tools = [turn["proposal"]["tool"] for turn in report["trace"] if turn["proposal"]]
    assert "read_scene" in tools and "compare_checklist" in tools and tools[-1] == "finish"
    successful = [t for t in report["trace"] if t["proposal"] and t["proposal"]["tool"] == "compare_checklist" and t["observation"]["ok"]]
    assert successful[-1]["observation"]["data"] == result
    assert report["trace"][-1]["proposal"]["arguments"]["questions"] == result["questions"]
    for category in CATEGORIES:
        for item in result["checklist"][category]:
            assert item["evidence"] in text
            assert item["value"].casefold() in item["evidence"].casefold()
    def values(category):
        return {item["value"].casefold() for item in result["checklist"][category]}
    assert {"eva", "noah"} <= values("characters"), "Missing expected character"
    assert any("silver camera" in v for v in values("props")), "Missing camera"
    assert any("table" in v for v in values("props")), "Missing table"
    assert len(result["checklist"]["actions"]) >= 2, "Expected at least two scene actions"
    if scene_id == "complete":
        assert result["status"] == "ready_for_human_review"
        assert any("community studio" in v for v in values("locations"))
        assert any("blue folder" in v for v in values("props"))
        assert not result["issues"] and not result["questions"]
    else:
        assert result["status"] == "needs_clarification"
        assert not values("locations"), "Location must not be invented"
        assert any(i["category"] == "locations" and i["status"] == "missing" for i in result["issues"])
        assert any(i["category"] == "props" and i["status"] == "uncertain" for i in result["issues"])
        assert any("where" in q.casefold() for q in result["questions"])
        assert any("item" in q.casefold() for q in result["questions"])
        assert not any("folder" in v for v in values("props")), "Must not import the prop from the other scene"
    return {"case": scene_id, "independent_check": "PASS", "steps": len(report["trace"]),
            "status": result["status"], "questions": result["questions"],
            "elapsed_seconds": report["elapsed_seconds"]}


if __name__ == "__main__":
    checks = [verify("complete"), verify("incomplete")]
    (ROOT / "evidence" / "independent_checks.json").write_text(json.dumps(checks, indent=2))
    print(json.dumps(checks, indent=2))
