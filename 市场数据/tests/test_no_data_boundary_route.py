# -*- coding: utf-8 -*-
"""回归测试：“数据边界”小模块在龙虎榜路必须永久消失，且只对 lhb 路生效(2026-09-12 用户拍板)。

防复发三层锁中“源头层”由本测试守住：review_pages.py 的 LIMITS_HIDDEN_ROUTES，
即使 limitations 数据非空，lhb 页也不再渲染该模块；其余路行为不变(数据/展示都保留)。
"""
import importlib.util
import unittest
from pathlib import Path

BASE = Path(r"D:/股票数据/市场数据")
REVIEW_PAGES = BASE / "review_pages.py"
DATE = "20260910"
SAMPLE_LIMIT = "兼容导入旧判断；原文立场未重新验证。"


def load_review_pages():
    spec = importlib.util.spec_from_file_location("review_pages_nodb_test", REVIEW_PAGES)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class NoDataBoundaryRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rp = load_review_pages()
        cls.contract = cls.rp._contract(BASE)

    def _render(self, route):
        model = self.rp.build_page_model(BASE, DATE, route)
        # 强制非空 limitations：证明“不渲染”是路由规则而非无数据
        model["limitations"] = [SAMPLE_LIMIT]
        return self.rp._render(model, self.contract), model

    def test_lhb_route_never_renders_data_boundary(self):
        html, model = self._render("lhb")
        self.assertEqual(model["limitations"], [SAMPLE_LIMIT])
        self.assertNotIn("数据边界", html)
        self.assertIn("lhb", self.rp.LIMITS_HIDDEN_ROUTES)

    def test_other_routes_still_render_limits(self):
        for route in ("auction", "logic", "cycle"):
            with self.subTest(route=route):
                html, _model = self._render(route)
                self.assertIn("数据边界", html)

    def test_limits_data_kept_in_model(self):
        _html, model = self._render("lhb")
        self.assertTrue(model["limitations"], "limitations 数据必须保留(供审计/门禁读取)，只是不渲染")


if __name__ == "__main__":
    unittest.main()
