"""
SQLite Data Extractor for Tweet Generation Pipeline

Extracts papers and authors from SQLite database using the schema from models.py
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from .state_manager import StateManager


class SQLiteExtractor:
    """Extracts data from SQLite databases."""
    
    def __init__(self, state_manager: StateManager, config: 'PipelineConfig'):
        self.state_manager = state_manager
        self.config = config
    
    def extract_data(self, sqlite_file: str) -> Dict[str, Any]:
        """Extract papers and authors from SQLite database."""
        print(f"🔍 Extracting data from {sqlite_file}...")
        
        # Check if already extracted
        if self.state_manager.checkpoint_exists("raw_papers.json") and \
           self.state_manager.checkpoint_exists("raw_authors.json"):
            print("  ✅ Data already extracted, loading from checkpoint...")
            papers = self.state_manager.load_checkpoint("raw_papers.json")
            authors = self.state_manager.load_checkpoint("raw_authors.json")
            return {"papers": papers, "authors": authors}
        
        db_path = self.config.get_sqlite_path()
        if not db_path.exists():
            raise FileNotFoundError(f"SQLite file not found: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        
        try:
            # Extract papers with Indian authors
            papers = self._extract_papers_with_indian_authors(conn)
            print(f"  📄 Found {len(papers)} papers with Indian authors")
            
            # Extract all authors for these papers
            authors = self._extract_authors_for_papers(conn, papers)
            print(f"  👥 Found {len(authors)} unique authors")
            
            # Save checkpoints
            self.state_manager.save_checkpoint("raw_papers.json", papers)
            self.state_manager.save_checkpoint("raw_authors.json", authors)
            
            # Update progress
            self.state_manager.update_progress(
                total_papers=len(papers),
                total_authors=len(authors)
            )
            
            return {"papers": papers, "authors": authors}
            
        finally:
            conn.close()
    
    def _extract_papers_with_indian_authors(self, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        """Extract accepted papers that have at least one Indian author."""
        query = """
        SELECT DISTINCT 
            p.id,
            p.title,
            p.status,
            p.pdf_url,
            p.pdf_path,
            p.pdate,
            p.odate,
            p.raw_authors,
            vi.conference,
            vi.year,
            vi.track
        FROM papers p
        JOIN venue_infos vi ON p.venue_info_id = vi.id
        JOIN paper_authors pa ON p.id = pa.paper_id
        WHERE pa.affiliation_country = 'IN' 
        AND p.status = 'accepted'
        ORDER BY p.title
        """
        
        cursor = conn.execute(query)
        papers = []
        
        for row in cursor:
            paper = {
                "id": row["id"],
                "title": row["title"],
                "status": row["status"],
                "pdf_url": row["pdf_url"],
                "pdf_path": row["pdf_path"],
                "pdate": row["pdate"],
                "odate": row["odate"],
                "raw_authors": json.loads(row["raw_authors"]) if row["raw_authors"] else None,
                "conference": row["conference"],
                "year": row["year"],
                "track": row["track"]
            }
            papers.append(paper)
        
        return papers
    
    def _extract_authors_for_papers(self, conn: sqlite3.Connection, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract all authors for the given papers."""
        paper_ids = [paper["id"] for paper in papers]
        placeholders = ",".join(["?" for _ in paper_ids])
        
        query = f"""
        SELECT DISTINCT
            a.id,
            a.full_name,
            a.email,
            a.openreview_id,
            a.orcid,
            a.google_scholar_link,
            a.linkedin,
            a.homepage,
            a.affiliation_history,
            pa.paper_id,
            pa.position,
            pa.affiliation_name,
            pa.affiliation_domain,
            pa.affiliation_state_province,
            pa.affiliation_country
        FROM authors a
        JOIN paper_authors pa ON a.id = pa.author_id
        WHERE pa.paper_id IN ({placeholders})
        ORDER BY pa.paper_id, pa.position
        """
        
        cursor = conn.execute(query, paper_ids)
        authors_data = {}
        paper_authors = {}
        
        for row in cursor:
            author_id = row["id"]
            paper_id = row["paper_id"]
            
            # Store unique author data
            if author_id not in authors_data:
                authors_data[author_id] = {
                    "id": author_id,
                    "full_name": row["full_name"],
                    "email": row["email"],
                    "openreview_id": row["openreview_id"],
                    "orcid": row["orcid"],
                    "google_scholar_link": row["google_scholar_link"],
                    "linkedin": row["linkedin"],
                    "homepage": row["homepage"],
                    "affiliation_history": json.loads(row["affiliation_history"]) if row["affiliation_history"] else None,
                    "papers": []
                }
            
            # Store paper-author relationship
            paper_author_info = {
                "paper_id": paper_id,
                "position": row["position"],
                "affiliation_name": row["affiliation_name"],
                "affiliation_domain": row["affiliation_domain"],
                "affiliation_state_province": row["affiliation_state_province"],
                "affiliation_country": row["affiliation_country"]
            }
            
            authors_data[author_id]["papers"].append(paper_author_info)
            
            # Group authors by paper
            if paper_id not in paper_authors:
                paper_authors[paper_id] = []
            
            paper_authors[paper_id].append({
                "author_id": author_id,
                "position": row["position"],
                "full_name": row["full_name"],
                "affiliation_name": row["affiliation_name"],
                "affiliation_country": row["affiliation_country"],
                "openreview_id": row["openreview_id"],
                "google_scholar_link": row["google_scholar_link"],
                "linkedin": row["linkedin"],
                "homepage": row["homepage"]
            })
        
        # Sort authors by position for each paper
        for paper_id in paper_authors:
            paper_authors[paper_id].sort(key=lambda x: x["position"])
        
        # Add author lists to papers
        for paper in papers:
            paper["authors"] = paper_authors.get(paper["id"], [])
        
        # Save paper-author mapping
        self.state_manager.save_checkpoint("paper_authors.json", paper_authors)
        
        return list(authors_data.values())
    
    def get_conference_info(self, sqlite_file: str) -> Dict[str, Any]:
        """Extract conference information from SQLite."""
        db_path = self.config.get_sqlite_path()
        if not db_path.exists():
            raise FileNotFoundError(f"SQLite file not found: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            query = """
            SELECT DISTINCT conference, year, track
            FROM venue_infos
            LIMIT 1
            """
            
            cursor = conn.execute(query)
            row = cursor.fetchone()
            
            if row:
                return {
                    "conference": row["conference"],
                    "year": row["year"],
                    "track": row["track"]
                }
            else:
                return {}
                
        finally:
            conn.close()
    
    def get_paper_statistics(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics about the papers."""
        total_papers = len(papers)
        
        # Count papers by status
        status_counts = {}
        for paper in papers:
            status = paper.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count Indian authors
        indian_authors = set()
        first_author_indian = 0
        majority_indian = 0
        
        for paper in papers:
            authors = paper.get("authors", [])
            if not authors:
                continue
            
            # Count Indian authors in this paper
            indian_count = 0
            for author in authors:
                if author.get("affiliation_country") == "IN":
                    indian_authors.add(author["author_id"])
                    indian_count += 1
            
            # Check if first author is Indian
            if authors and authors[0].get("affiliation_country") == "IN":
                first_author_indian += 1
            
            # Check if majority are Indian
            if indian_count > len(authors) / 2:
                majority_indian += 1
        
        return {
            "total_papers": total_papers,
            "total_indian_authors": len(indian_authors),
            "first_author_indian": first_author_indian,
            "majority_indian": majority_indian,
            "status_distribution": status_counts
        }
