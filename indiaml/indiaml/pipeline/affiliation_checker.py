from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

# Setup Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)


class AffiliationChecker:
    """
    Resolves an author's affiliation based on their affiliation history and a given date.
    """

    def __init__(self):
        pass  # No initialization needed as we're not interacting with the DB

    def resolve_affiliation(self, affiliation_history: List[Dict[str, Any]], paper_date: datetime) -> Optional[Dict[str, Any]]:
        """
        Determine the author's affiliation at the time of the paper's publication.

        :param affiliation_history: List of affiliation records.
        :param paper_date: Publication date of the paper.
        :return: A dictionary containing affiliation details or None if not found.
        """
        if not affiliation_history:
            logger.debug("No affiliation history provided.")
            return None

        for record in affiliation_history:
            start_year = record.get('start')
            end_year = record.get('end')
            institution = record.get('institution', {})
            affiliation_name = institution.get('name')
            affiliation_domain = institution.get('domain')
            affiliation_country = institution.get('country', 'UNK')  # Default to 'UNK' if not provided

            # Convert years to datetime objects for comparison
            try:
                start_date = datetime(start_year, 1, 1) if start_year else datetime.min
                end_date = datetime(end_year, 12, 31) if end_year else datetime.max
            except Exception as e:
                logger.error(f"Error parsing dates for affiliation record: {record}. Error: {e}")
                continue

            if start_date <= paper_date <= end_date:
                logger.debug(f"Affiliation found: {affiliation_name} for date {paper_date.date()}")
                return {
                    'name': affiliation_name,
                    'domain': affiliation_domain,
                    'country': affiliation_country
                }

        logger.debug(f"No matching affiliation found for date {paper_date.date()}")
        return None
