from PySide6.QtWidgets import (QMainWindow, QWidget, QTabWidget, QMessageBox)
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
from ..db import engine
from ..models import Base
from .kanji_practice import KanjiPracticeTab
from .listening_practice import ListeningPracticeTab
from .words_admin import WordsAdminTab
from .stats_panel import StatsPanel
from ..utils.backup import backup_db

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crisp Study — Kanji & Listening")
        self.resize(1100, 720)

        # Ensure DB tables
        Base.metadata.create_all(bind=engine)

        # Dark mode theme (study vibe)
        self._enable_dark_theme()

        # Backups
        backup_db()

        tabs = QTabWidget()
        tabs.addTab(KanjiPracticeTab(), "WaniKani Practice")
        tabs.addTab(ListeningPracticeTab(), "Listening Practice")
        tabs.addTab(WordsAdminTab(), "Words Admin")
        tabs.addTab(StatsPanel(), "Stats")

        self.setCentralWidget(tabs)

    def _enable_dark_theme(self):
        pal = QPalette()
        pal.setColor(QPalette.Window, QColor(30, 30, 30))
        pal.setColor(QPalette.WindowText, Qt.white)
        pal.setColor(QPalette.Base, QColor(45, 45, 45))
        pal.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
        pal.setColor(QPalette.ToolTipBase, Qt.white)
        pal.setColor(QPalette.ToolTipText, Qt.white)
        pal.setColor(QPalette.Text, Qt.white)
        pal.setColor(QPalette.Button, QColor(45, 45, 45))
        pal.setColor(QPalette.ButtonText, Qt.white)
        pal.setColor(QPalette.Highlight, QColor(100, 180, 100))
        pal.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(pal)