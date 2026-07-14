from app.models.plan import Plan

COMMANDS = [
    {
        "patterns" : [
            r"\b(open|launch|start)\b.*\bcalculator\b",
        ],
        "plan": Plan(
            intent="open_application",
            tool="application",
            parameters={"name": "Calculator"}
        )
    },
    {
        "patterns" : [
            r"\b(open|launch|start)\b.*\bnotepad\b"           
        ],
        "plan": Plan(
            intent="open_application",
            tool="application",
            parameters={"name": "Notepad"}
        )
    },
    {
        "patterns" : [
           r"\b(open|launch|start)\b.*\bchrome\b"            
        ],
        "plan": Plan(
            intent="open_application",
            tool="application",
            parameters={"name": "Google Chrome"}
        )
    },
    {
        "patterns" : [
            r"\b(open|launch|start)\b.*\bvisual studio code\b"
        ],
        "plan": Plan(
            intent="open_application",
            tool="application",
            parameters={"name": "Visual Studio Code"}
        )
    }
]