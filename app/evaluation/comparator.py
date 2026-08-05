"""Comparison helpers for planner evaluation."""

from __future__ import annotations

from app.models.plan import Plan

from .models import ComparisonResult


class PlanComparator:
    """Compare two planner outputs field by field."""

    def compare(self, rule_plan: Plan, llm_plan: Plan) -> ComparisonResult:
        intent_match = rule_plan.intent == llm_plan.intent
        tool_match = rule_plan.tool == llm_plan.tool
        parameters_match = rule_plan.parameters == llm_plan.parameters

        matched_fields = sum((intent_match, tool_match, parameters_match))
        overall_match = matched_fields == 3
        agreement_score = round((matched_fields / 3) * 100)

        return ComparisonResult(
            intent_match=intent_match,
            tool_match=tool_match,
            parameters_match=parameters_match,
            overall_match=overall_match,
            agreement_score=agreement_score,
        )