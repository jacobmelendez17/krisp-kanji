from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QShortcut, QKeySequence
from ..db import SessionLocal
from ..models import Word, DailyBundle
from ..services.tts import ensure_tts_audio
from ..services.srs import record_result
from pathlib import Path
import random, os

# QtMultimedia
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl

class ListeningPracticeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)

        self.current_list: list[Word] = []
        self.current_idx = -1

        root = QVBoxLayout(self)

        # Bundle controls (pick date or random 10)
        row = QHBoxLayout()
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.pick_btn = QPushButton("Load Daily Bundle (10)")
        self.prepare_btn = QPushButton("Prepare Today From Selection…")
        row.addWidget(QLabel("Date:"))
        row.addWidget(self.date)
        row.addStretch(1)
        row.addWidget(self.pick_btn)
        row.addWidget(self.prepare_btn)
        root.addLayout(row)

        # Quiz area
        self.lbl_index = QLabel("0 / 0")
        self.play_btn = QPushButton("▶ Play")
        self.answer = QLineEdit()
        self.answer.setPlaceholderText("Type the English meaning… (Enter to submit)")
        self.submit = QPushButton("Submit")

        quiz = QHBoxLayout()
        quiz.addWidget(self.lbl_index)
        quiz.addWidget(self.play_btn)
        quiz.addWidget(self.answer, stretch=1)
        quiz.addWidget(self.submit)
        root.addLayout(quiz)

        self.result = QLabel("")
        self.result.setAlignment(Qt.AlignCenter)
        root.addWidget(self.result)

        # Selection table (for preparing daily bundle)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Word", "Translation", "Audio?"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        root.addWidget(self.table)

        # Shortcuts
        QShortcut(QKeySequence("Return"), self, activated=self.on_submit)
        QShortcut(QKeySequence("Space"), self, activated=self.play_audio)

        # Wire
        self.pick_btn.clicked.connect(self.load_bundle)
        self.prepare_btn.clicked.connect(self.prepare_from_selection)
        self.play_btn.clicked.connect(self.play_audio)
        self.submit.clicked.connect(self.on_submit)

        self.refresh_table()

    def refresh_table(self):
        with SessionLocal() as db:
            rows = db.query(Word).order_by(Word.created_at.desc()).all()
        self.table.setRowCount(len(rows))
        for r, w in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(w.id)))
            self.table.setItem(r, 1, QTableWidgetItem(w.word))
            self.table.setItem(r, 2, QTableWidgetItem(w.translation))
            self.table.setItem(r, 3, QTableWidgetItem("✓" if w.audio_path and Path(w.audio_path).exists() else "✗"))

    def _set_bundle(self, words: list[Word]):
        random.shuffle(words)
        self.current_list = words[:10]
        self.current_idx = -1
        self.result.setText("")
        self.next_item()

    def load_bundle(self):
        d = self.date.date().toString("yyyyMMdd")
        with SessionLocal() as db:
            row = db.query(DailyBundle).filter_by(yyyymmdd=d).first()
            if row:
                ids = [int(x) for x in row.word_ids.split(",") if x.strip().isdigit()]
                words = db.query(Word).filter(Word.id.in_(ids)).all()
                self._set_bundle(words)
                return
            # else create random bundle of 10
            words = db.query(Word).all()
            if len(words) < 10:
                QMessageBox.warning(self, "Bundle", "Not enough words (<10) to form bundle.")
                return
            chosen = random.sample(words, 10)
            db.add(DailyBundle(yyyymmdd=d, word_ids=",".join(str(w.id) for w in chosen)))
            db.commit()
            self._set_bundle(chosen)

    def prepare_from_selection(self):
        d = self.date.date().toString("yyyyMMdd")
        selected_rows = set(i.row() for i in self.table.selectedIndexes())
        if not selected_rows:
            QMessageBox.information(self, "Prepare", "Please select rows in the table (Cmd/Ctrl-click).")
            return
        ids = []
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                ids.append(int(item.text()))
        with SessionLocal() as db:
            words = db.query(Word).filter(Word.id.in_(ids)).all()
            if len(words) < 1:
                QMessageBox.warning(self, "Prepare", "No valid rows selected.")
                return
            db.merge(DailyBundle(yyyymmdd=d, word_ids=",".join(str(w.id) for w in words)))
            db.commit()
            self._set_bundle(words)

    def play_audio(self):
        if 0 <= self.current_idx < len(self.current_list):
            w = self.current_list[self.current_idx]
            audio_path = Path(w.audio_path) if w.audio_path else None
            if not audio_path or not audio_path.exists():
                audio_path = ensure_tts_audio(w.word)
            self.player.setSource(QUrl.fromLocalFile(str(audio_path)))
            self.player.play()

    def next_item(self):
        self.current_idx += 1
        if self.current_idx >= len(self.current_list):
            self.lbl_index.setText("Done!")
            self.result.setText("Great job — bundle complete.")
            return
        self.lbl_index.setText(f"{self.current_idx+1} / {len(self.current_list)}")
        self.answer.clear()
        self.answer.setFocus()

    def on_submit(self):
        if not (0 <= self.current_idx < len(self.current_list)):
            return
        w = self.current_list[self.current_idx]
        guess = self.answer.text().strip().lower()
        truth = (w.translation or "").strip().lower()
        correct = guess == truth
        with SessionLocal() as db:
            record_result(db, correct)
        if correct:
            self.result.setStyleSheet("color:#8bdc8b")
            self.result.setText("Correct! (Enter for next)")
            self.next_item()
        else:
            self.result.setStyleSheet("color:#ff9292")
            self.result.setText(f"Wrong. Answer: {w.translation}")