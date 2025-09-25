from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import config

engine = create_engine(f"sqlite:///{config.DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)