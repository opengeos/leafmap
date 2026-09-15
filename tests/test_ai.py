"""Tests for leafmap.ai - natural language mapping module.

These tests focus on the safety sandbox and code sanitization logic.
They do NOT require a real LLM API key.
"""

import pytest

from leafmap.ai import (
    _check_ast_safety,
    _sanitize_code,
    run_safe_code,
    SafetyError,
)


class TestAstSafety:
    """AST 白名单/黑名单静态校验。"""

    def test_allows_whitelisted_import(self):
        code = "import leafmap\nm = leafmap.Map(center=[35, 105], zoom=4)"
        # 不抛异常即通过
        _check_ast_safety(code)

    def test_allows_folium_import(self):
        _check_ast_safety("import folium\nm = folium.Map(location=[35, 105])")

    def test_rejects_os_import(self):
        code = "import os\nprint(os.getcwd())"
        with pytest.raises(SafetyError, match="禁止导入"):
            _check_ast_safety(code)

    def test_rejects_subprocess_import(self):
        with pytest.raises(SafetyError, match="禁止导入"):
            _check_ast_safety("import subprocess")

    def test_rejects_forbidden_attribute(self):
        code = "import leafmap\ngetattr(leafmap, '__file__')"
        with pytest.raises(SafetyError, match="禁止调用"):
            _check_ast_safety(code)

    def test_rejects_open_call(self):
        with pytest.raises(SafetyError, match="禁止调用"):
            _check_ast_safety("open('/etc/passwd')")

    def test_rejects_import_from_os(self):
        with pytest.raises(SafetyError, match="禁止导入"):
            _check_ast_safety("from os import system")


class TestSanitizeCode:
    """LLM 输出清理。"""

    def test_strips_markdown_fence(self):
        raw = "```python\nimport leafmap\nprint('hi')\n```"
        assert _sanitize_code(raw) == "import leafmap\nprint('hi')"

    def test_strips_prefix_text(self):
        raw = "好的，以下是代码：\nimport leafmap\nm = leafmap.Map()"
        cleaned = _sanitize_code(raw)
        assert cleaned.startswith("import leafmap")

    def test_keeps_clean_code(self):
        code = "import leafmap\nm = leafmap.Map()"
        assert _sanitize_code(code) == code


class TestRunSafeCode:
    """受限命名空间执行。"""

    def test_executes_whitelisted_code(self):
        result = run_safe_code("print('ok')\n")
        assert result["ok"] is True
        assert result["error"] is None

    def test_rejects_dangerous_code(self):
        # run_safe_code 的安全检查在 try 之外，危险代码直接抛 SafetyError
        with pytest.raises(SafetyError, match="禁止导入"):
            run_safe_code("import os\n")

    def test_output_path_created(self, tmp_path):
        target = tmp_path / "sub" / "map.html"
        code = "import leafmap\nm = leafmap.Map(center=[35, 105], zoom=4)\nm.to_html(OUTPUT_PATH)\n"
        result = run_safe_code(code, output_path=str(target))
        assert result["ok"] is True
        assert target.exists()

    def test_leafmap_real_execution(self, tmp_path):
        """真实 leafmap folium 后端端到端：建图 + 导出 HTML。"""
        target = tmp_path / "map.html"
        code = (
            "import leafmap\n"
            "m = leafmap.Map(center=[32.06, 118.80], zoom=6)\n"
            "m.to_html(OUTPUT_PATH)\n"
        )
        result = run_safe_code(code, output_path=str(target))
        assert result["ok"] is True, result.get("traceback")
        assert target.exists()
        content = target.read_text(encoding="utf-8")
        assert "leaflet" in content.lower() or "folium" in content.lower()
