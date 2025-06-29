"""
SQLite Link Hydrator for Tweet Generation Pipeline

Hydrates author profiles with Google Scholar and LinkedIn links from SQLite databases.
Provides intelligent author matching and caching mechanisms.
"""

import sqlite3
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from difflib import SequenceMatcher
from .state_manager import StateManager


class SQLiteLinkHydrator:
    """Hydrates author data with links from SQLite databases."""
    
    def __init__(self, state_manager: StateManager, config: 'PipelineConfig'):
        self.state_manager = state_manager
        self.config = config
        self.cache = {}
        self.processed_authors = set()
        
        # Author matching configuration
        self.name_similarity_threshold = 0.85
        self.affiliation_similarity_threshold = 0.7
        
        # Statistics
        self.stats = {
            'total_authors': 0,
            'processed_authors': 0,
            'scholar_links_found': 0,
            'linkedin_links_found': 0,
            'exact_matches': 0,
            'fuzzy_matches': 0,
            'no_matches': 0,
            'cache_hits': 0
        }
    
    def hydrate_authors(self, authors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Hydrate authors with links from SQLite databases."""
        print(f"🔗 Starting SQLite link hydration for {len(authors)} authors...")
        
        # Load existing progress
        progress = self.state_manager.load_checkpoint("hydration_progress.json") or {}
        hydrated_authors = []
        
        self.stats['total_authors'] = len(authors)
        
        # Get available SQLite databases
        db_paths = self._get_available_databases()
        print(f"  📊 Found {len(db_paths)} SQLite databases to query")
        
        # Load cache from previous runs
        self._load_cache()
        
        for author in authors:
            author_id = str(author["id"])
            
            # Check if already processed
            if author_id in progress and progress[author_id].get("status") == "completed":
                print(f"  ⏭️  Skipping {author['full_name']} (already processed)")
                hydrated_author = author.copy()
                hydrated_author.update(progress[author_id]["data"])
                hydrated_authors.append(hydrated_author)
                continue
            
            # Hydrate single author
            hydrated_author = self._hydrate_single_author(author, db_paths, progress)
            hydrated_authors.append(hydrated_author)
            
            # Save progress periodically
            if len(hydrated_authors) % 10 == 0:
                self._save_progress(progress)
        
        # Final save
        self.state_manager.save_checkpoint("hydrated_authors.json", hydrated_authors)
        self._save_progress(progress)
        self._save_cache()
        
        self._print_statistics()
        return hydrated_authors
    
    def _get_available_databases(self) -> List[Path]:
        """Get list of available SQLite databases."""
        db_paths = []
        data_dir = self.config.data_dir
        
        # Look for venue database files
        patterns = [
            "venues-*.db",
            "*-venues.db",
            "*.db"
        ]
        
        for pattern in patterns:
            matches = list(data_dir.glob(pattern))
            for match in matches:
                if match not in db_paths:
                    db_paths.append(match)
        
        return db_paths
    
    def _hydrate_single_author(self, author: Dict[str, Any], db_paths: List[Path], 
                             progress: Dict[str, Any]) -> Dict[str, Any]:
        """Hydrate a single author with links from databases."""
        author_id = str(author["id"])
        author_name = author.get("full_name", "Unknown Author")
        
        print(f"  🔍 Processing: {author_name}")
        
        # Initialize hydrated author
        hydrated_author = author.copy()
        hydration_data = {
            "sqlite_google_scholar": None,
            "sqlite_linkedin": None,
            "sqlite_homepage": None,
            "sqlite_email": None,
            "sqlite_orcid": None,
            "match_confidence": 0.0,
            "match_type": "none",
            "matched_from_db": None,
            "hydration_status": "no_match"
        }
        
        # Check cache first
        cache_key = self._generate_cache_key(author)
        if cache_key in self.cache:
            print(f"    💾 Cache hit")
            hydration_data.update(self.cache[cache_key])
            hydration_data["hydration_status"] = "cache_hit"
            self.stats['cache_hits'] += 1
        else:
            # Search in databases
            best_match = self._find_best_match(author, db_paths)
            
            if best_match:
                hydration_data.update(best_match)
                hydration_data["hydration_status"] = "matched"
                
                # Cache the result
                self.cache[cache_key] = best_match
                
                # Update statistics
                if best_match["match_type"] == "exact":
                    self.stats['exact_matches'] += 1
                else:
                    self.stats['fuzzy_matches'] += 1
                
                if best_match.get("sqlite_google_scholar"):
                    self.stats['scholar_links_found'] += 1
                    print(f"    🎓 Found Scholar: {best_match['sqlite_google_scholar']}")
                
                if best_match.get("sqlite_linkedin"):
                    self.stats['linkedin_links_found'] += 1
                    print(f"    💼 Found LinkedIn: {best_match['sqlite_linkedin']}")
                
                if best_match.get("sqlite_homepage"):
                    print(f"    🏠 Found Homepage: {best_match['sqlite_homepage']}")
                
            else:
                self.stats['no_matches'] += 1
                print(f"    ❌ No match found")
        
        # Update author with hydrated data
        hydrated_author.update(hydration_data)
        
        # Save individual progress
        progress[author_id] = {
            "status": "completed",
            "data": hydration_data,
            "processed_at": self.state_manager.get_current_timestamp()
        }
        
        self.stats['processed_authors'] += 1
        return hydrated_author
    
    def _find_best_match(self, author: Dict[str, Any], db_paths: List[Path]) -> Optional[Dict[str, Any]]:
        """Find the best matching author across all databases."""
        best_match = None
        best_confidence = 0.0
        
        author_name = author.get("full_name", "").strip()
        author_affiliation = author.get("affiliation_name", "").strip()
        
        if not author_name:
            return None
        
        for db_path in db_paths:
            try:
                matches = self._search_database(author_name, author_affiliation, db_path)
                
                for match in matches:
                    confidence = self._calculate_match_confidence(author, match)
                    
                    if confidence > best_confidence and confidence >= self.name_similarity_threshold:
                        best_confidence = confidence
                        best_match = match.copy()
                        best_match["match_confidence"] = confidence
                        best_match["matched_from_db"] = db_path.name
                        
                        # Determine match type
                        if confidence >= 0.95:
                            best_match["match_type"] = "exact"
                        else:
                            best_match["match_type"] = "fuzzy"
            
            except Exception as e:
                print(f"    ⚠️  Error querying {db_path.name}: {e}")
                continue
        
        return best_match
    
    def _search_database(self, author_name: str, author_affiliation: str, db_path: Path) -> List[Dict[str, Any]]:
        """Search for author in a specific database."""
        if not db_path.exists():
            return []
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            # Try multiple search strategies
            matches = []
            
            # Strategy 1: Exact name match
            exact_matches = self._search_by_exact_name(conn, author_name)
            matches.extend(exact_matches)
            
            # Strategy 2: Fuzzy name match
            if len(matches) < 5:  # Only do fuzzy search if we don't have many exact matches
                fuzzy_matches = self._search_by_fuzzy_name(conn, author_name)
                matches.extend(fuzzy_matches)
            
            # Strategy 3: Search by affiliation if we have it
            if author_affiliation and len(matches) < 10:
                affiliation_matches = self._search_by_affiliation(conn, author_name, author_affiliation)
                matches.extend(affiliation_matches)
            
            return matches
            
        finally:
            conn.close()
    
    def _search_by_exact_name(self, conn: sqlite3.Connection, author_name: str) -> List[Dict[str, Any]]:
        """Search by exact name match."""
        query = """
        SELECT DISTINCT
            a.full_name,
            a.email,
            a.google_scholar_link,
            a.linkedin,
            a.homepage,
            a.orcid,
            pa.affiliation_name,
            pa.affiliation_domain,
            pa.affiliation_country
        FROM authors a
        LEFT JOIN paper_authors pa ON a.id = pa.author_id
        WHERE LOWER(a.full_name) = LOWER(?)
        LIMIT 20
        """
        
        cursor = conn.execute(query, (author_name,))
        return [dict(row) for row in cursor.fetchall()]
    
    def _search_by_fuzzy_name(self, conn: sqlite3.Connection, author_name: str) -> List[Dict[str, Any]]:
        """Search by fuzzy name matching."""
        # Extract first and last name for better matching
        name_parts = author_name.strip().split()
        if len(name_parts) < 2:
            return []
        
        first_name = name_parts[0]
        last_name = name_parts[-1]
        
        query = """
        SELECT DISTINCT
            a.full_name,
            a.email,
            a.google_scholar_link,
            a.linkedin,
            a.homepage,
            a.orcid,
            pa.affiliation_name,
            pa.affiliation_domain,
            pa.affiliation_country
        FROM authors a
        LEFT JOIN paper_authors pa ON a.id = pa.author_id
        WHERE (LOWER(a.full_name) LIKE LOWER(?) OR LOWER(a.full_name) LIKE LOWER(?))
        LIMIT 30
        """
        
        pattern1 = f"%{first_name}%{last_name}%"
        pattern2 = f"%{last_name}%{first_name}%"
        
        cursor = conn.execute(query, (pattern1, pattern2))
        return [dict(row) for row in cursor.fetchall()]
    
    def _search_by_affiliation(self, conn: sqlite3.Connection, author_name: str, affiliation: str) -> List[Dict[str, Any]]:
        """Search by affiliation and name."""
        query = """
        SELECT DISTINCT
            a.full_name,
            a.email,
            a.google_scholar_link,
            a.linkedin,
            a.homepage,
            a.orcid,
            pa.affiliation_name,
            pa.affiliation_domain,
            pa.affiliation_country
        FROM authors a
        LEFT JOIN paper_authors pa ON a.id = pa.author_id
        WHERE LOWER(pa.affiliation_name) LIKE LOWER(?)
        AND LOWER(a.full_name) LIKE LOWER(?)
        LIMIT 20
        """
        
        affiliation_pattern = f"%{affiliation}%"
        name_pattern = f"%{author_name}%"
        
        cursor = conn.execute(query, (affiliation_pattern, name_pattern))
        return [dict(row) for row in cursor.fetchall()]
    
    def _calculate_match_confidence(self, author: Dict[str, Any], db_match: Dict[str, Any]) -> float:
        """Calculate confidence score for a potential match."""
        confidence = 0.0
        
        # Name similarity (most important factor)
        author_name = author.get("full_name", "").strip().lower()
        db_name = db_match.get("full_name", "").strip().lower()
        
        if author_name and db_name:
            name_similarity = SequenceMatcher(None, author_name, db_name).ratio()
            confidence += name_similarity * 0.7  # 70% weight for name
        
        # Affiliation similarity
        author_affiliation = author.get("affiliation_name", "").strip().lower()
        db_affiliation = db_match.get("affiliation_name", "").strip().lower()
        
        if author_affiliation and db_affiliation:
            affiliation_similarity = SequenceMatcher(None, author_affiliation, db_affiliation).ratio()
            confidence += affiliation_similarity * 0.2  # 20% weight for affiliation
        
        # Email domain matching
        author_domain = author.get("affiliation_domain", "").strip().lower()
        db_domain = db_match.get("affiliation_domain", "").strip().lower()
        
        if author_domain and db_domain and author_domain == db_domain:
            confidence += 0.1  # 10% bonus for matching email domain
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def _generate_cache_key(self, author: Dict[str, Any]) -> str:
        """Generate a cache key for an author."""
        name = author.get("full_name", "").strip().lower()
        affiliation = author.get("affiliation_name", "").strip().lower()
        return f"{name}|{affiliation}"
    
    def _load_cache(self) -> None:
        """Load cache from previous runs."""
        cache_data = self.state_manager.load_checkpoint("hydration_cache.json")
        if cache_data:
            self.cache = cache_data
            print(f"  💾 Loaded {len(self.cache)} cached entries")
    
    def _save_cache(self) -> None:
        """Save cache for future runs."""
        self.state_manager.save_checkpoint("hydration_cache.json", self.cache)
    
    def _save_progress(self, progress: Dict[str, Any]) -> None:
        """Save hydration progress."""
        self.state_manager.save_checkpoint("hydration_progress.json", progress)
        
        # Update state manager progress
        self.state_manager.update_progress(
            processed_authors=self.stats['processed_authors'],
            hydrated_authors=self.stats['processed_authors']
        )
    
    def _print_statistics(self) -> None:
        """Print hydration statistics."""
        print(f"\n🔗 SQLite Link Hydration Summary:")
        print(f"  📊 Total authors: {self.stats['total_authors']}")
        print(f"  ✅ Processed: {self.stats['processed_authors']}")
        print(f"  🎯 Exact matches: {self.stats['exact_matches']}")
        print(f"  🔍 Fuzzy matches: {self.stats['fuzzy_matches']}")
        print(f"  ❌ No matches: {self.stats['no_matches']}")
        print(f"  💾 Cache hits: {self.stats['cache_hits']}")
        print(f"  🎓 Scholar links found: {self.stats['scholar_links_found']}")
        print(f"  💼 LinkedIn links found: {self.stats['linkedin_links_found']}")
        
        if self.stats['processed_authors'] > 0:
            match_rate = (self.stats['exact_matches'] + self.stats['fuzzy_matches']) / self.stats['processed_authors'] * 100
            print(f"  📈 Overall match rate: {match_rate:.1f}%")
