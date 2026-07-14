from app.policy.risk import RiskLevel


POLICY_RULES = {

    "chat": {
        "allowed": True,
        "risk": RiskLevel.LOW,
        "confirmation": False,
    },

    "open_browser": {
        "allowed": True,
        "risk": RiskLevel.LOW,
        "confirmation": False,
    },

    "open_application": {
        "allowed": True,
        "risk": RiskLevel.LOW,
        "confirmation": False,
    },

    "create_folder": {
        "allowed": True,
        "risk": RiskLevel.MEDIUM,
        "confirmation": False,
    },

    "read_file": {
        "allowed": True,
        "risk": RiskLevel.MEDIUM,
        "confirmation": False,
    },

    "delete_file": {
        "allowed": True,
        "risk": RiskLevel.HIGH,
        "confirmation": True,
    },

    "delete_folder": {
        "allowed": True,
        "risk": RiskLevel.HIGH,
        "confirmation": True,
    },

    "shutdown": {
        "allowed": True,
        "risk": RiskLevel.CRITICAL,
        "confirmation": True,
    },

    "shutdown_system": {
        "allowed": True,
        "risk": RiskLevel.CRITICAL,
        "confirmation": True,
    },

}