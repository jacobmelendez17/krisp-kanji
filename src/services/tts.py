from gtts import gTTS
from pathlib import Path
from ..config import config

def ensure_tts_audio(text: str, lang: str = "ja") -> Path:
    out = config.media_path / (re_safe(text) + ".mp3")
    if not out.exists():
        tts = gTTS(text=text, lang=lang)
        tts.save(str(out))
    return out

def re_safe(s: str) -> str:
    import re
    return re.sub(r"[^\w\-]+", "_", s)