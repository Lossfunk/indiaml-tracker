from datetime import datetime
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
    UniqueConstraint,
    ForeignKeyConstraint,
)
from sqlalchemy.types import JSON

# --- Base Class ---
Base = declarative_base()


# --- Canonical Tables ---

class Institution(Base):
    """Stores the canonical information for an institution."""
    __tablename__ = 'institutions'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    ror_id = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    paper_affiliations = relationship("PaperAuthorAffiliation", back_populates="institution")

class Keyword(Base):
    """
    Stores the canonical, unique string for each keyword. This is the simple,
    non-hierarchical version.
    """
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True)
    keyword = Column(String, nullable=False, unique=True)

    papers = relationship("PaperKeyword", back_populates="keyword", cascade="all, delete-orphan")


# --- Core Entity Tables ---

class VenueInfo(Base):
    """
    Represents a specific instance of a conference (a specific year and track).
    Conference name is stored as a simple string.
    """
    __tablename__ = 'venue_infos'
    # The unique constraint now uses the 'conference' string field
    __table_args__ = (UniqueConstraint('conference', 'year', 'track', name='uix_conference_year_track'),)
    
    id = Column(Integer, primary_key=True)
    conference = Column(String, nullable=False) # Conference name is a string
    year = Column(Integer, nullable=False)
    track = Column(String, nullable=False, default='main')
    
    # Relationship to Paper is unchanged
    papers = relationship("Paper", back_populates="venue_info", cascade="all, delete-orphan")

class Paper(Base):
    """Represents a single paper."""
    __tablename__ = 'papers'
    
    id = Column(String, primary_key=True, comment="e.g., OpenReview ID")
    venue_info_id = Column(Integer, ForeignKey('venue_infos.id'), nullable=False)


    title = Column(String, nullable=False)
    status = Column(String) # accepted, rejected, etc.
    status_type = Column(String, nullable=True)  # e.g "oral", "poster", "spotlight" or "desk rejected" etc

    raw_authors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    venue_info = relationship("VenueInfo", back_populates="papers")
    authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")
    keywords = relationship("PaperKeyword", back_populates="paper", cascade="all, delete-orphan")

class Author(Base):
    """Represents a single, unique author."""
    __tablename__ = 'authors'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    openreview_id = Column(String, unique=True, nullable=True)
    orcid = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    papers = relationship("PaperAuthor", back_populates="author", cascade="all, delete-orphan")


# --- Association Tables ---

class PaperAuthor(Base):
    """Links a Paper to an Author, including the author's position."""
    __tablename__ = 'paper_authors'
    
    paper_id = Column(String, ForeignKey('papers.id'), primary_key=True)
    author_id = Column(Integer, ForeignKey('authors.id'), primary_key=True)
    position = Column(Integer, nullable=False)
    
    paper = relationship("Paper", back_populates="authors")
    author = relationship("Author", back_populates="papers")
    affiliations = relationship("PaperAuthorAffiliation", back_populates="paper_author", cascade="all, delete-orphan")

class PaperAuthorAffiliation(Base):
    """Links an authorship (PaperAuthor) to one or more Institutions."""
    __tablename__ = 'paper_author_affiliations'
    
    paper_id = Column(String, primary_key=True)
    author_id = Column(Integer, primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), primary_key=True)
    
    __table_args__ = (ForeignKeyConstraint(['paper_id', 'author_id'], ['paper_authors.paper_id', 'paper_authors.author_id']),)
    
    institution = relationship("Institution", back_populates="paper_affiliations")
    paper_author = relationship("PaperAuthor", back_populates="affiliations")



class PaperKeyword(Base):
    """Links a Paper to a Keyword. This is an optional link."""
    __tablename__ = 'paper_keywords'
    
    paper_id = Column(String, ForeignKey('papers.id'), primary_key=True)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), primary_key=True)

    paper = relationship("Paper", back_populates="keywords")
    keyword = relationship("Keyword", back_populates="papers")