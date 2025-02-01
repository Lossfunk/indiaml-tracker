# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models.models import Base

DATABASE_URL = "sqlite:///venues.db"  # Replace with your actual database URL

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

def init_db():
    """Create all tables. Call this once at startup."""
    Base.metadata.create_all(bind=engine)
