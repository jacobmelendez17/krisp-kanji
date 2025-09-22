from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    WANIKANI_API_TOKEN: str = os.getenv("WANIKANI_API_TOKEN", "")
    CACHE_TTL_DAYS: int = int(os.getenv("CACHE_TTL_DAYS", "1"))
    DB_PATH: str = os.getenv("DB_PATH", "study.db")
    MEDIA_DIR: str = os.getenv("MEDIA_DIR", "media/audio")

    @property
    def media_path(self) -> Path:
        p = Path(self.MEDIA_DIR)
        p.mkdir(parens=True, exist_ok=True)
        return p
    
config = Config()