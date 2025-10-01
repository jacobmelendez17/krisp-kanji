from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Stat

def get_or_create_stats(db: Session) -> Stat:
    row = db.scalars(select(Stat)).first()
    if not row:
        ow = Stat(id=1, total_reviews=0, correct_answers=0, wrong_answers=0)
        db.add(row)
        db.commit()
    return row

def record_result(db: Session, correct: bool):
    s = get_or_create_stats(db)
    s.total_reviews += 1
    if correct:
        s.correct_answers += 1
    else:
        s.wrong_answers += 1
    db.commit()