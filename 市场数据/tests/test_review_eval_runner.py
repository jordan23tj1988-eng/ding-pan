"""只执行 Python 本地受控命令；不进行任何模型网络调用。"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import pytest
from tests.test_review_eval_freeze import api, sandbox, read, write, BASE
from tests.test_review_eval_compare import compare_case, controlled


def observation():
    return {"schema_version":1,"d":"20260904","run_id":"controlled-log","stage":"judge",
            "started":"2026-09-06T09:00:00+00:00","ended":"2026-09-06T09:00:01+00:00",
            "duration":1.0,"status":"ok","input_hash":"a"*64,"provider":None,"model":None,
            "tokens":None,"cost":None,"retries":0}

def append(api,*args):
    assert hasattr(api,"append_observation"), "append_observation missing"
    return api.append_observation(*args)

def run(api,*args,**kwargs):
    assert hasattr(api,"run_model"), "run_model missing"
    return api.run_model(*args,**kwargs)

def test_idempotent_append_and_conflicting_run_rejected(api,sandbox):
    root,out=sandbox
    row=observation()
    assert append(api,out,"20260904",row)["appended"] is True
    before=(out/"observability.jsonl").read_bytes()
    assert append(api,out,"20260904",row)["appended"] is False
    assert (out/"observability.jsonl").read_bytes()==before
    row["input_hash"]="b"*64
    assert append(api,out,"20260904",row)["status"]=="fail"
    assert (out/"observability.jsonl").read_bytes()==before

def test_no_run_reuse_across_dates(api,sandbox):
    root,out=sandbox; row=observation()
    assert append(api,out,"20260904",row)["status"]=="ok"
    row["d"]="20260907"; row["stage"]="other"
    assert append(api,out,"20260907",row)["status"]=="fail"

@pytest.mark.parametrize("bad",["duration","timestamps","d","tokens","cost","retries"])
def test_observation_rejects_invented_or_invalid_metrics(api,sandbox,bad):
    _,out=sandbox; row=observation()
    if bad=="duration": row["duration"]=900
    elif bad=="timestamps": row["ended"]="2026-09-05T00:00:00Z"
    elif bad=="d": row["d"]="20260907"
    elif bad=="tokens": row["tokens"]={"input_tokens":-1,"output_tokens":None}
    elif bad=="cost": row["cost"]=-1
    elif bad=="retries": row["retries"]=-1
    assert append(api,out,"20260904",row)["status"]=="fail"

def test_default_offline_never_executes_command(api,compare_case):
    case,_,out=compare_case
    marker=out.parent/"must-not-exist"
    command=[sys.executable,"-B","-c","from pathlib import Path; Path("+repr(str(marker))+").touch()"]
    result=run(api,out.parent,"20260904",case,out,command=command,run_id="offline-test")
    assert result["status"]=="offline",result
    assert not marker.exists()
    log=read_lines(out/"observability.jsonl")
    assert log[-1]["status"]=="offline" and log[-1]["cost"] is None

def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

def test_real_subprocess_timeout_is_logged(api,compare_case):
    case,_,out=compare_case
    result=run(api,out.parent,"20260904",case,out,command=[sys.executable,"-B","-c","import time; time.sleep(5)"],
               allow_execution=True,timeout=0.05,run_id="controlled-timeout",kind="controlled_test_output")
    assert result["status"]=="fail",result
    row=read_lines(out/"observability.jsonl")[-1]
    assert row["status"]=="timeout"
    assert 0 < row["duration"] < 3, "timeout left the interpreter child running"
    assert row["tokens"] is None and row["cost"] is None
    assert "timeout" in str(result["errors"])

def test_runner_stdin_json_stdout_import_and_duplicate_no_execution(api,compare_case):
    case,source,out=compare_case
    # Local echo of a clearly marked controlled response; no actual model usage.
    response=read(source)
    code="import json,sys; req=json.load(sys.stdin); assert req['d']=='20260904'; print("+repr(json.dumps(response,ensure_ascii=True))+")"
    command=[sys.executable,"-B","-c",code]
    kwargs=dict(command=command,allow_execution=True,run_id="controlled-echo",kind="controlled_test_output",provider="local-python",model="fixture-echo")
    result=run(api,out.parent,"20260904",case,out,**kwargs)
    assert result["status"]=="ok",result
    row=read_lines(out/"observability.jsonl")[-1]
    assert row["input_hash"]==read(case.parent/"hashes.json")["case_sha256"]
    assert row["tokens"] is None and row["cost"] is None
    assert read(out/"output.json")["kind"]=="controlled_test_output"
    before=(out/"observability.jsonl").read_bytes()
    again=run(api,out.parent,"20260904",case,out,**kwargs)
    assert again["status"]=="ok" and again["cached"] is True
    assert (out/"observability.jsonl").read_bytes()==before

def test_runner_wrong_date_fails_before_execution(api,compare_case):
    case,_,out=compare_case
    result=run(api,out.parent,"20260907",case,out,command=["never-execute"],allow_execution=True)
    assert result["status"]=="fail" and "date" in str(result["errors"])

@pytest.mark.parametrize("code",["print('not json')","import sys; sys.exit(3)"])
def test_runner_errors_are_logged_without_fabricated_usage(api,compare_case,code):
    case,_,out=compare_case
    result=run(api,out.parent,"20260904",case,out,command=[sys.executable,"-B","-c",code],
               allow_execution=True,kind="controlled_test_output")
    assert result["status"]=="fail"
    row=read_lines(out/"observability.jsonl")[-1]
    assert row["status"]=="fail" and row["cost"] is None

def test_freeze_and_compare_have_node_observability(api,compare_case):
    case,output,out=compare_case
    assert (case.parent/"observability.jsonl").exists(), "freeze node observation missing"
    assert api.evaluate_outputs(case,[output],out)["status"]=="ok"
    rows=read_lines(out/"observability.jsonl")
    assert rows[-1]["stage"]=="compare" and rows[-1]["provider"] is None

def test_cli_freeze_and_compare(api,sandbox):
    root,out=sandbox
    script=BASE/"root"/"review_eval.py"
    command=[sys.executable,"-B",str(script),"freeze","20260904","--root",str(root),"--out",str(out)]
    result=subprocess.run(command,capture_output=True,text=True,encoding="utf-8")
    assert result.stdout.strip(), "CLI freeze is missing"
    assert result.returncode==0,result.stderr+result.stdout
    frozen=json.loads(result.stdout)
    candidate=out.parent/"controlled.json"
    write(candidate,controlled(read(out/"case.json"),frozen["case_hash"]))
    result=subprocess.run([sys.executable,"-B",str(script),"compare","--case",str(out/"case.json"),"--outputs",str(candidate),"--out",str(out.parent/"compare")],capture_output=True,text=True,encoding="utf-8")
    assert result.returncode==0,result.stderr+result.stdout
    assert json.loads(result.stdout)["status"]=="ok"
