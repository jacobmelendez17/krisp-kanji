import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import requests
from ..config import config
from ..db import SessionLocal, engine
from ..models import WKCache, Base
from sqlalchemy import select

WK_API = "https://api.wanikani.com/v2"
HEADERS = {"Authorization": f"Bearer {config.WANIKANI_API_TOKEN}"}
CACHE_FILE = Path(".cache_wk.json")

def _need_refresh(last: str | None) -> bool:
    if not last:
        return True
    try:
        dt = datetime.fromisoformat(last)
    except Exception:
        return True
    return datetime.now() - dt > timedelta(days=config.CACHE_TTL_DAYS)

def _fetch_all_kanji() -> List[Dict]:
    kanji: dict[int, Dict] = {}

    # 1) assignments
    url = f"{WK_API}/assignments?subject_types=kanji"
    while url:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        subject_ids = [a["data"]["subject_id"] for a in data["data"]]
        for sid in subject_ids:
            kanji[sid] = {}
        url = data["pages"]["next_url"]

    if not kanji:
        return []

    ids = list(kanji.keys())
    out: List[Dict] = []
    for i in range(0, len(ids), 500):
        chunk = ids[i:i+500]
        q = ",".join(map(str, chunk))
        url = f"{WK_API}/subjects?ids={q}"
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        for item in data["data"]:
            if item["object"] != "kanji":
                continue
            d = item["data"]
            out.append({
                "id": item["id"],
                "characters": d.get("characters"),
                "meanings": [m["meaning"] for m in d.get("meanings", []) if m.get("primary") or True],
                "readings": [{"reading": r["reading"], "type": r["type"]} for r in d.get("readings", [])],
            })
    return out

def get_wk_kanji(force_refresh: bool = False) -> List[Dict]:
    # Create cache table if first run
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        row = db.scalars(select(WKCache)).first()
        if not row:
            row = WKCache(id=1, last_refresh=None, payload_path=str(CACHE_FILE))
            db.add(row)
            db.commit()
        stale = _need_refresh(row.last_refresh) or force_refresh
        if stale:
            items = _fetch_all_kanji()
            CACHE_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
            row.last_refresh = datetime.now().isoformat()
            row.payload_path = str(CACHE_FILE)
            db.commit()
        else:
            if not Path(row.payload_path or "").exists():
                items = _fetch_all_kanji()
                CACHE_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
                row.last_refresh = datetime.now().isoformat()
                row.payload_path = str(CACHE_FILE)
                db.commit()
        # Return current cache
        return json.loads(Path(row.payload_path or str(CACHE_FILE)).read_text(encoding="utf-8"))