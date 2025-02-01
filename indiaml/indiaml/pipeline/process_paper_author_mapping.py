from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import List, Optional, Dict
from ..venue.venudao import VenueDB
from ..models.models import Paper, Author, PaperAuthor
from .affiliation_checker import AffiliationChecker  # We'll update this as well
import logging
import sys

# Setup Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)


def create_paper_authors():
    """
    Populate the PaperAuthor table with paper-author associations and affiliation details.
    """
    try:
        with VenueDB() as db:
            session: Session = db.session

            # Initialize AffiliationChecker
            affiliation_checker = AffiliationChecker()

            # Fetch all papers with their venue_info
            papers: List[Paper] = session.query(Paper).options(
                joinedload(Paper.venue_info)
            ).all()

            logger.info(f"Found {len(papers)} papers in the database.")

            for paper in papers:
                logger.debug(f"Processing Paper ID: {paper.id}")

                # Ensure necessary relationships are loaded
                if not paper.venue_info:
                    logger.warning(f"Missing venue information for Paper ID: {paper.id}")
                    continue

                # Determine the paper's publication date (use pdate if available, else odate)
                paper_date = paper.pdate or paper.odate
                if not paper_date:
                    logger.warning(f"No publication date available for Paper ID: {paper.id}")
                    continue

                # Iterate through raw authors
                raw_authors = paper.raw_authors or []
                for idx, author_data in enumerate(raw_authors):
                    openreview_id = author_data.get('openreview_id')
                    author = None

                    # Fetch the Author object based on openreview_id or email
                    if openreview_id:
                        author = session.query(Author).filter_by(openreview_id=openreview_id).one_or_none()
                    if not author and 'email' in author_data and author_data['email']:
                        author = session.query(Author).filter_by(email=author_data['email']).one_or_none()

                    if not author:
                        logger.warning(f"Author not found for Paper ID: {paper.id} with data: {author_data}")
                        continue

                    # Resolve affiliation using AffiliationChecker
                    affiliation_details = affiliation_checker.resolve_affiliation(
                        affiliation_history=author.affiliation_history or [],
                        paper_date=paper_date
                    )
                    if not affiliation_details:
                        affiliation_details = {
                            'name': 'Unknown',
                            'domain': 'unknown.edu',
                            'state_province': '',
                            'country': 'UNK'
                        }


                    # Check if PaperAuthor association already exists
                    paper_author = session.query(PaperAuthor).filter_by(
                        paper_id=paper.id,
                        author_id=author.id
                    ).one_or_none()

                    if not paper_author:
                        paper_author = PaperAuthor(
                            paper=paper,
                            author=author,
                            position=idx  # Sequence starts at 0
                        )

                        # Set affiliation details if available
                        if 'name' in affiliation_details:
                            paper_author.affiliation_name = affiliation_details['name']
                        if 'domain' in affiliation_details:
                            paper_author.affiliation_domain = affiliation_details['domain']
                        if 'state_province' in affiliation_details:
                            paper_author.affiliation_state_province = affiliation_details['state_province']
                        if 'country' in affiliation_details:
                            paper_author.affiliation_country = affiliation_details['country']
                        session.add(paper_author)


                    else:
                        # Update affiliation details if necessary
                        updated = False
                        if 'name' in affiliation_details and paper_author.affiliation_name != affiliation_details['name']:
                            paper_author.affiliation_name = affiliation_details['name']
                            updated = True
                        if 'domain' in affiliation_details and paper_author.affiliation_domain != affiliation_details['domain']:
                            paper_author.affiliation_domain = affiliation_details['domain']
                            updated = True
                        if 'state_province' in affiliation_details and paper_author.affiliation_state_province != affiliation_details['state_province']:
                            paper_author.affiliation_state_province = affiliation_details['state_province']
                            updated = True
                        if 'country' in affiliation_details and paper_author.affiliation_country != affiliation_details['country']:
                            paper_author.affiliation_country = affiliation_details['country']
                            updated = True

                        if updated:
                            session.add(paper_author)

                    session.commit()
                logger.info(f"Processed Paper ID: {paper.id}")

            logger.info("All PaperAuthor associations have been created/updated successfully.")

    except Exception as e:
        logger.error(f"An error occurred while creating PaperAuthor associations: {e}")
        

if __name__ == "__main__":
    create_paper_authors()
