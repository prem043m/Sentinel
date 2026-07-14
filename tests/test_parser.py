from app.planner.parser import PlanParser


def test_valid_plan():

    plan = PlanParser.parse(
        {
            "intent":"chat",
            "tool":"llm",
            "parameters":{}
        }
    )

    assert plan.intent == "chat"
    
import pytest

from app.planner.parser import PlanParser


def test_missing_field():

    with pytest.raises(ValueError):

        PlanParser.parse(
            {
                "intent":"chat"
            }
        )
        
import pytest

from app.planner.parser import PlanParser


def test_parameters_required():

    with pytest.raises(ValueError):

        PlanParser.parse(
            {
                "intent":"chat",
                "tool":"llm"
            }
        )