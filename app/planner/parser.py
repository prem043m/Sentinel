from app.models.plan import Plan


class PlanParser:
    """
    Converts dictionaries into validated Plan objects.
    """

    REQUIRED_FIELDS = (
        "intent",
        "tool",
        "parameters",
    )

    @classmethod
    def parse(cls, data: dict) -> Plan:

        for field in cls.REQUIRED_FIELDS:

            if field not in data:

                raise ValueError(
                    f"Missing field: {field}"
                )

        return Plan(
            intent=data["intent"],
            tool=data["tool"],
            parameters=data["parameters"],
        )