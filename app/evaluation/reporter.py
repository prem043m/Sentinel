"""Simple reporting utilities for planner observations."""

from __future__ import annotations

from dataclasses import dataclass

from .storage import JSONLObservationStorage


@dataclass(frozen=True, slots=True)
class ObservationReport:
    total_observations: int
    agreement_rate: float
    intent_agreement_rate: float
    tool_agreement_rate: float
    parameter_agreement_rate: float
    llm_better_count: int
    rule_better_count: int
    unknown_count: int
    average_execution_latency_ms: float
    average_rule_latency_ms: float
    average_llm_latency_ms: float


class ObservationReporter:
    """Build lightweight summaries from stored observations."""

    def __init__(self, storage: JSONLObservationStorage) -> None:
        self._storage = storage

    def build_report(self) -> ObservationReport:
        records = self._storage.read_all()

        if not records:
            return ObservationReport(
                total_observations=0,
                agreement_rate=0.0,
                intent_agreement_rate=0.0,
                tool_agreement_rate=0.0,
                parameter_agreement_rate=0.0,
                llm_better_count=0,
                rule_better_count=0,
                unknown_count=0,
                average_execution_latency_ms=0.0,
                average_rule_latency_ms=0.0,
                average_llm_latency_ms=0.0,
            )

        total = len(records)

        comparison_key = "comparison_result" if "comparison_result" in records[0] else "comparison"
        production_key = "production_plan" if "production_plan" in records[0] else "execution_plan"

        identical_count = sum(1 for record in records if record[comparison_key]["overall_match" if comparison_key == "comparison_result" else "identical"])
        intent_count = sum(1 for record in records if record[comparison_key]["intent_match"])
        tool_count = sum(1 for record in records if record[comparison_key]["tool_match"])
        parameter_count = sum(1 for record in records if record[comparison_key]["parameters_match"])

        rule_better_count = 0
        llm_better_count = 0
        unknown_count = 0

        for record in records:
            rule_plan = record["rule_plan"]
            llm_plan = record["llm_plan"]
            production_plan = record[production_key]

            rule_matches = rule_plan == production_plan
            llm_matches = llm_plan == production_plan

            if rule_matches and not llm_matches:
                rule_better_count += 1
            elif llm_matches and not rule_matches:
                llm_better_count += 1
            else:
                unknown_count += 1

        execution_latency = sum(
            record.get("latency_ms", record.get("execution_latency_ms", 0.0))
            for record in records
        )
        rule_latency = sum(record.get("rule_latency_ms", record.get("rule_planner_latency_ms", 0.0)) for record in records)
        llm_latency = sum(record.get("llm_latency_ms", record.get("llm_planner_latency_ms", 0.0)) for record in records)

        return ObservationReport(
            total_observations=total,
            agreement_rate=round(identical_count / total, 3),
            intent_agreement_rate=round(intent_count / total, 3),
            tool_agreement_rate=round(tool_count / total, 3),
            parameter_agreement_rate=round(parameter_count / total, 3),
            llm_better_count=llm_better_count,
            rule_better_count=rule_better_count,
            unknown_count=unknown_count,
            average_execution_latency_ms=round(execution_latency / total, 1),
            average_rule_latency_ms=round(rule_latency / total, 1),
            average_llm_latency_ms=round(llm_latency / total, 1),
        )

    def format_report(self) -> str:
        report = self.build_report()

        return (
            "Planner evaluation report\n"
            f"- observations: {report.total_observations}\n"
            f"- agreement rate: {report.agreement_rate:.3f}\n"
            f"- intent agreement: {report.intent_agreement_rate:.3f}\n"
            f"- tool agreement: {report.tool_agreement_rate:.3f}\n"
            f"- parameter agreement: {report.parameter_agreement_rate:.3f}\n"
            f"- llm better count: {report.llm_better_count}\n"
            f"- rule better count: {report.rule_better_count}\n"
            f"- unknown count: {report.unknown_count}\n"
            f"- avg execution latency ms: {report.average_execution_latency_ms:.1f}\n"
            f"- avg rule latency ms: {report.average_rule_latency_ms:.1f}\n"
            f"- avg llm latency ms: {report.average_llm_latency_ms:.1f}"
        )