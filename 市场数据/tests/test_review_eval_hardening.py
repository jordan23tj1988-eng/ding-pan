"""边界回归：受控格式/身份注入，不产生模型能力结论。"""
import json
from pathlib import Path
import pytest
from tests.test_review_eval_freeze import api,sandbox,read,write,BASE
from tests.test_review_eval_compare import compare_case,controlled
from tests.test_review_eval_runner import read_lines

@pytest.mark.parametrize("invalid",[[],None,"invalid",7])
def test_non_object_json_returns_uniform_failure(api,compare_case,invalid):
    case,candidate,out=compare_case
    write(candidate,invalid)
    result=api.evaluate_outputs(case,[candidate],out)
    assert result["status"]=="fail"
    assert result["d"]=="20260904" and result["errors"]

@pytest.mark.parametrize("name",["A.json","B.json","out.json"])
def test_short_external_filenames_do_not_trigger_identity_false_positive(api,compare_case,name):
    case,candidate,out=compare_case
    doc=read(candidate)["output"]
    short=candidate.with_name(name); write(short,doc)
    result=api.evaluate_outputs(case,[short],out)
    assert result["status"]=="ok",result

def test_failed_freeze_records_real_stage_timing(api,sandbox):
    root,out=sandbox
    (root/"_学习"/"theme判断_20260904.json").unlink()
    result=api.freeze_case(root,"20260904",out)
    assert result["status"]=="fail"
    assert (out/"observability.jsonl").exists(),"failed freeze observation missing"
    row=read_lines(out/"observability.jsonl")[-1]
    assert row["stage"]=="freeze" and row["status"]=="fail" and row["cost"] is None

def test_failed_compare_hash_check_records_failure(api,compare_case):
    case,candidate,out=compare_case
    case.write_bytes(case.read_bytes()+b" ")
    assert api.evaluate_outputs(case,[candidate],out)["status"]=="fail"
    assert (out/"observability.jsonl").exists(),"failed verify/compare observation missing"
    row=read_lines(out/"observability.jsonl")[-1]
    assert row["stage"]=="compare" and row["status"]=="fail"

def test_contract_matches_frozen_schema_and_documents_null_gates(api,sandbox):
    contract=BASE/"root"/"_契约"/"评估契约.v1.json"
    assert contract.exists(),"evaluation contract missing"
    root,out=sandbox
    assert api.freeze_case(root,"20260904",out)["status"]=="ok"
    spec=read(contract)
    assert spec["schema_version"]==1
    assert spec["output_schema"]==read(out/"case.json")["output_schema"]
    assert spec["semantic_score_default"] is None
    assert spec["cost_without_usage"] is None
    assert spec["calibration"]["min_samples"]==30

def test_foreign_path_cannot_overwrite_source_while_runner_executes(api,compare_case):
    case,candidate,out=compare_case
    result=api.run_model(out,"20260904",case,out.parent/"escaped",command=["never"],allow_execution=True)
    assert result["status"]=="fail"

@pytest.mark.parametrize("field",["meta","judgment"])
def test_malformed_legacy_metadata_is_uniform_failure(api,sandbox,field):
    root,out=sandbox
    path=root/"_学习"/"auction判断_20260904.json"; doc=read(path)
    if field=="meta": doc["meta"]=[]
    else: doc["判断"]=[]
    write(path,doc)
    assert api.freeze_case(root,"20260904",out)["status"]=="fail"
