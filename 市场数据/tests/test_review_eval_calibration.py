"""合成事件/概率仅用于算法边界测试；结算行情来自真实 9/4 fact。"""
import hashlib
import pytest
from tests.test_review_eval_freeze import api, sandbox, read, write


def calibration_inputs(root, probability=0):
    # Explicit controlled test registration, not a historical model forecast.
    event={"schema_version":1,"id":"controlled-event", "d":"20260903", "due":"20260904",
           "registered_at":"2026-09-03T18:00:00+08:00", "mode":"controlled_test",
           "source_id":"fact", "field":"/facts/温度/value", "op":"gt", "threshold":13.2, "unit":"分"}
    forecast={"schema_version":1,"id":event["id"],"d":event["d"],"submitted_at":"2026-09-03T19:00:00+08:00",
              "probability":probability}
    path=root/"_学习"/"fact_20260904.json"
    label={"schema_version":1,"id":event["id"],"d":"20260904", "source_path":"_学习/fact_20260904.json",
           "field":event["field"], "unit":"分", "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
           "observed_at":"2026-09-04T19:02:54+08:00"}
    return event,forecast,label


def run(api,root,event,forecast,label,d="20260904",**kwargs):
    assert hasattr(api,"calibration_report"), "calibration_report is missing"
    return api.calibration_report(root,d,[event], [forecast] if forecast else [], [label] if label else [],**kwargs)

@pytest.mark.parametrize("p,expected",[(0,1.0),(1,0.0)])
def test_zero_one_probability_brier_boundaries_use_real_outcome(api,sandbox,p,expected):
    root,_=sandbox
    event,forecast,label=calibration_inputs(root,p)
    result=run(api,root,event,forecast,label,min_samples=1,min_bin_samples=1,bins=2)
    assert result["status"]=="ok",result
    assert result["brier"]==expected
    assert result["denominators"]["scored"]==1
    assert sum(b["n"] for b in result["bins"])==1
    assert result["score_scope"]=="controlled_test"
    assert result["improvement_conclusion"] is None

def test_no_probability_cannot_settle_subjective_confidence(api,sandbox):
    root,_=sandbox
    event,forecast,label=calibration_inputs(root,None)
    forecast["confidence"]=99
    result=run(api,root,event,forecast,label,min_samples=1)
    assert result["status"]=="ok",result
    assert result["brier"] is None
    assert result["exclusions"]["no_probability"]==1
    assert result["denominators"]["scored"]==0

@pytest.mark.parametrize("p",[-0.1,1.1,True,"0.9"])
def test_invalid_probability_is_failure(api,sandbox,p):
    root,_=sandbox; event,forecast,label=calibration_inputs(root,p)
    assert run(api,root,event,forecast,label)["status"]=="fail"

def test_minimum_samples_and_bin_denominators(api,sandbox):
    root,_=sandbox; event,forecast,label=calibration_inputs(root,0.8)
    result=run(api,root,event,forecast,label,min_samples=2,min_bin_samples=2)
    assert result["brier"] is None
    assert result["denominators"]["registered"]==1
    assert result["denominators"]["scored"]==1
    assert result["sample_gate"]=="insufficient"
    assert all(b["observed_rate"] is None for b in result["bins"])
    assert result["improvement_conclusion"] is None

@pytest.mark.parametrize("missing",["forecast","label","value"])
def test_missing_data_is_not_zero_or_success(api,sandbox,missing):
    root,_=sandbox; event,forecast,label=calibration_inputs(root,0.8)
    if missing=="forecast": forecast=None
    elif missing=="label": label=None
    else:
        path=root/"_学习"/"fact_20260904.json"; doc=read(path)
        doc["facts"]["温度"]["value"]=None; write(path,doc)
        label["sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
    result=run(api,root,event,forecast,label,min_samples=1)
    assert result["status"]=="ok",result
    assert result["brier"] is None
    assert result["exclusions"]["missing_"+missing]==1

def test_no_future_label_consumption_before_due(api,sandbox):
    root,_=sandbox; event,forecast,label=calibration_inputs(root,0.8)
    result=run(api,root,event,forecast,label,d="20260903",min_samples=1)
    assert result["status"]=="ok",result
    assert result["exclusions"]["pending"]==1
    assert result["denominators"]["scored"]==0

@pytest.mark.parametrize("bad",["late_registration","late_forecast","tamper","wrong_date","wrong_unit","wrong_field","future_observation"])
def test_preregistration_and_real_label_provenance_required(api,sandbox,bad):
    root,_=sandbox; event,forecast,label=calibration_inputs(root,0.8)
    if bad=="late_registration": event["registered_at"]="2026-09-04T20:00:00+08:00"
    elif bad=="late_forecast": forecast["submitted_at"]="2026-09-04T20:00:00+08:00"
    elif bad=="tamper": label["sha256"]="wrong"
    elif bad=="wrong_date": label["d"]="20260907"
    elif bad=="wrong_unit": label["unit"]="%"
    elif bad=="wrong_field": label["field"]="/facts/涨停数/value"
    elif bad=="future_observation": label["observed_at"]="2026-09-07T19:00:00+08:00"
    assert run(api,root,event,forecast,label)["status"]=="fail"

def test_duplicate_events_do_not_inflate_denominator(api,sandbox):
    root,_=sandbox; event,forecast,label=calibration_inputs(root,0.8)
    assert hasattr(api,"calibration_report"), "calibration_report is missing"
    result=api.calibration_report(root,"20260904",[event,event],[forecast],[label])
    assert result["status"]=="fail"
