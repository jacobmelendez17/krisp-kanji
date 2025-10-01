from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, DateTime, func, Boolean
from typing import Optional

class Base(DeclarativeBase):
    pass

class Word(Base):
    __tablename__ = "words"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String(128), index=True)
    translation: Mapped[str] = mapped_column(String(256))
    audio_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Stat(Base):
    __tablename__ = "stats"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Aggregate counters
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    wrong_answers: Mapped[int] = mapped_column(Integer, default=0)

class DailyBundle(Base):
    __tablename__ = "daily_bundles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    yyyymmdd: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    # Comma-separated list of word ids for simplicity
    word_ids: Mapped[str] = mapped_column(Text)

class WKCache(Base):
    __tablename__ = "wk_cache"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_refresh: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    payload_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)