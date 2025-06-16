from datetime import datetime
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.types import JSON

Base = declarative_base()

class VenueInfo(Base):
    __tablename__ = 'venue_infos'
    __table_args__ = (UniqueConstraint('conference', 'year', 'track', name='uix_conference_year_track'),)
    
    id = Column(Integer, primary_key=True)
    conference = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    track = Column(String, nullable=False)
    
    papers = relationship("Paper", back_populates="venue_info", cascade="all, delete-orphan")


class Paper(Base):
    __tablename__ = 'papers'
    
    id = Column(String, primary_key=True)  # e.g., OpenReview ID
    venue_info_id = Column(Integer, ForeignKey('venue_infos.id'), nullable=False)
    
    title = Column(String, nullable=False)
    status = Column(String)
    pdf_url = Column(String)
    pdf_path = Column(String)
    pdate = Column(DateTime)
    odate = Column(DateTime)
    
    # New field to store raw authors data
    raw_authors = Column(JSON, nullable=True)
    
    # Relationships
    venue_info = relationship("VenueInfo", back_populates="papers")
    authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")




class Author(Base):
    __tablename__ = 'authors'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=False, nullable=True)
    openreview_id = Column(String, unique=True, nullable=True)  # e.g. "~John_Smith1"
    orcid = Column(String, nullable=True)
    google_scholar_link = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    homepage = Column(String, nullable=True)
    affiliation_history = Column(JSON, nullable=True)

    papers = relationship("PaperAuthor", back_populates="author", cascade="all, delete-orphan")




class PaperAuthor(Base):
    """
    Association table linking a Paper to an Author, including the
    'position' (i.e., ordering) of the author on that paper and affiliation details.
    """
    __tablename__ = 'paper_authors'
    
    paper_id = Column(String, ForeignKey('papers.id'), primary_key=True)
    author_id = Column(Integer, ForeignKey('authors.id'), primary_key=True)
    position = Column(Integer, nullable=False)
    
    # Affiliation details
    affiliation_name = Column(String, nullable=True)
    affiliation_domain = Column(String, nullable=True)
    affiliation_state_province = Column(String, nullable=True)
    affiliation_country = Column(String, nullable=True)
    
    paper = relationship("Paper", back_populates="authors")
    author = relationship("Author", back_populates="papers")

