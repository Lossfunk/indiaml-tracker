# adapters/neurips_adapter.py

from datetime import datetime, timezone
from .base_adapter import BaseAdapter, PaperRecord
from ..models.dto import PaperDTO, AuthorDTO
from typing import List, Optional
import openreview
from logging import getLogger

logger = getLogger(__name__)

def get_preferred_name(or_name_obj: List[dict]) -> str:
    for name in or_name_obj:
        if name.get('preferred', False):
            return name.get('fullname', '')
    return ''



class NeurIPSAdapter(BaseAdapter):
    def fetch_papers(self) -> List[PaperDTO]:
        venue_group = self.client.get_group(self.config.source_id)
        submission_name = venue_group.content.get('submission_name', {}).get('value', 'Submission')
        invitation = f"{self.config.source_id}/-/{submission_name}"
        notes = self.client.get_all_notes(invitation=invitation)

        papers = []
        for note in notes:
            venueid = note.content.get('venueid', {}).get('value', '')
            status = self.determine_status(venue_group, venueid)
            pdate = self._convert_timestamp(note.pdate)
            odate = self._convert_timestamp(note.odate)

            paper = PaperDTO(
                id=note.id,
                title=note.content.get('title', {}).get('value', ''),
                status=status,
                pdf_url=note.content.get('pdf', {}).get('value', ''),
                pdate=pdate,
                odate=odate,
                conference=self.config.conference,
                year=self.config.year,
                track=self.config.track,
                authors=[
                    AuthorDTO(name=name, openreview_id=aid)
                    for name, aid in zip(
                        note.content.get("authors", {}).get("value", []),
                        note.content.get("authorids", {}).get("value", [])
                    )
                ]
            )
            print(paper)
            papers.append(paper)
        return papers


    def determine_status(self, venue_group: openreview.Group, venueid: str) -> str:
        """Map venueid to submission status using ICML-specific logic."""
        if venueid.endswith("/Withdrawn_Submission"):
            return 'withdrawn'
        elif venueid.endswith("/Desk_Rejected_Submission"):
            return 'desk_rejected'
        elif venueid.endswith("/Rejected_Submission"):
            return 'rejected'
        elif venueid == venue_group.id:
            return 'accepted'
        else:
            return 'unknown'


    def _convert_timestamp(self, unix_ms: Optional[int]) -> Optional[str]:
        """Convert Unix millisecond timestamp to ISO 8601 format."""
        if unix_ms is None:
            return None
        return datetime.fromtimestamp(unix_ms / 1000, tz=timezone.utc).isoformat()



    def fetch_authors(self, author_ids: List[str]) -> List[AuthorDTO]:
        """
        Fetch author profiles while strictly preserving original author IDs.
        Handles OpenReview's profile merging and username changes.
        """
        if not author_ids:
            return []

        try:
            logger.debug(f"Fetching profiles for author IDs: {author_ids}")
            profiles = openreview.tools.get_profiles(
                self.client,
                ids_or_emails=author_ids,
                with_publications=False,
                with_relations=False
            )

            # Create mapping of all known usernames to profiles
            username_profile_map = {}
            for profile in profiles:
                for name_entry in profile.content.get('names', []):
                    if username := name_entry.get('username'):
                        username_profile_map[username] = profile

            authors = []
            for original_id in author_ids:
                # Lookup by original ID only - don't accept any other usernames
                if profile := username_profile_map.get(original_id):
                    authors.append(self._create_author_dto(original_id, profile))
                    
            return authors

        except Exception as e:
            logger.error(f"Error fetching author profiles: {e}")
            return []


    def _create_author_dto(self, author_id: str, profile: openreview.Profile) -> AuthorDTO:
        """Helper to create AuthorDTO while handling name preferences"""
        return AuthorDTO(
            name=get_preferred_name(profile.content.get('names', [])),
            email=profile.content.get('email', ''),
            openreview_id=author_id,  # Critical: use original ID, not profile.id
            orcid=profile.content.get('ORCID', ''),
            dblp=profile.content.get('dblp', ''),
            google_scholar_link=profile.content.get('gscholar', ''),
            linkedin=profile.content.get('linkedin', ''),
            homepage=profile.content.get('homepage', ''),
            history=profile.content.get('history', [])
        )