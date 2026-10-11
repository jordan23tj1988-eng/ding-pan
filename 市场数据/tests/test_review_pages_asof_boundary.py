import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import review_pages


def test_asof_reader_stops_before_future_value(tmp_path):
    source = tmp_path / "_市场温度表.json"
    source.write_text(
        '{\n'
        ' "20261007": {"日": "20261007", "温度": 10},\n'
        ' "20261008": {"日": "20261008", "温度": 20},\n'
        ' "20261009": {\n'
        '  THIS FUTURE PAYLOAD IS INVALID JSON AND MUST NOT BE PARSED\n'
        '}\n'
        '}\n',
        encoding="utf-8",
    )

    data = review_pages._read_json_asof(source, "20261008")

    assert list(data) == ["20261007", "20261008"]
    assert data["20261008"]["温度"] == 20
    assert "20261009" not in data


def test_cycle_components_block_stale_lead_graph_when_target_missing(tmp_path):
    root = tmp_path
    learn = root / "_学习"
    learn.mkdir()
    learn.joinpath("_市场温度表.json").write_text(
        '{\n "20261008": {"日":"20261008", "成交额亿":null, "温度":26.3, "涨停数":43, "跌停数":13},\n'
        ' "20261009": {\n  "日":"20261009"\n }\n}\n',
        encoding="utf-8",
    )
    learn.joinpath("_情绪先行指标.json").write_text(
        '{\n "20260930": {"晋级":{"涨停数_净":52}},\n "20261009": {\n  "晋级":{"涨停数_净":999}\n }\n}\n',
        encoding="utf-8",
    )
    learn.joinpath("先行指标卡_20261008.html").write_text("<svg>STALE FUTURE-UNSAFE GRAPH</svg>", encoding="utf-8")
    day_dir = root / "20261008"
    day_dir.mkdir()
    (day_dir / "zt_pool.csv").write_text("代码,名称,连板数\n000001,测试股,2\n", encoding="utf-8")

    model = {"d": "20261008", "route": "cycle", "components": [], "complete": True,
             "limitations": [], "claims": []}
    review_pages._components(model, root)
    lead = next(component for component in model["components"] if component["id"] == "LEADIND")

    assert lead["status"] == "missing"
    assert lead["html"] is None
    assert "目标日先行指标缺失" in lead["issue"]
    assert all("STALE FUTURE-UNSAFE GRAPH" not in (component.get("html") or "")
               for component in model["components"])


def test_pure_renderer_receives_only_asof_temperature_rows(tmp_path):
    learn = tmp_path / "_学习"
    learn.mkdir()
    source = learn / "_市场温度表.json"
    source.write_text(
        '{\n "20261008": {"日":"20261008", "温度":26.3, "温度档":"偏冷", "涨停数":43, "跌停数":13, "炸板率":0.427, "成交额亿":null},\n'
        ' "20261009": {\n  "日":"20261009", "温度":999, "温度档":"未来"\n }\n}\n',
        encoding="utf-8",
    )

    renderer = review_pages._pure_renderer("index", tmp_path, "20261008")
    html = renderer.r_mach_temp("20261008")

    assert "26.3" in html
    assert "999" not in html
    assert "未来" not in html


def test_asof_prefix_hash_ignores_future_values(tmp_path):
    source = tmp_path / "_情绪先行指标.json"
    root = tmp_path
    prefix = '{\n "20261007": {"晋级": {"一进二率": 0.2}},\n'
    source.write_text(prefix + ' "20261009": {\n  "预测": "未来值A"\n }\n}\n', encoding="utf-8")
    first = review_pages._source_record(source, root, "20261008")["sha256"]
    source.write_text(prefix + ' "20261009": {\n  "预测": "未来值B"\n }\n}\n', encoding="utf-8")
    second = review_pages._source_record(source, root, "20261008")["sha256"]

    assert first == second
    assert review_pages._read_json_asof(source, "20261008") == {
        "20261007": {"晋级": {"一进二率": 0.2}}
    }


def test_asof_reader_rejects_invalid_date_and_future_embedded_date(tmp_path):
    source = tmp_path / "table.json"
    source.write_text('{\n "20261007": {"日": "20261009"}\n}\n', encoding="utf-8")

    try:
        review_pages._read_json_asof(source, "2026-10-08")
    except ValueError as exc:
        assert "日期格式" in str(exc)
    else:
        raise AssertionError("invalid as-of date was accepted")

    try:
        review_pages._read_json_asof(source, "20261008")
    except ValueError as exc:
        assert "未来记录" in str(exc)
    else:
        raise AssertionError("future embedded record date was accepted")
