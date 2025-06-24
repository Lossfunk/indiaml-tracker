import sqlite3
import argparse
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConferenceAnalytics:
    """Class to generate analytics for conference papers with country-specific focus."""
    
    def __init__(self, db_path: str, institution_file: str):
        """
        Initialize the analytics engine.
        
        Args:
            db_path: Path to the SQLite database
            institution_file: Path to JSON file with institution variations
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # Load institution mappings
        try:
            with open(institution_file, 'r') as f:
                self.institution_variations = json.load(f)
            logger.info(f"Loaded institution variations from {institution_file}")
            
            # Build inverted index for direct institution resolution
            self.reverse_mapping = {}
            self.institution_types = {}
            
            for canonical_name, info in self.institution_variations.items():
                # Store the institute type
                self.institution_types[canonical_name] = info.get("type", "unknown")
                
                # Map each variation to the canonical name
                for variant in info.get("variations", []):
                    self.reverse_mapping[variant] = canonical_name
                    
            logger.info(f"Built institution mapping with {len(self.reverse_mapping)} variations")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load institution file: {e}")
            raise
                
        # Country mappings (moved from hardcoded values)
        self.country_map = {
            "US": "United States",
            "CN": "China",
            "UK": "United Kingdom",
            "IN": "India",
            "JP": "Japan",
            "DE": "Germany",
            "FR": "France",
            "CA": "Canada",
            "KR": "South Korea",
            "AU": "Australia",
            "UNK": "Unknown"
        }
        
        # APAC countries list
        self.apac_countries = ["CN", "IN", "JP", "KR", "AU", "SG", "MY", "TH", "VN", "ID"]
        
        self.color_scheme = {
            "us": "hsl(221, 83%, 53%)",
            "cn": "hsl(0, 84%, 60%)",
            "focusCountry": "hsl(36, 96%, 50%)",
            "primary": "hsl(var(--primary))",
            "secondary": "hsl(var(--secondary-foreground))",
            "academic": "hsl(221, 83%, 53%)",
            "corporate": "hsl(330, 80%, 60%)",
            "spotlight": "hsl(48, 96%, 50%)",
            "oral": "hsl(142, 71%, 45%)"
        }

    def connect_database(self) -> None:
        """Establish connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def close_database(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def normalize_institution_name(self, name: str) -> Tuple[str, str]:
        """
        Normalize institution names using direct lookup in the variations mapping.
        
        Args:
            name: Raw institution name
        
        Returns:
            Tuple[str, str]: (normalized_name, institution_type)
        """
        if not name:
            return "Unknown Institution", "unknown"
        
        # Find canonical name if it exists in our mapping
        canonical_name = self.reverse_mapping.get(name, name)
        
        # Get the institution type
        institution_type = self.institution_types.get(canonical_name, "unknown")
        
        return canonical_name, institution_type
    
    def get_country_name(self, country_code: str) -> str:
        """
        Get the full name of a country from its code.
        
        Args:
            country_code: Two-letter country code
        
        Returns:
            str: Full country name
        """
        return self.country_map.get(country_code.upper(), country_code)
        
    def fetch_conference_info(self, conference_name: str, year: int, track: str) -> Dict:
        """
        Get conference info and total accepted papers.
        
        Args:
            conference_name: Name of the conference
            year: Year of the conference
            track: Track of the conference
            
        Returns:
            Dict: Conference information including total accepted papers
        """
        self.cursor.execute("""
            SELECT COUNT(*) AS total
            FROM papers p
            JOIN venue_infos vi ON p.venue_info_id = vi.id
            WHERE vi.conference = ? AND vi.year = ? AND vi.track = ? AND p.status = 'accepted'
        """, (conference_name, year, track))
        
        total_accepted_papers = self.cursor.fetchone()['total']
        
        return {
            "name": conference_name,
            "year": year,
            "track": track,
            "totalAcceptedPapers": total_accepted_papers
        }
    
    def fetch_papers(self, conference_name: str, year: int, track: str) -> Dict:
        """
        Get all accepted papers for the specified conference.
        
        Args:
            conference_name: Name of the conference
            year: Year of the conference
            track: Track of the conference
            
        Returns:
            Dict: Dictionary of papers indexed by paper_id
        """
        self.cursor.execute("""
            SELECT 
                p.id,
                p.title,
                p.status
            FROM 
                papers p
            JOIN
                venue_infos vi ON p.venue_info_id = vi.id
            WHERE 
                vi.conference = ? AND vi.year = ? AND vi.track = ?
                AND p.status = 'accepted'
        """, (conference_name, year, track))
        
        papers = {}
        for row in self.cursor.fetchall():
            paper_id = row['id']
            papers[paper_id] = {
                'id': paper_id,
                'title': row['title'],
                'status': row['status'],
                'isSpotlight': False,  # Not available in this database schema
                'isOral': False,      # Not available in this database schema
                'authors': [],
                'countries': set(),
                'institutions': [],
                'focus_country_authors': 0,
                'total_authors': 0
            }
        
        logger.info(f"Found {len(papers)} papers for {conference_name} {year} {track}")
        return papers
    
    def fetch_paper_authors(self, paper_ids: List[str]) -> List:
        """
        Get author information for the specified papers.
        
        Args:
            paper_ids: List of paper IDs
            
        Returns:
            List: Author information rows
        """
        if not paper_ids:
            logger.warning("No paper IDs provided to fetch authors")
            return []
        
        placeholder = ','.join(['?'] * len(paper_ids))
        query = f"""
            SELECT 
                pa.paper_id,
                pa.position,
                a.id AS author_id,
                a.full_name,
                pa.affiliation_name,
                pa.affiliation_domain,
                pa.affiliation_country
            FROM 
                paper_authors pa
            JOIN
                authors a ON pa.author_id = a.id
            WHERE 
                pa.paper_id IN ({placeholder})
            ORDER BY
                pa.paper_id, pa.position
        """
        
        try:
            self.cursor.execute(query, paper_ids)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching paper authors: {e}")
            raise
    
    def process_authors(self, author_rows: List, papers: Dict, focus_country: str) -> Tuple[Dict, Dict]:
        """
        Process authors and update paper data with author information.
        """
        country_stats = defaultdict(lambda: {
            'paper_count': 0, 
            'author_count': 0, 
            'spotlights': set(),  # Using sets for deduplication
            'orals': set(),
            'papers': set()
        })
        
        # Track authors and papers per institution for proper deduplication
        institution_stats = defaultdict(lambda: {
            'paper_count': 0,
            'author_count': 0,
            'spotlights': set(),
            'orals': set(),
            'papers': set(),
            'authors': set(),
            'type': 'unknown',
            'country': 'UNK'
        })
        
        # First pass - process all authors and update paper data
        for row in author_rows:
            paper_id = row['paper_id']
            if paper_id not in papers:
                continue
                
            paper = papers[paper_id]
            author_id = row['author_id']
            author_name = row['full_name']
            position = row['position']
            country = row['affiliation_country'] or 'UNK'
            
            # Normalize institution name using the direct lookup approach
            institution_name, institution_type = self.normalize_institution_name(row['affiliation_name'])
            
            # Add author to paper's data
            author_info = {
                'id': author_id,
                'name': author_name,
                'position': position,
                'country': country,
                'institution': institution_name
            }
            paper['authors'].append(author_info)
            paper['countries'].add(country)
            paper['institutions'].append(institution_name)
            paper['total_authors'] += 1
            
            if country.upper() == focus_country.upper():
                paper['focus_country_authors'] += 1
            
            # Update country statistics
            country_stats[country]['author_count'] += 1
            country_stats[country]['papers'].add(paper_id)
            if paper['isSpotlight']:
                country_stats[country]['spotlights'].add(paper_id)
            if paper['isOral']:
                country_stats[country]['orals'].add(paper_id)
            
            # Update institution statistics - ensuring proper deduplication
            institution_stats[institution_name]['papers'].add(paper_id)
            institution_stats[institution_name]['authors'].add(author_name)
            institution_stats[institution_name]['type'] = institution_type
            institution_stats[institution_name]['country'] = country
            if paper['isSpotlight']:
                institution_stats[institution_name]['spotlights'].add(paper_id)
            if paper['isOral']:
                institution_stats[institution_name]['orals'].add(paper_id)
        
        # Convert sets to counts for the final output
        for country, stats in country_stats.items():
            stats['paper_count'] = len(stats['papers'])
            stats['spotlights'] = len(stats['spotlights'])
            stats['orals'] = len(stats['orals'])
        
        # Process institution statistics
        final_institution_stats = {}
        for name, stats in institution_stats.items():
            final_institution_stats[name] = {
                'paper_count': len(stats['papers']),
                'author_count': len(stats['authors']),
                'spotlights': len(stats['spotlights']),
                'orals': len(stats['orals']),
                'papers': stats['papers'],
                'authors': stats['authors'],
                'type': stats['type'],
                'country': stats['country']
            }
        
        return country_stats, final_institution_stats
    

    def categorize_papers_by_country(self, papers: Dict, focus_country: str) -> Dict:
        """
        Categorize papers by author country focus.
        
        Args:
            papers: Dictionary of papers
            focus_country: Country code to focus on
            
        Returns:
            Dict: Categorized papers dict
        """
        focus_country = focus_country.upper()
        focus_country_papers = {
            'at_least_one': [],
            'majority': [],
            'first_author': []
        }
        
        for paper_id, paper in papers.items():
            if focus_country in paper['countries']:
                # Papers with at least one author from focus country
                focus_country_papers['at_least_one'].append({
                    'id': paper_id,
                    'title': paper['title'],
                    'isSpotlight': paper['isSpotlight'],
                    'isOral': paper['isOral']
                })
                
                # Check if majority of authors are from focus country
                if paper['focus_country_authors'] > paper['total_authors'] / 2:
                    focus_country_papers['majority'].append({
                        'id': paper_id,
                        'title': paper['title'],
                        'isSpotlight': paper['isSpotlight'],
                        'isOral': paper['isOral']
                    })
                
                # Check if first author is from focus country
                if paper['authors'] and paper['authors'][0]['country'].upper() == focus_country:
                    focus_country_papers['first_author'].append({
                        'id': paper_id,
                        'title': paper['title'],
                        'isSpotlight': paper['isSpotlight'],
                        'isOral': paper['isOral']
                    })
        
        return focus_country_papers
    
    def process_focus_country_institutions(self, institution_stats: Dict, papers: Dict, 
                                        focus_country_papers: Dict, focus_country: str) -> Tuple[List, Dict]:
        """
        Process institutions for the focus country.
        
        Args:
            institution_stats: Dictionary of institution statistics
            papers: Dictionary of papers
            focus_country_papers: Categorized papers by country focus
            focus_country: Country code to focus on
            
        Returns:
            Tuple[List, Dict]: (focus_country_institutions, institution_types_count)
        """
        focus_country_institutions = []
        institution_types_count = defaultdict(int)
        
        focus_country_upper = focus_country.upper()
        
        for name, stats in institution_stats.items():
            # Skip institutions not from the focus country
            if stats['country'].upper() != focus_country_upper:
                continue
            
            # Count institution types
            institution_types_count[stats['type']] += 1
            
            # Collect first-author papers from this institution
            first_author_papers = [p for p in stats['papers'] 
                                 if p in [paper['id'] for paper in focus_country_papers['first_author']]]
            
            # Add to focus country institutions
            focus_country_institutions.append({
                'institute': name,
                'total_paper_count': len(stats['papers']),
                'unique_paper_count': len(first_author_papers),
                'author_count': len(stats['authors']),
                'spotlights': stats['spotlights'],
                'orals': stats['orals'],
                'type': stats['type'],
                'papers': [
                    {
                        'id': p,
                        'title': papers[p]['title'],
                        'isSpotlight': papers[p]['isSpotlight'],
                        'isOral': papers[p]['isOral']
                    } for p in stats['papers']
                ],
                'authors': list(stats['authors'])
            })
        
        # Sort institutions by paper count
        focus_country_institutions.sort(key=lambda x: x['total_paper_count'], reverse=True)
        return focus_country_institutions, institution_types_count


    def generate_insights(self, data: Dict) -> None:
        """
        Generate insights for the dashboard based on the data.
        
        Args:
            data: Analytics data dict
        """
        conference_info = data['conferenceInfo']
        focus_country = data['focusCountry']
        global_stats = data['globalStats']['countries']
        
        # Sort countries by paper count
        countries_by_papers = sorted(global_stats, key=lambda x: x['paper_count'], reverse=True)
        
        # Find focus country rank
        focus_country_rank = next((i+1 for i, c in enumerate(countries_by_papers) 
                                  if c['affiliation_country'] == focus_country['country_code']), "N/A")
        
        # Calculate percentages
        if conference_info['totalAcceptedPapers'] > 0:
            focus_papers_percentage = (focus_country['at_least_one_focus_country_author']['count'] / 
                                      conference_info['totalAcceptedPapers']) * 100
        else:
            focus_papers_percentage = 0
        
        # Generate the different sections of insights
        self._generate_summary_insights(data, conference_info, focus_country, focus_papers_percentage, focus_country_rank)
        self._generate_context_insights(data, countries_by_papers)
        self._generate_focus_country_insights(data, conference_info, focus_country)
        self._generate_institution_insights(data, conference_info, focus_country)
    
    def _generate_summary_insights(self, data: Dict, conference_info: Dict, focus_country: Dict, 
                                percentage: float, rank: str) -> None:
        """Generate enhanced summary insights section."""
        summary_insights = [
            f"{focus_country['country_name']}'s ML researchers are making their mark with {focus_country['at_least_one_focus_country_author']['count']} papers at {conference_info['name']} {conference_info['year']}, including {focus_country['total_spotlights']} spotlight and {focus_country['total_orals']} oral presentations that demonstrate the quality of research.",
            f"Positioned globally, {focus_country['country_name']} contributes {percentage:.1f}% to the body of work at {conference_info['name']} {conference_info['year']}.",
            f"Analysis of {focus_country['first_focus_country_author']['count']} first authorship and {focus_country['majority_focus_country_authors']['count']} majority authorship collaborations reveals trends in research leadership and international collaboration.",
            f"The {focus_country['country_name']} ML research landscape shows a mix of {focus_country['institution_types']['academic']} academic and {focus_country['institution_types']['corporate']} corporate contributions, with leading institutions demonstrating significant research impact."
        ]
        
        data['configuration']['sections']['summary']['insights'] = summary_insights


    
    def _generate_context_insights(self, data: Dict, countries_by_papers: List) -> None:
        """Generate context insights section."""
        top_countries = [c['affiliation_country'] for c in countries_by_papers[:5]]
        context_insights = [
            f"The top 5 contributing countries were: {', '.join(self.get_country_name(c) for c in top_countries)}.",
        ]
        
        data['configuration']['sections']['context']['insights'] = context_insights
    
    def _generate_focus_country_insights(self, data: Dict, conference_info: Dict, focus_country: Dict) -> None:
        """Generate focus country insights section."""
        focus_insights = [
            f"{focus_country['country_name']} had {focus_country['total_authors']} unique authors contributing to {conference_info['name']} {conference_info['year']}.",
            f"{focus_country['first_focus_country_author']['count']} papers had a first author from {focus_country['country_name']}.",
            f"{focus_country['majority_focus_country_authors']['count']} papers had a majority of authors from {focus_country['country_name']}."
        ]
        
        data['configuration']['sections']['focusCountry']['insights'] = focus_insights
    
    def _generate_institution_insights(self, data: Dict, conference_info: Dict, focus_country: Dict) -> None:
        """Generate institution insights section."""
        institution_insights = []
        
        if focus_country['institutions']:
            top_institution = focus_country['institutions'][0]['institute']
            top_institution_papers = focus_country['institutions'][0]['total_paper_count']
            institution_insights.append(
                f"{top_institution} was the top contributing institution from {focus_country['country_name']} with {top_institution_papers} papers."
            )
        
        institution_insights.append(
            f"{focus_country['country_name']} had {focus_country['institution_types']['academic']} academic and {focus_country['institution_types']['corporate']} corporate institutions contributing to {conference_info['name']} {conference_info['year']}."
        )
        
        data['configuration']['sections']['institutions']['insights'] = institution_insights

    def fetch_all_accepted_authors(self, conference_name: str, year: int, track: str) -> int:
        """
        Get the total count of unique authors for all accepted papers.
        
        Args:
            conference_name: Name of the conference
            year: Year of the conference
            track: Track of the conference
            
        Returns:
            int: Total count of unique authors
        """
        # First get all accepted paper IDs
        self.cursor.execute("""
            SELECT p.id
            FROM papers p
            JOIN venue_infos vi ON p.venue_info_id = vi.id
            WHERE vi.conference = ? AND vi.year = ? AND vi.track = ? AND p.status = 'accepted'
        """, (conference_name, year, track))
        
        paper_ids = [row['id'] for row in self.cursor.fetchall()]
        
        if not paper_ids:
            return 0
            
        # Now get all unique authors for these papers
        placeholder = ','.join(['?'] * len(paper_ids))
        query = f"""
            SELECT COUNT(DISTINCT author_id) AS total_authors
            FROM paper_authors
            WHERE paper_id IN ({placeholder})
        """
        
        try:
            self.cursor.execute(query, paper_ids)
            result = self.cursor.fetchone()
            return result['total_authors'] if result else 0
        except sqlite3.Error as e:
            logger.error(f"Error fetching total authors: {e}")
            return 0


    def analyze(self, focus_country: str, conference_name: str, year: int, 
               track: str, output_file: str) -> None:
        """
        Generate comprehensive analytics for papers from a specific conference venue.
        
        Args:
            focus_country: Country code to focus on (e.g., "IN" for India)
            conference_name: Name of the conference (e.g., "NeurIPS")
            year: Year of the conference
            track: Track of the conference (e.g., "Conference")
            output_file: Path to save the JSON output
        """
        try:
            self.connect_database()
            logger.info(f"Starting analysis for {conference_name} {year} with focus on {focus_country}")
            
            # Get conference info and initialize output structure
            conference_info = self.fetch_conference_info(conference_name, year, track)
            
            # Get total unique authors across all accepted papers
            total_authors = self.fetch_all_accepted_authors(conference_name, year, track)
            conference_info["totalAcceptedAuthors"] = total_authors
            
            output = self._initialize_output_structure(focus_country, conference_info)
            
            # Get papers and authors
            papers = self.fetch_papers(conference_name, year, track)
            if not papers:
                logger.warning(f"No papers found for {conference_name} {year} {track}")
                return
            
            # Process author data
            author_rows = self.fetch_paper_authors(list(papers.keys()))
            country_stats, institution_stats = self.process_authors(author_rows, papers, focus_country)
            
            # Update global country statistics
            self._update_global_stats(output, country_stats)
            
            # Process focus country data
            focus_country_upper = focus_country.upper()
            focus_country_papers = self.categorize_papers_by_country(papers, focus_country_upper)
            
            # Update focus country statistics
            self._update_focus_country_stats(output, focus_country_upper, country_stats, focus_country_papers)
            
            # Process institutions
            focus_institutions, institution_types = self.process_focus_country_institutions(
                institution_stats, papers, focus_country_papers, focus_country_upper
            )
            
            output['focusCountry']['institutions'] = focus_institutions
            output['focusCountry']['institution_types']['academic'] = institution_types.get('academic', 0)
            output['focusCountry']['institution_types']['corporate'] = institution_types.get('corporate', 0)
            
            # Generate insights
            self.generate_insights(output)
            
            # Save output to file
            with open(output_file, 'w') as f:
                json.dump(output, f, indent=2)
            
            logger.info(f"Analysis complete. Results saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Error in analysis: {e}", exc_info=True)
            raise
        finally:
            self.close_database()    

    def _initialize_output_structure(self, focus_country: str, conference_info: Dict) -> Dict:
        """Initialize the output data structure with complete configuration."""
        return {
            "conferenceInfo": {
                **conference_info,
            },
            "globalStats": {
                "countries": []
            },
            "focusCountry": {
                "country_code": focus_country,
                "country_name": self.get_country_name(focus_country),
                "total_authors": 0,
                "total_spotlights": 0,
                "total_orals": 0,
                "institution_types": {
                    "corporate": 0,
                    "academic": 0
                },
                "at_least_one_focus_country_author": {
                    "count": 0,
                    "papers": []
                },
                "majority_focus_country_authors": {
                    "count": 0,
                    "papers": []
                },
                "first_focus_country_author": {
                    "count": 0,
                    "papers": []
                },
                "institutions": []
            },
            "configuration": {
                "countryMap": self.country_map,
                "apacCountries": self.apac_countries,
                "colorScheme": {
                    "us": "hsl(221, 83%, 53%)",
                    "cn": "hsl(0, 84%, 60%)",
                    "focusCountry": "hsl(36, 96%, 50%)",
                    "primary": "hsl(var(--primary))",
                    "secondary": "hsl(var(--secondary-foreground))",
                    "academic": "hsl(221, 83%, 53%)",
                    "corporate": "hsl(330, 80%, 60%)",
                    "spotlight": "hsl(48, 96%, 50%)",
                    "oral": "hsl(142, 71%, 45%)"
                },
                "dashboardTitle": f"{self.get_country_name(focus_country)} @ {conference_info['name']} {conference_info['year']}",
                "dashboardSubtitle": f"{self.get_country_name(focus_country)}'s Contributions, Global Context & Institutional Landscape",
                "sections": {
                    "summary": {
                        "title": "Executive Summary: Impact at a Glance",
                        "insights": []
                    },
                    "context": {
                        "title": "Global & APAC Context: India's Standing",
                        "subtitle": "Comparing India's research output with global and regional peers.",
                        "insights": []
                    },
                    "focusCountry": {
                        "title": f"{self.get_country_name(focus_country)} Deep Dive",
                        "subtitle": "Analyzing authorship, collaboration, and institutional contributions.",
                        "insights": []
                    },
                    "institutions": {
                        "title": "Institutions: Internal Ecosystem",
                        "subtitle": "Analyzing the performance and impact of individual institutions within India.",
                        "insights": []
                    }
                }
            },
            "credits": [
                {
                    "name": "Sohan",
                    "link": "https://x.com/HiSohan"
                },
                {
                    "name": "Paras",
                    "link": "https://x.com/paraschopra"
                }
            ]
        }
    
    def _update_global_stats(self, output: Dict, country_stats: Dict) -> None:
        """Update global statistics section with country data."""
        for country, stats in country_stats.items():
            output['globalStats']['countries'].append({
                'affiliation_country': country,
                'paper_count': stats['paper_count'],
                'author_count': stats['author_count'],
                'spotlights': stats['spotlights'],
                'orals': stats['orals']
            })
        
        # Sort countries by paper count
        output['globalStats']['countries'].sort(key=lambda x: x['paper_count'], reverse=True)
    
    def _update_focus_country_stats(self, output: Dict, focus_country: str, 
                                country_stats: Dict, focus_country_papers: Dict) -> None:
        """Update focus country statistics in the output."""
        output['focusCountry']['total_authors'] = country_stats.get(focus_country, {}).get('author_count', 0)
        output['focusCountry']['total_spotlights'] = country_stats.get(focus_country, {}).get('spotlights', 0)
        output['focusCountry']['total_orals'] = country_stats.get(focus_country, {}).get('orals', 0)
        
        # The rest of the method remains unchanged
        output['focusCountry']['at_least_one_focus_country_author']['count'] = len(focus_country_papers['at_least_one'])
        output['focusCountry']['at_least_one_focus_country_author']['papers'] = focus_country_papers['at_least_one']
        
        output['focusCountry']['majority_focus_country_authors']['count'] = len(focus_country_papers['majority'])
        output['focusCountry']['majority_focus_country_authors']['papers'] = focus_country_papers['majority']
        
        output['focusCountry']['first_focus_country_author']['count'] = len(focus_country_papers['first_author'])
        output['focusCountry']['first_focus_country_author']['papers'] = focus_country_papers['first_author']

def main():
    """Parse command-line arguments and run the conference analytics."""
    parser = argparse.ArgumentParser(description='Generate conference analytics with focus on a specific country')
    
    # Required arguments
    parser.add_argument('--db_path', required=True, help='Path to the SQLite database')
    parser.add_argument('--country_code', required=True, help='Country code to focus on (e.g., IN for India)')
    parser.add_argument('--institution_file', required=True, help='Path to JSON file with institution variations')
    
    # Conference details
    parser.add_argument('--conference_name', required=True, help='Name of the conference (e.g., NeurIPS)')
    parser.add_argument('--conference_year', required=True, type=int, help='Year of the conference')
    parser.add_argument('--conference_track', required=True, help='Track of the conference (e.g., Conference)')
    
    # Output options
    parser.add_argument('--output', default='conference_analytics.json', help='Path to save the JSON output')
    
    args = parser.parse_args()
    
    try:
        # Create the analytics engine and run the analysis
        analytics = ConferenceAnalytics(args.db_path, args.institution_file)
        analytics.analyze(
            args.country_code,
            args.conference_name,
            args.conference_year,
            args.conference_track,
            args.output
        )
        logger.info(f"Analytics successfully generated for {args.conference_name} {args.conference_year} with focus on {args.country_code}")
        return 0
    except Exception as e:
        logger.error(f"Error running analysis: {e}")
        return 1


if __name__ == "__main__":
    main()
