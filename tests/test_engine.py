"""
稷下学宫引擎单元测试

覆盖：
- persona.py：加载、解析触发点
- discussion.py：prompt 构建、用户发言注入
- moderator.py：点名解析
"""
import pytest
from pathlib import Path
from src.engine.persona import Persona, load_persona, _parse_trigger_points, PersonaNotFoundError
from src.engine.discussion import (
    Discussion, _build_system_prompt, _format_history, SpeechEntry
)


# ── persona.py ──────────────────────────────────────────────────────────────

class TestParseTrigerPoints:
    def test_parses_confucius_triggers(self):
        p = load_persona("confucius")
        assert len(p.trigger_points) == 4
        assert any("言行不一" in t for t in p.trigger_points)

    def test_returns_empty_for_missing_section(self):
        result = _parse_trigger_points("# 普通文档\n没有触发点字段")
        assert result == []

    def test_stops_at_next_heading(self):
        content = (
            "**被激怒的触发点**：\n"
            "- 触发点A\n"
            "- 触发点B\n"
            "\n"
            "**下一节标题**\n"
            "- 不应该被收集\n"
        )
        result = _parse_trigger_points(content)
        assert result == ["触发点A", "触发点B"]

    def test_all_personas_load_without_error(self):
        """所有人格文件都能正常加载，trigger_points 是 list（可空）"""
        personas_dir = Path("personas")
        for md_file in personas_dir.rglob("*.md"):
            slug = md_file.stem
            p = load_persona(slug)
            assert isinstance(p.trigger_points, list)

    def test_persona_not_found_raises(self):
        with pytest.raises(PersonaNotFoundError):
            load_persona("不存在的人格xyz")


# ── discussion.py ────────────────────────────────────────────────────────────

class TestBuildSystemPrompt:
    def setup_method(self):
        self.persona = load_persona("confucius")

    def test_contains_identity_anchor(self):
        prompt = _build_system_prompt(self.persona, "测试议题", ["孔子"])
        assert "身份锚定" in prompt
        assert "孔子" in prompt

    def test_contains_trigger_points(self):
        prompt = _build_system_prompt(self.persona, "测试议题", ["孔子"])
        assert "你的雷区" in prompt
        assert "言行不一" in prompt

    def test_opening_statement_at_end(self):
        prompt = _build_system_prompt(
            self.persona, "议题", ["孔子"],
            opening_statement="我的开场白"
        )
        assert "主持人开场" in prompt
        # 主持人开场必须在雷区之后
        assert prompt.index("主持人开场") > prompt.index("你的雷区")

    def test_no_opening_statement_when_none(self):
        prompt = _build_system_prompt(self.persona, "议题", ["孔子"])
        assert "主持人开场" not in prompt

    def test_no_trigger_section_when_empty(self):
        empty_persona = Persona(name="测试", content="内容", trigger_points=[])
        prompt = _build_system_prompt(empty_persona, "议题", ["测试"])
        assert "你的雷区" not in prompt


class TestFormatHistory:
    def test_empty_history(self):
        result = _format_history([])
        assert "尚无发言" in result

    def test_formats_persona_speech(self):
        history: list[SpeechEntry] = [
            {"name": "孔子", "text": "仁者爱人", "role": "persona"}
        ]
        result = _format_history(history)
        assert "孔子" in result
        assert "仁者爱人" in result

    def test_formats_user_speech(self):
        history: list[SpeechEntry] = [
            {"name": "你", "text": "这有道理吗", "role": "user"}
        ]
        result = _format_history(history)
        assert "你" in result
        assert "这有道理吗" in result


class TestInjectUserSpeech:
    def test_inject_appends_to_history(self, monkeypatch):
        # mock OpenAI client 避免真实 API 调用
        monkeypatch.setenv("GEMINI_API_KEY", "fake_key")
        monkeypatch.setattr(
            "src.engine.discussion.OpenAI",
            lambda **kwargs: None
        )
        p = load_persona("confucius")
        d = Discussion(personas=[p], topic="测试")
        d._client = None  # type: ignore

        d.inject_user_speech("这是用户的话")
        assert len(d.history) == 1
        assert d.history[0]["name"] == "你"
        assert d.history[0]["role"] == "user"
        assert d.history[0]["text"] == "这是用户的话"
