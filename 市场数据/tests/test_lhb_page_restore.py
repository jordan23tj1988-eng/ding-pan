import importlib.util
import re
import unittest
from pathlib import Path


BASE = Path(r"D:/股票数据/市场数据")
SITE = BASE / "复盘/盯盘台/lhb.html"
RESTORE = BASE / "restore_lhb_page.py"


def load_restore():
    spec = importlib.util.spec_from_file_location("restore_lhb_page_test", RESTORE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class LhbPageRestoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_restore()
        cls.current = SITE.read_text(encoding="utf-8")

    def test_build_is_golden_front_four_plus_two_evolution(self):
        page = self.mod.build_page("20260910", self.current)
        self.assertEqual(len(self.mod._evolution_sections(page)), 2)
        self.assertNotIn('<section id="', page)
        self.assertTrue(all(f"<h2>{n} " in page for n in "一二三四五六"))
        self.assertLess(page.find("<h2>四 "), page.find('<section class="evolution"'))
        self.assertEqual(page.count("<div"), page.count("</div>"))
        self.assertEqual(page.count("<!--FUNDTEMP-->"), 1)
        self.assertEqual(page.count("<!--/FUNDTEMP-->"), 1)
        self.assertEqual(page.count("<!--LHBLEDGER-->"), 1)
        self.assertEqual(page.count("<!--/LHBLEDGER-->"), 1)

    def test_evolution_sections_are_preserved_byte_for_byte(self):
        source = self.mod._renumber_evolution(
            self.mod._evolution_sections(self.current)[:2]
        )
        page = self.mod.build_page("20260910", self.current)
        self.assertEqual(self.mod._evolution_sections(page), source)

    def test_no_data_boundary_module_in_output(self):
        """“数据边界”小模块已下线(2026-09-12)：黄金版工程不含它，输出出现即失败。"""
        page = self.mod.build_page("20260910", self.current)
        self.assertNotIn("数据边界", page)

    def test_data_boundary_inherited_from_current_is_stripped(self):
        """复发防线：当日发布页若带回“数据边界”，恢复器必须剥离而不是继承。"""
        card = ('<div class="card"><b>数据边界</b><ul>'
                '<li>兼容导入旧判断；原文立场未重新验证。</li></ul></div>')
        i = self.current.find('<h2>一')
        self.assertGreater(i, 0)
        polluted = self.current[:i] + card + "\n" + self.current[i:]
        page = self.mod.build_page("20260910", polluted)
        self.assertNotIn("数据边界", page)
        self.assertEqual(self.mod._strip_data_boundary(card), "")

    def test_missing_evolution_refuses_overwrite(self):
        stripped = re.sub(
            r"\n?<section class=\"evolution\"[^>]*>.*?</section>\n?",
            "\n",
            self.current,
            flags=re.S,
        )
        old_index = self.mod.INDEX
        self.mod.INDEX = BASE / "_tmp/does-not-exist-index.html"
        try:
            with self.assertRaises(RuntimeError):
                self.mod.build_page("20260910", stripped)
        finally:
            self.mod.INDEX = old_index


if __name__ == "__main__":
    unittest.main()
