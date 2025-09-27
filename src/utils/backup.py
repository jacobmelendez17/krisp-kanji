from pathlib import Path
from datetime import datetime
import shutil
from ..config import config

def backup_db():
    db = Path(config.DB_PATH)
    if not db.exists():
        return
    backups = Path("backups")
    backups.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    dst = backups / f"{db.stem}-{stamp}.sqlite"
    if not dst.exists():
        shutil.copy2(db, dst)