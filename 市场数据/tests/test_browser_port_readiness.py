"""TEST ONLY: deterministic filesystem race injection; not browser acceptance."""
from pathlib import Path
from types import SimpleNamespace
import pytest
import review_publish as pub


def test_waits_for_readable_complete_portfile(tmp_path,monkeypatch):
    portfile=tmp_path/'DevToolsActivePort'
    states=iter([PermissionError('TEST sharing violation'),'','31415\n','31415\n/devtools/browser/TEST-ID\n'])
    reads=[]
    def read(self,*args,**kwargs):
        assert self==portfile
        value=next(states);reads.append(value)
        if isinstance(value,Exception):raise value
        return value
    monkeypatch.setattr(Path,'read_text',read)
    assert pub._wait_devtools_port(SimpleNamespace(poll=lambda:None),portfile,timeout=1)==31415
    assert len(reads)==4


def test_permanent_denial_is_not_a_pass(tmp_path,monkeypatch):
    def denied(self,*args,**kwargs):
        raise PermissionError('TEST permanently locked')
    monkeypatch.setattr(Path,'read_text',denied)
    with pytest.raises(TimeoutError,match='PermissionError'):
        pub._wait_devtools_port(SimpleNamespace(poll=lambda:None),tmp_path/'DevToolsActivePort',timeout=.01)


def test_exited_chrome_cannot_use_stale_portfile(tmp_path):
    portfile=tmp_path/'DevToolsActivePort'
    portfile.write_text('31415\n/devtools/browser/TEST-ID\n',encoding='utf-8')
    with pytest.raises(RuntimeError,match='Chrome exited'):
        pub._wait_devtools_port(SimpleNamespace(poll=lambda:3),portfile,timeout=1)


@pytest.mark.parametrize('payload',[None,'31415\n','0\n/devtools/browser/TEST\n','65536\n/devtools/browser/TEST\n'])
def test_missing_partial_or_invalid_port_fails_closed(tmp_path,payload):
    portfile=tmp_path/'DevToolsActivePort'
    if payload is not None:portfile.write_text(payload,encoding='utf-8')
    with pytest.raises(TimeoutError):
        pub._wait_devtools_port(SimpleNamespace(poll=lambda:None),portfile,timeout=.01)
