"""Evaluation data models for planner observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models.plan import Plan
from app.planner.prompt_builder import PROMPT_BUILDER_VERSION

PLANNER_VERSION = "v0.1.0"


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    """Field-by-field comparison between two plans."""

    intent_match: bool
    tool_match: bool
    parameters_match: bool
    overall_match: bool
    agreement_score: int

    def to_dict(self) -> dict:
        return {
            "intent_match": self.intent_match,
            "tool_match": self.tool_match,
            "parameters_match": self.parameters_match,
            "overall_match": self.overall_match,
            "agreement_score": self.agreement_score,
        }


PlanComparison = ComparisonResult


@dataclass(frozen=True, slots=True)
class Observation:
    """A single planner evaluation record."""

    timestamp: str
    user_input: str
    rule_plan: Plan
    llm_plan: Plan
    production_plan: Plan
    comparison_result: ComparisonResult
    latency_ms: float
    planner_used: str
    planner_version: str = PLANNER_VERSION
    prompt_builder_version: str = PROMPT_BUILDER_VERSION
    rule_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0

    @classmethod
    def now(
        cls,
        *,
        user_input: str,
        rule_plan: Plan,
        llm_plan: Plan,
        production_plan: Plan,
        comparison_result: ComparisonResult,
        latency_ms: float,
        planner_used: str,
        planner_version: str = PLANNER_VERSION,
        prompt_builder_version: str = PROMPT_BUILDER_VERSION,
        rule_latency_ms: float = 0.0,
        llm_latency_ms: float = 0.0,
    ) -> "Observation":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_input=user_input,
            rule_plan=rule_plan,
            llm_plan=llm_plan,
            production_plan=production_plan,
            comparison_result=comparison_result,
            latency_ms=latency_ms,
            planner_used=planner_used,
            planner_version=planner_version,
            prompt_builder_version=prompt_builder_version,
            rule_latency_ms=rule_latency_ms,
            llm_latency_ms=llm_latency_ms,
        )

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "user_input": self.user_input,
            "planner_version": self.planner_version,
            "prompt_builder_version": self.prompt_builder_version,
            "rule_plan": {
                "intent": self.rule_plan.intent,
                "tool": self.rule_plan.tool,
                "parameters": self.rule_plan.parameters,
            },
            "llm_plan": {
                "intent": self.llm_plan.intent,
                "tool": self.llm_plan.tool,
                "parameters": self.llm_plan.parameters,
            },
            "production_plan": {
                "intent": self.production_plan.intent,
                "tool": self.production_plan.tool,
                "parameters": self.production_plan.parameters,
            },
            "comparison_result": self.comparison_result.to_dict(),
            "latency_ms": self.latency_ms,
            "planner_used": self.planner_used,
            "rule_latency_ms": self.rule_latency_ms,
            "llm_latency_ms": self.llm_latency_ms,
        }