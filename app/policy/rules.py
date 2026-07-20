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

    "open_url": {
        "allowed": True,
        "risk": RiskLevel.LOW,
        "confirmation": False,
    },

    "search_web": {
        "allowed": True,
        "risk": RiskLevel.LOW,
        "confirmation": False,
    },

    # Future browser capabilities — pre-registered with
    # appropriate risk levels for when they are implemented.
    "browser_download": {
        "allowed": True,
        "risk": RiskLevel.MEDIUM,
        "confirmation": True,
    },

    "browser_automation": {
        "allowed": False,
        "risk": RiskLevel.HIGH,
        "confirmation": True,
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

    "list_directory": {
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