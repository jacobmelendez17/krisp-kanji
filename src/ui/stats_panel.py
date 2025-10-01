from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from ..db import SessionLocal
from ..services.srs import get_or_create_stats

class StatsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.lbl = QLabel("")
        root = QVBoxLayout(self)
        root.addWidget(self.lbl)
        self.refresh()

    def refresh(self):
        with SessionLocal() as db:
            s = get_or_create_stats(db)
        acc = (s.correct_answers / s.total_reviews * 100.0) if s.total_reviews else 0.0
        self.lbl.setText(
            f"Total Reviews: {s.total_reviews}\n"
            f"Correct: {s.correct_answers}\n"
            f"Wrong: {s.wrong_answers}\n"
            f"Accuracy: {acc:.1f}%"
        )