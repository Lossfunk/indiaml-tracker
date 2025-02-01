from typing import List
from sqlalchemy.orm import Session

from ..config.venues_config import VenueConfig
from ..venue_adapters.adapter_factory import get_adapter
from ..venue.venudao import VenueDB
from ..models.dto import PaperDTO
from datetime import datetime, timezone
from ..config.db_config import init_db

# SETUP LOGGING
import logging
import sys
root = logging.getLogger()
root.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

logger = logging.getLogger(__name__)

def fetch_paper_metadata(config) -> List[PaperDTO]:
    """Fetch papers using the appropriate adapter."""
    logger.info(f"Fetching paper metadata for {config.source_id} ...")
    try:
        adapter = get_adapter(config)
        papers = adapter.fetch_papers()
        logger.info(f"Fetched {len(papers)} papers for {config.source_id}")
        return papers
    except Exception as e:
        logger.error(f"Error fetching papers for {config.source_id}: {e}")
        return []


def store_metadata(config, papers: List[PaperDTO]):
    """Store venue and paper metadata into the database."""
    try:
        logger.info(f"Storing paper metadata for {config.source_id} ...")
        with VenueDB() as db:
            db.store_papers(papers)
            logger.info(f"Stored {len(papers)} papers for {config.source_id} in DB.")
    except Exception as e:
        logger.error(f"Error storing papers for {config.source_id}: {e}")


def main_flow(configs: List[VenueConfig], only_accepted: bool = True, cache_dir: str = "cache"):
    """
    Orchestrate the processing of multiple venues:
    - Fetch papers
    - Store metadata
    - Assign affiliations
    """

    init_db()
    
    for cfg in configs:
        logger.info(f"Starting processing for venue: {cfg.conference} {cfg.year} {cfg.track}")
        papers = fetch_paper_metadata(cfg)
        if not papers:
            logger.warning(f"No papers fetched for {cfg.source_id}.")
            continue
        
        store_metadata(cfg, papers)


if __name__ == "__main__":
    from ..config.venues_config import VENUE_CONFIGS
    # Process all venue configurations
    main_flow(VENUE_CONFIGS, only_accepted=True, cache_dir="cache")
