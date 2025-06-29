"""
Card Integrator for Tweet Generation Pipeline

Integrates card.py functionality into the main pipeline.
Generates visual cards for papers and links them to tweets.
"""

import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from .state_manager import StateManager


class CardIntegrator:
    """Integrates card generation into the tweet pipeline."""
    
    def __init__(self, state_manager: StateManager, config: 'PipelineConfig'):
        self.state_manager = state_manager
        self.config = config
        
        # Card generation settings
        self.card_formats = ['png', 'jpg']  # Default formats
        self.card_quality = 95
        self.generate_pdf = True
        
        # Statistics
        self.stats = {
            'total_papers': 0,
            'cards_generated': 0,
            'cards_failed': 0,
            'formats_generated': {},
            'pdf_generated': False
        }
    
    def generate_cards_for_tweets(self, papers: List[Dict[str, Any]], 
                                 tweet_thread: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cards for papers and integrate with tweet thread."""
        print(f"🎨 Starting card generation for {len(papers)} papers...")
        
        # Check if already generated
        if self.state_manager.checkpoint_exists("generated_cards.json"):
            print("  ✅ Cards already generated, loading from checkpoint...")
            return self.state_manager.load_checkpoint("generated_cards.json")
        
        self.stats['total_papers'] = len(papers)
        
        # Prepare output directory
        cards_dir = self._prepare_cards_directory()
        
        # Convert papers to card-compatible format
        card_data = self._prepare_card_data(papers)
        
        # Generate cards using card.py
        card_results = self._generate_cards(card_data, cards_dir)
        
        # Link cards to tweets
        enhanced_tweet_thread = self._link_cards_to_tweets(tweet_thread, card_results)
        
        # Save results
        final_results = {
            "cards_directory": str(cards_dir),
            "card_results": card_results,
            "enhanced_tweet_thread": enhanced_tweet_thread,
            "statistics": self.stats,
            "generated_at": self.state_manager.get_current_timestamp()
        }
        
        self.state_manager.save_checkpoint("generated_cards.json", final_results)
        self._print_statistics()
        
        return final_results
    
    def _prepare_cards_directory(self) -> Path:
        """Prepare directory for card generation."""
        # Create cards directory in output
        output_dir = self.config.get_output_path()
        cards_dir = output_dir / "cards"
        cards_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"  📁 Cards directory: {cards_dir}")
        return cards_dir
    
    def _prepare_card_data(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert papers to card-compatible format."""
        card_data = []
        
        for paper in papers:
            # Convert to card.py expected format
            card_paper = {
                "title": paper.get("title", "Untitled"),
                "authors": self._format_authors_for_cards(paper.get("authors", [])),
                "conference": paper.get("conference", "ICML 2025"),
                "presentation_type": paper.get("presentation_type", "Research Paper"),
                "paper_id": paper.get("id", "")
            }
            
            card_data.append(card_paper)
        
        return card_data
    
    def _format_authors_for_cards(self, authors: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format authors for card generation."""
        formatted_authors = []
        
        for author in authors:
            # Convert country code to flag emoji
            country = author.get("affiliation_country", "")
            flag = self._country_to_flag(country)
            
            formatted_author = {
                "name": author.get("full_name", "Unknown Author"),
                "flag": flag
            }
            
            formatted_authors.append(formatted_author)
        
        return formatted_authors
    
    def _country_to_flag(self, country_code: str) -> str:
        """Convert country code to flag emoji."""
        flag_map = {
            "IN": "🇮🇳", "US": "🇺🇸", "GB": "🇬🇧", "CA": "🇨🇦", 
            "DE": "🇩🇪", "JP": "🇯🇵", "FR": "🇫🇷", "AU": "🇦🇺",
            "CN": "🇨🇳", "KR": "🇰🇷", "BR": "🇧🇷", "IT": "🇮🇹",
            "ES": "🇪🇸", "NL": "🇳🇱", "SE": "🇸🇪", "CH": "🇨🇭",
            "AT": "🇦🇹", "BE": "🇧🇪", "DK": "🇩🇰", "FI": "🇫🇮",
            "NO": "🇳🇴", "PL": "🇵🇱", "RU": "🇷🇺", "IL": "🇮🇱",
            "SG": "🇸🇬", "HK": "🇭🇰", "TW": "🇹🇼", "TH": "🇹🇭",
            "MX": "🇲🇽", "AR": "🇦🇷", "ZA": "🇿🇦"
        }
        
        return flag_map.get(country_code, "🌍")  # Default to world emoji
    
    def _generate_cards(self, card_data: List[Dict[str, Any]], cards_dir: Path) -> Dict[str, Any]:
        """Generate cards using card.py."""
        # Create temporary JSON file for card.py
        temp_json = cards_dir / "temp_papers.json"
        
        try:
            # Write card data to temporary file
            with open(temp_json, 'w', encoding='utf-8') as f:
                json.dump(card_data, f, indent=2, ensure_ascii=False)
            
            # Generate cards for each format
            card_results = {
                "formats": {},
                "pdf_path": None,
                "total_cards": len(card_data),
                "success": True,
                "error": None
            }
            
            for format_name in self.card_formats:
                format_results = self._generate_cards_format(temp_json, cards_dir, format_name)
                card_results["formats"][format_name] = format_results
                
                if format_results["success"]:
                    self.stats['cards_generated'] += format_results["cards_count"]
                    self.stats['formats_generated'][format_name] = format_results["cards_count"]
                else:
                    self.stats['cards_failed'] += len(card_data)
            
            # Generate PDF if requested
            if self.generate_pdf:
                pdf_result = self._generate_pdf(temp_json, cards_dir)
                card_results["pdf_path"] = pdf_result.get("pdf_path")
                self.stats['pdf_generated'] = pdf_result.get("success", False)
            
            return card_results
            
        except Exception as e:
            print(f"  ❌ Card generation failed: {e}")
            self.stats['cards_failed'] += len(card_data)
            return {
                "formats": {},
                "pdf_path": None,
                "total_cards": len(card_data),
                "success": False,
                "error": str(e)
            }
        
        finally:
            # Clean up temporary file
            if temp_json.exists():
                temp_json.unlink()
    
    def _generate_cards_format(self, json_file: Path, output_dir: Path, format_name: str) -> Dict[str, Any]:
        """Generate cards in a specific format."""
        try:
            # Get path to card.py - try multiple locations
            possible_paths = [
                Path("card.py"),  # Current directory
                Path("eda/tweetgen/card.py"),  # From project root
                Path(__file__).parent.parent / "card.py"  # Relative to this file
            ]
            
            card_script = None
            for path in possible_paths:
                if path.exists():
                    card_script = path
                    break
            
            if card_script is None:
                raise FileNotFoundError(f"card.py not found in any expected location")
            
            # Prepare command
            cmd = [
                "python", str(card_script),
                str(json_file),
                "--format", format_name,
                "--output", str(output_dir / format_name)
            ]
            
            print(f"  🎨 Generating {format_name.upper()} cards...")
            
            # Run card generation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            if result.returncode == 0:
                # Count generated files
                format_dir = output_dir / format_name
                if format_dir.exists():
                    card_files = list(format_dir.glob(f"*.{format_name}"))
                    print(f"    ✅ Generated {len(card_files)} {format_name.upper()} cards")
                    
                    return {
                        "success": True,
                        "cards_count": len(card_files),
                        "output_directory": str(format_dir),
                        "card_files": [str(f) for f in card_files],
                        "error": None
                    }
                else:
                    raise Exception(f"Output directory {format_dir} not created")
            else:
                raise Exception(f"Card generation failed: {result.stderr}")
                
        except Exception as e:
            print(f"    ❌ Failed to generate {format_name} cards: {e}")
            return {
                "success": False,
                "cards_count": 0,
                "output_directory": None,
                "card_files": [],
                "error": str(e)
            }
    
    def _generate_pdf(self, json_file: Path, output_dir: Path) -> Dict[str, Any]:
        """Generate PDF with all cards."""
        try:
            # Get path to card.py - try multiple locations
            possible_paths = [
                Path("card.py"),  # Current directory
                Path("eda/tweetgen/card.py"),  # From project root
                Path(__file__).parent.parent / "card.py"  # Relative to this file
            ]
            
            card_script = None
            for path in possible_paths:
                if path.exists():
                    card_script = path
                    break
            
            if card_script is None:
                raise FileNotFoundError(f"card.py not found in any expected location")
            
            # Use PNG format for PDF generation
            cmd = [
                "python", str(card_script),
                str(json_file),
                "--format", "png",
                "--output", str(output_dir / "pdf_temp"),
                "--pdf"
            ]
            
            print(f"  📄 Generating PDF...")
            
            # Run card generation with PDF
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            if result.returncode == 0:
                # Look for generated PDF
                pdf_files = list(output_dir.glob("**/*.pdf"))
                if pdf_files:
                    pdf_path = pdf_files[0]
                    # Move PDF to main cards directory
                    final_pdf = output_dir / "papers_cards.pdf"
                    if pdf_path != final_pdf:
                        shutil.move(str(pdf_path), str(final_pdf))
                    
                    print(f"    ✅ Generated PDF: {final_pdf}")
                    return {
                        "success": True,
                        "pdf_path": str(final_pdf),
                        "error": None
                    }
                else:
                    raise Exception("PDF file not found after generation")
            else:
                raise Exception(f"PDF generation failed: {result.stderr}")
                
        except Exception as e:
            print(f"    ❌ Failed to generate PDF: {e}")
            return {
                "success": False,
                "pdf_path": None,
                "error": str(e)
            }
    
    def _link_cards_to_tweets(self, tweet_thread: Dict[str, Any], 
                            card_results: Dict[str, Any]) -> Dict[str, Any]:
        """Link generated cards to corresponding tweets."""
        enhanced_thread = tweet_thread.copy()
        
        if not card_results.get("success", False):
            print("  ⚠️  Cards not generated successfully, skipping linking")
            return enhanced_thread
        
        # Get card files by format
        card_files_by_format = {}
        for format_name, format_data in card_results.get("formats", {}).items():
            if format_data.get("success", False):
                card_files_by_format[format_name] = format_data.get("card_files", [])
        
        # Link cards to paper tweets
        tweets = enhanced_thread.get("tweets", [])
        paper_tweet_index = 0
        
        for tweet in tweets:
            if tweet.get("type") == "paper":
                # Find corresponding card files
                if paper_tweet_index < len(card_files_by_format.get("png", [])):
                    tweet["attached_cards"] = {}
                    
                    # Add card files for each format
                    for format_name, card_files in card_files_by_format.items():
                        if paper_tweet_index < len(card_files):
                            tweet["attached_cards"][format_name] = card_files[paper_tweet_index]
                    
                    # Add PDF reference if available
                    if card_results.get("pdf_path"):
                        tweet["attached_cards"]["pdf_page"] = paper_tweet_index + 1
                        tweet["attached_cards"]["pdf_file"] = card_results["pdf_path"]
                
                paper_tweet_index += 1
        
        # Add card metadata to thread
        enhanced_thread["card_generation"] = {
            "cards_generated": card_results.get("success", False),
            "total_cards": card_results.get("total_cards", 0),
            "formats": list(card_files_by_format.keys()),
            "pdf_available": bool(card_results.get("pdf_path")),
            "cards_directory": card_results.get("cards_directory"),
            "generation_date": self.state_manager.get_current_timestamp()
        }
        
        print(f"  🔗 Linked cards to {paper_tweet_index} paper tweets")
        return enhanced_thread
    
    def _print_statistics(self) -> None:
        """Print card generation statistics."""
        print(f"\n🎨 Card Generation Summary:")
        print(f"  📊 Total papers: {self.stats['total_papers']}")
        print(f"  ✅ Cards generated: {self.stats['cards_generated']}")
        print(f"  ❌ Cards failed: {self.stats['cards_failed']}")
        
        if self.stats['formats_generated']:
            print(f"  🎯 Formats generated:")
            for format_name, count in self.stats['formats_generated'].items():
                print(f"    • {format_name.upper()}: {count} cards")
        
        if self.stats['pdf_generated']:
            print(f"  📄 PDF generated: ✅")
        else:
            print(f"  📄 PDF generated: ❌")
        
        if self.stats['total_papers'] > 0:
            success_rate = (self.stats['cards_generated'] / (self.stats['total_papers'] * len(self.card_formats))) * 100
            print(f"  📈 Success rate: {success_rate:.1f}%")
    
    def get_card_summary(self) -> Dict[str, Any]:
        """Get card generation summary for reporting."""
        return {
            "statistics": self.stats.copy(),
            "generation_date": self.state_manager.get_current_timestamp(),
            "formats_supported": self.card_formats,
            "pdf_enabled": self.generate_pdf
        }
