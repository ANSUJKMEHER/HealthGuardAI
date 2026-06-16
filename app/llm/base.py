"""
HealthGuard AI — Abstract LLM Provider Interface
All LLM providers must implement this interface for swappable AI backends.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    Implement this to add new AI backends (OpenAI, Anthropic, local models, etc.)
    """

    @abstractmethod
    def analyze_anomaly(self, metrics: Dict[str, Any], logs: list) -> Dict[str, Any]:
        """
        Analyze system metrics and logs to diagnose the root cause of an anomaly.

        Args:
            metrics: Current system metrics (cpu_percent, memory_mb, etc.)
            logs: Recent log entries from the monitored system

        Returns:
            Dict with keys:
                - thought_process (str): Chain-of-thought reasoning
                - root_cause (str): Identified root cause
                - confidence (float): 0.0 to 1.0
                - recommended_action (str): RESTART_SERVICE | CLEAR_CACHE | HEAL_REMOTE_SYSTEM | WAIT
        """
        pass

    @abstractmethod
    def generate_report(self, incident_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable incident post-mortem report.

        Args:
            incident_data: Full incident context including diagnosis and resolution

        Returns:
            Markdown-formatted incident report string
        """
        pass
