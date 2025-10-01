from PySide6.QtWidgets import (
QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from ..db import SessionLocal
from ..models import Word
from pathlib import Path
import pandas as pd

class WordsAdminTab(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)

        # Controls
        bar = QHBoxLayout()
        self.word = QLineEdit(); self.word.setPlaceholderText("Word (JP)")
        self.trans = QLineEdit(); self.trans.setPlaceholderText("Translation (EN)")
        self.tags = QLineEdit(); self.tags.setPlaceholderText("Tags (comma-separated)")
        self.audio = QLineEdit(); self.audio.setPlaceholderText("Audio path (mp3)")
        btn_add = QPushButton("Add")
        btn_upd = QPushButton("Update Selected")
        btn_del = QPushButton("Delete Selected")
        btn_imp = QPushButton("Import CSV…")
        btn_exp = QPushButton("Export CSV…")
        for w in [self.word, self.trans, self.tags, self.audio]:
            bar.addWidget(w)
        bar.addWidget(btn_add)
        bar.addWidget(btn_upd)
        bar.addWidget(btn_del)
        bar.addStretch(1)
        bar.addWidget(btn_imp)
        bar.addWidget(btn_exp)
        root.addLayout(bar)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Word", "Translation", "Tags", "Audio Path"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        root.addWidget(self.table)

        # Wire
        btn_add.clicked.connect(self.add_row)
        btn_upd.clicked.connect(self.update_selected)
        btn_del.clicked.connect(self.delete_selected)
        btn_imp.clicked.connect(self.import_csv)
        btn_exp.clicked.connect(self.export_csv)
        self.table.itemSelectionChanged.connect(self.populate_inputs_from_selection)

        self.refresh()

    def refresh(self):
        with SessionLocal() as db:
            rows = db.query(Word).order_by(Word.id.desc()).all()
        self.table.setRowCount(len(rows))
        for r, w in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(w.id)))
            self.table.setItem(r, 1, QTableWidgetItem(w.word))
            self.table.setItem(r, 2, QTableWidgetItem(w.translation))
            self.table.setItem(r, 3, QTableWidgetItem(w.tags or ""))
            self.table.setItem(r, 4, QTableWidgetItem(w.audio_path or ""))

        def populate_inputs_from_selection(self):
            items = self.table.selectedItems()
            if not items:
                return
            row = items[0].row()
            self.word.setText(self.table.item(row, 1).text())
            self.trans.setText(self.table.item(row, 2).text())
            self.tags.setText(self.table.item(row, 3).text())
            
        def add_row(self):
            w = Word(word=self.word.text().strip(), translation=self.trans.text().strip(), tags=self.tags.text().strip() or None, audio_path=self.audio.text().strip() or None)
            with SessionLocal() as db:
                db.add(w); db.commit()
            self.refresh()
            self.word.clear(); self.trans.clear(); self.tags.clear(); self.audio.clear()

        def update_selected(self):
            items = self.table.selectedItems()
            if not items:
                return
            row = items[0].row()
            id_ = int(self.table.item(row, 0).text())
            with SessionLocal() as db:
                w = db.get(Word, id_)
                if not w:
                    return
                w.word = self.word.text().strip()
                w.translation = self.trans.text().strip()
                w.tags = self.tags.text().strip() or None
                p = self.audio.text().strip() or None
                if p and not Path(p).exists():
                    QMessageBox.warning(self, "Audio", "Path does not exist. Save anyway?")
                w.audio_path = p
                db.commit()
            self.refresh()

        def delete_selected(self):
            items = self.table.selectedItems()
            if not items:
                return
            row = items[0].row()
            id_ = int(self.table.item(row, 0).text())
            with SessionLocal() as db:
                w = db.get(Word, id_)
                if w:
                    db.delete(w); db.commit()
            self.refresh()

        def import_csv(self):
            path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
            if not path:
                return
            df = pd.read_csv(path)
            required = {"word", "translation"}
            if not required.issubset(set(df.columns)):
                QMessageBox.critical(self, "CSV", "CSV must include at least 'word' and 'translation' columns.")
                return
            with SessionLocal() as db:
                for _, row in df.iterrows():
                    db.add(Word(word=str(row.get("word", "")).strip(), translation=str(row.get("translation", "")).strip(), tags=str(row.get("tags", "") or None) if "tags" in df.columns else None, audio_path=str(row.get("audio_path", "") or None) if "audio_path" in df.columns else None))
                db.commit()
            self.refresh()

        def export_csv(self):
            path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "words.csv", "CSV Files (*.csv)")
            if not path:
                return
            with SessionLocal() as db:
                rows = db.query(Word).all()
            import csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["word", "translation", "audio_path", "tags"])
                for w in rows:
                    writer.writerow([w.word, w.translation, w.audio_path or "", w.tags or ""])
            QMessageBox.information(self, "Export", f"Exported {len(rows)} rows.")