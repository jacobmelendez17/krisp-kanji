from typing import Optional
try:
    import wanakana
    def to_hiragana(s: str) -> str:
        return wanakana.to_hiragana(s)
except Exception:
    try: 
        import romkan
        def to_hiragana(s: str) -> str:
            return romkan.to_hiragana(s)
    except Exception:
        def to_hiragana(s: str) -> str:
            return s.lower()
        
import re

def normalize_english(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip()).lower()