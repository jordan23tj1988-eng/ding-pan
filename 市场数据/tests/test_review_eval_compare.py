"""所有输出均为受控测试输出，不是模型调用结果。"""
import copy
import json
import pytest
from tests.test_review_eval_freeze import api, sandbox, read, write


def controlled(case, digest):
    return {"schema_version": 1, "kind": "controlled_test_output", "provider": "test-vendor", "model": "test-model-secret",
            "run_id": "controlled-001", "d": "20260904", "output": {
        "schema_version": 1, "d": "20260904", "case_hash": digest,
        "event": {"id": case["event_id"], "claim": "受控格式测试：温度为13.4，不能证明可交易性。",
        "evidence": [{"source_id": "fact:20260904", "field": "/facts/温度/value", "value": 13.4, "unit": "分"}],
        "counterevidence": [{"claim": "受控测试：成交额为20307.0亿元，另一个指标不能独立证明方向。", "references": [
            {"source_id": "fact:20260904", "field": "/facts/成交额亿/value", "value": 20307.0, "unit": "亿元"}]}],
        "limitations": ["受控测试输出。缺少历史as_of，语义与模型能力均未评审。"],
        "prediction": {"source_id": "fact:20260904", "field": "/facts/温度/value", "op": "gt", "threshold": 13.4,
                       "unit": "分", "due": "20260907", "probability": None}}}}

@pytest.fixture
def compare_case(api, sandbox):
    root, out = sandbox
    freeze = api.freeze_case(root, "20260904", out)
    assert freeze["status"] == "ok"
    candidate = out.parent / "test-model-secret.json"
    write(candidate, controlled(read(out / "case.json"), freeze["case_hash"]))
    return out / "case.json", candidate, out.parent / "comparison"

def compare(api, *args):
    assert hasattr(api, "evaluate_outputs"), "evaluate_outputs is missing"
    return api.evaluate_outputs(*args)

def test_blind_comparison_has_separate_mapping_and_null_semantics(api, compare_case):
    case, output, out = compare_case
    other = output.with_name("other.json"); write(other, read(output))
    result = compare(api, case, [output, other], out)
    assert result["status"] == "ok", result
    blind = read(out / "blind_review.json")
    assert {r["alias"] for r in blind["candidates"]} == {"A", "B"}
    assert all(r["structure"]["status"] == "pass" for r in blind["candidates"])
    assert all(r["semantic_score"] is None for r in blind["candidates"])
    assert blind["improvement_conclusion"] is None
    text = (out / "blind_review.json").read_text(encoding="utf-8")
    for secret in ["test-model-secret", "test-vendor", "controlled-001", str(output)]:
        assert secret not in text
    mapping = read(out / "private" / "mapping.json")
    assert {r["alias"] for r in mapping["candidates"]} == {"A", "B"}
    assert all(r["usage"]["cost"] is None and r["duration"] is None for r in mapping["candidates"])
    assert all(r["kind"] == "controlled_test_output" for r in mapping["candidates"])

@pytest.mark.parametrize("mutation,reason", [
    ("value", "value"), ("unit", "unit"), ("reference", "reference"), ("id", "id"),
    ("op", "op"), ("threshold", "threshold"), ("due", "due"), ("weekend", "due"),
    ("date", "d"), ("case_hash", "hash"), ("counter", "counterevidence"),
    ("probability", "probability"), ("confidence", "additional"), ("identity", "identity"),
    ("bool_value", "value"), ("judge_prediction", "fact"), ("no_limitations", "limitations")])
def test_reject_invalid_output_without_raw_identity_leak(api, compare_case, mutation, reason):
    case, output, out = compare_case
    doc = read(output); body=doc["output"]; event=body["event"]; pred=event["prediction"]
    if mutation == "value": event["evidence"][0]["value"] = 1340 # deliberate unit/value error injection
    elif mutation == "unit": event["evidence"][0]["unit"] = "%"
    elif mutation == "reference": event["evidence"][0]["field"] = "/facts/missing/value"
    elif mutation == "id": event["id"] = "wrong"
    elif mutation == "op": pred["op"] = "down"
    elif mutation == "threshold": pred["threshold"] = "13.4"
    elif mutation == "due": pred["due"] = "20260904"
    elif mutation == "weekend": pred["due"] = "20260905"
    elif mutation == "date": body["d"] = "20260907"
    elif mutation == "case_hash": body["case_hash"] = "wrong"
    elif mutation == "counter": event["counterevidence"] = []
    elif mutation == "probability": pred["probability"] = 80
    elif mutation == "confidence": pred["confidence"] = 80
    elif mutation == "identity": event["claim"] = "I am test-model-secret by test-vendor"
    elif mutation == "bool_value": event["evidence"][0]["value"] = True
    elif mutation == "judge_prediction": pred.update(source_id="logic判断:20260904", field="/判断/档位")
    elif mutation == "no_limitations": event["limitations"] = []
    write(output, doc)
    result = compare(api, case, [output], out)
    assert result["status"] == "fail", result
    candidate=read(out/"blind_review.json")["candidates"][0]
    assert reason in str(candidate["structure"]["errors"]), candidate
    assert candidate["output"] is None
    assert "test-model-secret" not in (out/"blind_review.json").read_text(encoding="utf-8")

def test_compare_rejects_tampered_case_before_reading_outputs(api, compare_case):
    case, output, out=compare_case
    case.write_bytes(case.read_bytes()+b" ")
    assert compare(api,case,[output],out)["status"] == "fail"
    assert not (out/"blind_review.json").exists()

def test_empty_input_is_failure(api, compare_case):
    case, _, out=compare_case
    assert compare(api,case,[],out)["status"] == "fail"

def test_usage_is_reported_only_when_provided(api, compare_case):
    case, output, out=compare_case
    doc=read(output); doc.update(started="2026-09-06T09:00:00+00:00", ended="2026-09-06T09:00:02.5+00:00",
                                 usage={"input_tokens":12,"output_tokens":3,"cost":0,"currency":"USD"})
    write(output,doc)
    assert compare(api,case,[output],out)["status"] == "ok"
    metric=read(out/"private"/"mapping.json")["candidates"][0]
    assert metric["duration"] == 2.5
    assert metric["usage"]["cost"] == 0
    assert metric["usage"]["input_tokens"] == 12
