import re

class PatternMatcher:
    """"
    Matches user input against command patterns.
    """
    @staticmethod
    def match_pattern(patterns: list[str], text: str) -> bool:
        
        text = text.lower().strip()
        
        for pattern in patterns:
            
            if re.search(pattern, text):
                return True
        return False

    @staticmethod
    def matches(patterns: list[str], text: str) -> bool:
        return PatternMatcher.match_pattern(patterns, text)