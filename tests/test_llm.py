"""
Tests for LLM provider interface and prompt templates.
"""

from app.llm.base import LLMProvider
from app.llm.fallback_provider import FallbackProvider
from app.llm.prompts import DIAGNOSTICIAN_SYSTEM_PROMPT, REPORTER_SYSTEM_PROMPT


class TestLLMInterface:
    """Test that LLM providers implement the required interface."""

    def test_fallback_implements_interface(self):
        """FallbackProvider should be a valid LLMProvider."""
        provider = FallbackProvider()
        assert isinstance(provider, LLMProvider)

    def test_interface_methods_exist(self):
        """LLMProvider should define required abstract methods."""
        import inspect
        methods = [m for m, _ in inspect.getmembers(LLMProvider, predicate=inspect.isfunction)]
        assert "analyze_anomaly" in methods
        assert "generate_report" in methods


class TestPromptTemplates:
    """Test prompt template quality and structure."""

    def test_diagnostician_prompt_has_required_sections(self):
        """Diagnostician prompt should include key sections."""
        assert "OBJECTIVE" in DIAGNOSTICIAN_SYSTEM_PROMPT
        assert "DIAGNOSTIC RULES" in DIAGNOSTICIAN_SYSTEM_PROMPT
        assert "ALLOWED ACTIONS" in DIAGNOSTICIAN_SYSTEM_PROMPT
        assert "OUTPUT FORMAT" in DIAGNOSTICIAN_SYSTEM_PROMPT
        assert "JSON" in DIAGNOSTICIAN_SYSTEM_PROMPT

    def test_diagnostician_prompt_lists_safe_actions(self):
        """Prompt should explicitly list only safe actions."""
        assert "RESTART_SERVICE" in DIAGNOSTICIAN_SYSTEM_PROMPT
        assert "CLEAR_CACHE" in DIAGNOSTICIAN_SYSTEM_PROMPT
        assert "HEAL_REMOTE_SYSTEM" in DIAGNOSTICIAN_SYSTEM_PROMPT
        assert "WAIT" in DIAGNOSTICIAN_SYSTEM_PROMPT
        # Should NOT contain dangerous actions
        assert "DELETE" not in DIAGNOSTICIAN_SYSTEM_PROMPT
        assert "DROP" not in DIAGNOSTICIAN_SYSTEM_PROMPT

    def test_reporter_prompt_has_structure(self):
        """Reporter prompt should define report structure."""
        assert "GUIDELINES" in REPORTER_SYSTEM_PROMPT
        assert "Markdown" in REPORTER_SYSTEM_PROMPT

    def test_prompts_are_not_empty(self):
        """Prompts should have substantial content."""
        assert len(DIAGNOSTICIAN_SYSTEM_PROMPT) > 500
        assert len(REPORTER_SYSTEM_PROMPT) > 100
