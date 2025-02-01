# venue/venudao.py
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..config.db_config import SessionLocal
from ..models.models import VenueInfo, Paper, Author, PaperAuthor
from ..models.dto import PaperDTO, AuthorDTO
from openreview.api import OpenReviewClient
from openreview import OpenReviewException


class VenueDB:
    """DAL using SQLAlchemy ORM."""

    def __init__(self):
        self.session = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    def fetch_openreview_username(self, openreview_id: str) -> Optional[str]:
        """
        Fetch the OpenReview username using the OpenReview API.
        Returns None if not found or on error.
        """
        client = OpenReviewClient(baseurl="https://api2.openreview.net")
        try:
            profile = client.get_profile(openreview_id)
            return profile.username
        except OpenReviewException as e:
            print(
                f"OpenReviewException: Unable to fetch profile for {openreview_id}: {e}"
            )
            return None
        except Exception as e:
            print(
                f"Exception: Unexpected error fetching profile for {openreview_id}: {e}"
            )
            return None

    def get_or_create(self, model, **kwargs):
        instance = self.session.query(model).filter_by(**kwargs).one_or_none()
        if instance:
            return instance
        else:
            instance = model(**kwargs)
            self.session.add(instance)
            try:
                self.session.commit()
            except IntegrityError:
                self.session.rollback()
                instance = self.session.query(model).filter_by(**kwargs).one()
            return instance

    def get_or_create_author(self, author_dto: AuthorDTO) -> Author:
        """
        Get an existing Author by openreview_id or email, or create a new one.
        Prioritize openreview_id for uniqueness.
        """
        if author_dto.openreview_id:
            author = (
                self.session.query(Author)
                .filter_by(openreview_id=author_dto.openreview_id)
                .one_or_none()
            )
            if author:
                if (
                    author_dto.history
                    and author.affiliation_history != author_dto.history
                ):
                    author.affiliation_history = author_dto.history
                    self.session.commit()
                return author

        if author_dto.email:
            author = (
                self.session.query(Author)
                .filter_by(email=author_dto.email)
                .one_or_none()
            )
            if author:
                if (
                    author_dto.history
                    and author.affiliation_history != author_dto.history
                ):
                    author.affiliation_history = author_dto.history
                    self.session.commit()
                return author

        return self.get_or_create(
            Author,
            full_name=author_dto.name,
            email=author_dto.email,
            openreview_id=author_dto.openreview_id,
            orcid=author_dto.orcid,
            google_scholar_link=author_dto.google_scholar_link,
            linkedin=author_dto.linkedin,
            homepage=author_dto.homepage,
            affiliation_history=author_dto.history,  # Store affiliation history
        )

    # def get_or_create_affiliation(self, name: str, location: str, country_code: str) -> Affiliation:
    #     return self.get_or_create(Affiliation, name=name, location=location, country_code=country_code)

    def store_papers(self, paper_dtos: List[PaperDTO]):
        for dto in paper_dtos:
            try:
                # 1. Get or create VenueInfo
                venue_info = self.get_or_create(
                    VenueInfo, conference=dto.conference, year=dto.year, track=dto.track
                )

                # 2. Convert pdate and odate
                pdate = datetime.fromisoformat(dto.pdate) if dto.pdate else None
                odate = datetime.fromisoformat(dto.odate) if dto.odate else None

                # 3. Get or create Paper
                paper = self.session.query(Paper).filter_by(id=dto.id).one_or_none()
                if not paper:
                    paper = Paper(
                        id=dto.id,
                        venue_info=venue_info,
                        title=dto.title,
                        status=dto.status,
                        pdf_url=dto.pdf_url,
                        pdate=pdate,
                        odate=odate,
                        raw_authors=[
                            {k: v for k, v in author.__dict__.items() if v is not None}
                            for author in dto.authors
                        ],
                    )
                    self.session.add(paper)
                else:
                    # Update existing paper
                    paper.title = dto.title
                    paper.status = dto.status
                    paper.pdf_url = dto.pdf_url
                    paper.pdate = pdate
                    paper.odate = odate
                    paper.venue_info = venue_info
                    paper.raw_authors = [
                        {k: v for k, v in author.__dict__.items() if v is not None}
                        for author in dto.authors
                    ]

                self.session.commit()

            except Exception as e:
                self.session.rollback()
                print(f"Error processing paper {dto.id}: {e}")
                raise e

    def resolve_affiliation(
        self, author: Author, paper_date: datetime
    ) -> Optional[Dict]:
        """
        Resolve the author's affiliation based on the paper's date and the author's affiliation history.
        Returns a dictionary with affiliation details or None if not found.
        """
        if not author.affiliation_history:
            return None

        for record in author.affiliation_history:
            start_date_str = record.get("start_date")
            end_date_str = record.get("end_date")
            affiliation = record.get("affiliation", {})

            # Parse dates
            start_date = (
                datetime.fromisoformat(start_date_str)
                if start_date_str
                else datetime.min
            )
            end_date = (
                datetime.fromisoformat(end_date_str) if end_date_str else datetime.max
            )

            if start_date <= paper_date <= end_date:
                return {
                    "name": affiliation.get("name"),
                    "domain": affiliation.get("domain"),
                    "state_province": affiliation.get("stateProvince"),
                    "country": affiliation.get("country"),
                }

        return None  # No matching affiliation found

    def update_venue_metadata(self, venue_config):
        """Update venue metadata such as source_adapter, source_id, adapter_class, etc.
        This can be extended based on your specific metadata needs."""
        # Placeholder for updating additional venue metadata
        pass

    def close(self):
        self.session.close()
