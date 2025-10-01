from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QComboBox, QMessageBox, QGroupBox
)
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt
from ..services.wanikani import get_wk_kanji
from ..services.romaji import to_hiragana, normalize_english
from ..db import SessionLocal
from ..services.srs import record_result
import random

class KanjiPracticeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.items = []
        self.current = None
        self.undo_stack = [] # store last (item, correct?)

        root = QVBoxLayout(self)

        # Controls: mode selector & refresh
        top = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItems(["On'yomi", "Kun'yomi", "Meaning"]) # Separate modes
        self.refresh_btn = QPushButton("Refresh WK Cache")
        self.refresh_btn.clicked.connect(self.load_items)
        top.addWidget(QLabel("Mode:"))
        top.addWidget(self.mode)
        top.addStretch(1)
        top.addWidget(self.refresh_btn)
        root.addLayout(top)

        # Card area
        box = QGroupBox("Prompt")
        card = QVBoxLayout()
        self.lbl_kanji = QLabel("—")
        self.lbl_kanji.setAlignment(Qt.AlignCenter)
        self.lbl_kanji.setStyleSheet("font-size: 72px; font-weight: 700; padding: 24px;")
        card.addWidget(self.lbl_kanji)
        box.setLayout(card)
        root.addWidget(box)

        # Answer
        ans_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Type your answer… (Enter to submit)")
        self.submit = QPushButton("Submit")
        self.undo = QPushButton("Undo typo")
        ans_row.addWidget(self.input, stretch=1)
        ans_row.addWidget(self.submit)
        ans_row.addWidget(self.undo)
        root.addLayout(ans_row)

        # Result label
        self.result = QLabel("")
        self.result.setAlignment(Qt.AlignCenter)
        self.result.setStyleSheet("font-size: 18px; padding: 6px;")
        root.addWidget(self.result)

        # Shortcuts
        QShortcut(QKeySequence("Return"), self, activated=self.on_submit)

        # Wiring
        self.submit.clicked.connect(self.on_submit)
        self.undo.clicked.connect(self.on_undo)

        # Initial load
        self.load_items()
        self.next_item()

        def load_items(self):
            try:
                self.items = get_wk_kanji(force_refresh=True)
                random.shuffle(self.items)
                QMessageBox.information(self, "WaniKani", f"Loaded {len(self.items)} kanji from WaniKani.")
            except Exception as e:
                QMessageBox.critical(self, "WaniKani Error", str(e))

        def next_item(self):
            if not self.items:
                self.current = None
                self.lbl_kanji.setText("—")
                return
            self.current = random.choice(self.items)
            self.lbl_kanji.setText(self.current.get("characters", "?"))
            self.input.clear()
            self.result.setText("")
            self.input.setFocus()

        def expected_answers(self):
            if not self.current:
                return []
            mode = self.mode.currentText()
            if mode == "Meaning":
                return [m.lower() for m in self.current.get("meanings", [])]
            else:
                t = "onyomi" if mode.startswith("On") else "kunyomi"
                return [r["reading"] for r in self.current.get("readings", []) if r.get("type") == t]
            
        def on_submit(self):
            guess = self.input.text().strip()
            mode = self.mode.currentText()
            answers = self.expected_answers()
            if mode != "Meaning":
                guess = to_hiragana(guess)
            else:
                guess = normalize_english(guess)
                answers = [normalize_english(a) for a in answers]

            correct = any(guess == a for a in answers)
            with SessionLocal() as db:
                record_result(db, correct)
            
            # track for undo
            self.undo_stack.append((self.current, correct))

            if correct:
                self.result.setStyleSheet("color: #8bdc8b; font-size: 18px; padding:6px;")
                self.result.setText("Correct! Press Enter for next…")
                self.next_item()
            else:
                which = ", ".join(answers) if answers else "(none)"
                label = f"Wrong. Expected: {which}"
                self.result.setStyleSheet("color: #ff9292; font-size: 18px; padding:6px;")
                self.result.setText(label)

            def on_undo(self):
                if not self.undo_stack:
                    return
                # Flip last result from wrong→correct (typo forgiveness)
                item, was_correct = self.undo_stack.pop()
                if was_correct:
                    # already correct; do nothing
                    return
                with SessionLocal() as db:
                    # subtract wrong, add correct
                    from ..services.srs import get_or_create_stats
                    s = get_or_create_stats(db)
                    if s.wrong_answers > 0:
                        s.wrong_answers -= 1
                        s.correct_answers += 1
                        db.commit()
                self.result.setText("Undone last typo. You got credit.")