from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone
from typing import List
from ..venue.venudao import VenueDB
from ..models.models import PaperAuthor, Paper, Author
from ..models.dto import AuthorDTO
from ..config.venues_config import VENUE_CONFIGS
from ..venue_adapters.adapter_factory import get_adapter
from ..config.db_config import init_db
import logging
import sys

# SETUP LOGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def process_authors():
    """Process authors from stored papers and save them to the database."""
    try:
        with VenueDB() as db:
            session: Session = db.session
            # Fetch all papers with related venue_info using joinedload to optimize queries
            papers: List[Paper] = session.query(Paper).options(
                joinedload(Paper.venue_info)
            ).all()

            logger.info(f"Processing authors for {len(papers)} papers.")


            for paper in papers:
                logger.debug(f"Processing paper ID: {paper.id}")
                
                # Access venue_info directly
                if not paper.venue_info:
                    logger.warning(f"Missing venue information for paper ID: {paper.id}")
                    continue
                
                conference = paper.venue_info.conference
                year = paper.venue_info.year
                track = paper.venue_info.track

                # Retrieve the corresponding VenueConfig based on conference, year, and track
                venue_config = next(
                    (cfg for cfg in VENUE_CONFIGS 
                     if cfg.conference == conference and
                        cfg.year == year and
                        cfg.track == track),
                    None
                )
                
                if not venue_config:
                    logger.warning(f"No VenueConfig found for paper ID: {paper.id} with conference '{conference}', year '{year}', and track '{track}'")
                    continue


                # Get the appropriate adapter
                adapter = get_adapter(venue_config)
                
                # Fetch detailed author information using the adapter
                detailed_authors = adapter.fetch_authors(
                    [author.get('openreview_id') for author in paper.raw_authors if 'openreview_id' in author]
                )


                if not detailed_authors:
                    logger.warning(f"No detailed authors fetched for paper ID: {paper.id}")
                    # Fallback to raw authors if detailed authors are not available
                    detailed_authors = [
                        AuthorDTO(
                            name=author.get('name'),
                            email=author.get('email'),
                            openreview_id=author.get('openreview_id'),
                            orcid=author.get('orcid'),
                            google_scholar_link=author.get('google_scholar_link'),
                            linkedin=author.get('linkedin'),
                            homepage=author.get('homepage'),
                            history=author.get('history')  # Ensure history is included if available
                        )
                        for author in paper.raw_authors
                    ]

                if not detailed_authors:
                    logger.warning(f"No authors to process for paper ID: {paper.id}")
                    continue


                for idx, author_dto in enumerate(detailed_authors):
                    try:
                        author = db.get_or_create_author(author_dto)
                        
                        # Create or update PaperAuthor association with sequence position
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
                            session.add(paper_author)
                        else:
                            paper_author.position = idx  # Update position if necessary

                    except Exception as e:
                        session.rollback()
                        logger.error(f"Error processing author '{author_dto.name}' for paper {paper.id}: {e}")
                
                session.commit()
            logger.info("All authors processed successfully.")
    
    except Exception as e:
        logger.error(f"Error in processing authors: {e}")

if __name__ == "__main__":
    init_db()  # Ensure the database is initialized
    process_authors()
