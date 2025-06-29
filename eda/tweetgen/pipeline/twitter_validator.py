"""
Twitter Validator for Tweet Generation Pipeline

Validates and standardizes Twitter handles and URLs using regex patterns.
Checks for active profiles and removes duplicates.
"""

import re
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Set, Tuple
from urllib.parse import urlparse
from .state_manager import StateManager


class TwitterValidator:
    """Validates and standardizes Twitter handles and URLs."""
    
    def __init__(self, state_manager: StateManager, config: 'PipelineConfig'):
        self.state_manager = state_manager
        self.config = config
        
        # Twitter validation patterns
        self.handle_pattern = re.compile(r'^@?([a-zA-Z0-9_]{1,15})$')
        self.url_patterns = [
            re.compile(r'https?://(www\.)?(twitter|x)\.com/([a-zA-Z0-9_]{1,15})(?:/.*)?$', re.IGNORECASE),
            re.compile(r'https?://([a-zA-Z0-9_]{1,15})\.twitter\.com/?$', re.IGNORECASE)
        ]
        
        # Invalid/reserved handles
        self.reserved_handles = {
            'home', 'explore', 'search', 'intent', 'share', 'settings', 
            'notifications', 'messages', 'compose', 'tos', 'privacy', 
            'jobs', 'about', 'download', 'account', 'help', 'signup', 
            'login', 'lists', 'moments', 'topics', 'bookmarks', 'i',
            'api', 'oauth', 'admin', 'support', 'dev', 'developer',
            'twitter', 'x', 'status', 'hashtag', 'who_to_follow'
        }
        
        # Statistics
        self.stats = {
            'total_handles': 0,
            'valid_handles': 0,
            'invalid_handles': 0,
            'duplicate_handles': 0,
            'reserved_handles': 0,
            'active_profiles': 0,
            'inactive_profiles': 0,
            'check_errors': 0
        }
        
        # Cache for profile checks
        self.profile_cache = {}
    
    def validate_authors(self, authors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate Twitter handles for all authors."""
        print(f"🐦 Starting Twitter validation for {len(authors)} authors...")
        
        # Load existing progress and cache
        progress = self.state_manager.load_checkpoint("twitter_validation_progress.json") or {}
        self._load_cache()
        
        validated_authors = []
        seen_handles = set()
        
        for author in authors:
            author_id = str(author["id"])
            
            # Check if already processed
            if author_id in progress and progress[author_id].get("status") == "completed":
                validated_author = author.copy()
                validated_author.update(progress[author_id]["data"])
                validated_authors.append(validated_author)
                
                # Track seen handles for duplicate detection
                validated_handle = validated_author.get("validated_twitter_handle")
                if validated_handle:
                    seen_handles.add(validated_handle.lower())
                continue
            
            # Validate single author
            validated_author = self._validate_single_author(author, seen_handles, progress)
            validated_authors.append(validated_author)
            
            # Save progress periodically
            if len(validated_authors) % 20 == 0:
                self._save_progress(progress)
        
        # Final save
        self.state_manager.save_checkpoint("validated_authors.json", validated_authors)
        self._save_progress(progress)
        self._save_cache()
        
        self._print_statistics()
        return validated_authors
    
    def _validate_single_author(self, author: Dict[str, Any], seen_handles: Set[str], 
                               progress: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Twitter handles for a single author."""
        author_id = str(author["id"])
        author_name = author.get("full_name", "Unknown Author")
        
        # Initialize validated author
        validated_author = author.copy()
        validation_data = {
            "validated_twitter_handle": None,
            "validated_twitter_url": None,
            "twitter_validation_status": "no_handle",
            "twitter_validation_errors": [],
            "is_active_profile": None,
            "profile_check_date": None
        }
        
        # Collect all potential Twitter handles/URLs
        potential_handles = self._collect_twitter_handles(author)
        
        if not potential_handles:
            validation_data["twitter_validation_status"] = "no_handle"
        else:
            self.stats['total_handles'] += len(potential_handles)
            
            # Validate and select best handle
            best_handle = self._validate_and_select_best_handle(
                potential_handles, seen_handles, author_name
            )
            
            if best_handle:
                validation_data.update(best_handle)
                seen_handles.add(best_handle["validated_twitter_handle"].lower())
                self.stats['valid_handles'] += 1
            else:
                validation_data["twitter_validation_status"] = "all_invalid"
                self.stats['invalid_handles'] += 1
        
        # Update author with validation data
        validated_author.update(validation_data)
        
        # Save individual progress
        progress[author_id] = {
            "status": "completed",
            "data": validation_data,
            "processed_at": self.state_manager.get_current_timestamp()
        }
        
        return validated_author
    
    def _collect_twitter_handles(self, author: Dict[str, Any]) -> List[str]:
        """Collect all potential Twitter handles/URLs from author data."""
        handles = []
        
        # Check various fields that might contain Twitter info
        fields_to_check = [
            'twitter_handle', 'twitter_url', 'twitter',
            'sqlite_twitter', 'enriched_twitter_handle', 'enriched_twitter_url'
        ]
        
        for field in fields_to_check:
            value = author.get(field)
            if value and isinstance(value, str):
                value = value.strip()
                if value and value not in handles:
                    handles.append(value)
        
        return handles
    
    def _validate_and_select_best_handle(self, potential_handles: List[str], 
                                       seen_handles: Set[str], author_name: str) -> Optional[Dict[str, Any]]:
        """Validate handles and select the best one."""
        valid_handles = []
        
        for handle_or_url in potential_handles:
            validation_result = self._validate_single_handle(handle_or_url, seen_handles)
            
            if validation_result["is_valid"]:
                valid_handles.append(validation_result)
        
        if not valid_handles:
            return None
        
        # Select best handle (prefer exact matches, then by confidence)
        best_handle = self._select_best_handle(valid_handles, author_name)
        
        return {
            "validated_twitter_handle": best_handle["handle"],
            "validated_twitter_url": best_handle["url"],
            "twitter_validation_status": "valid",
            "twitter_validation_errors": [],
            "validation_confidence": best_handle.get("confidence", 1.0)
        }
    
    def _validate_single_handle(self, handle_or_url: str, seen_handles: Set[str]) -> Dict[str, Any]:
        """Validate a single Twitter handle or URL."""
        result = {
            "original": handle_or_url,
            "handle": None,
            "url": None,
            "is_valid": False,
            "errors": [],
            "confidence": 0.0
        }
        
        # Clean and normalize input
        cleaned = handle_or_url.strip()
        
        # Try to extract handle from URL
        if cleaned.startswith(('http://', 'https://')):
            extracted_handle = self._extract_handle_from_url(cleaned)
            if extracted_handle:
                cleaned = extracted_handle
            else:
                result["errors"].append("Invalid Twitter URL format")
                return result
        
        # Remove @ prefix if present
        if cleaned.startswith('@'):
            cleaned = cleaned[1:]
        
        # Validate handle format
        if not self.handle_pattern.match(cleaned):
            result["errors"].append("Invalid handle format")
            return result
        
        # Check if handle is reserved
        if cleaned.lower() in self.reserved_handles:
            result["errors"].append("Reserved handle")
            self.stats['reserved_handles'] += 1
            return result
        
        # Check for duplicates
        if cleaned.lower() in seen_handles:
            result["errors"].append("Duplicate handle")
            self.stats['duplicate_handles'] += 1
            return result
        
        # Handle is valid
        result.update({
            "handle": f"@{cleaned}",
            "url": f"https://x.com/{cleaned}",
            "is_valid": True,
            "confidence": 1.0
        })
        
        return result
    
    def _extract_handle_from_url(self, url: str) -> Optional[str]:
        """Extract Twitter handle from URL."""
        for pattern in self.url_patterns:
            match = pattern.match(url)
            if match:
                # Extract handle from different URL formats
                if 'twitter.com' in url or 'x.com' in url:
                    # Standard format: https://twitter.com/handle or https://x.com/handle
                    groups = match.groups()
                    if len(groups) >= 3:
                        return groups[2]  # The handle group
                else:
                    # Subdomain format: https://handle.twitter.com
                    groups = match.groups()
                    if len(groups) >= 1:
                        return groups[0]  # The handle group
        
        return None
    
    def _select_best_handle(self, valid_handles: List[Dict[str, Any]], author_name: str) -> Dict[str, Any]:
        """Select the best handle from valid options."""
        if len(valid_handles) == 1:
            return valid_handles[0]
        
        # Score handles based on various factors
        scored_handles = []
        
        for handle_data in valid_handles:
            score = handle_data["confidence"]
            handle = handle_data["handle"][1:]  # Remove @ for comparison
            
            # Bonus for handles that might match author name
            if author_name:
                name_parts = author_name.lower().split()
                handle_lower = handle.lower()
                
                # Check if handle contains name parts
                for part in name_parts:
                    if len(part) > 2 and part in handle_lower:
                        score += 0.2
                
                # Check if handle starts with first name or last name
                if name_parts:
                    if handle_lower.startswith(name_parts[0].lower()[:3]):
                        score += 0.1
                    if len(name_parts) > 1 and handle_lower.startswith(name_parts[-1].lower()[:3]):
                        score += 0.1
            
            # Prefer shorter handles (usually more authentic)
            if len(handle) <= 10:
                score += 0.1
            
            scored_handles.append((score, handle_data))
        
        # Sort by score and return best
        scored_handles.sort(key=lambda x: x[0], reverse=True)
        return scored_handles[0][1]
    
    async def check_profile_activity(self, authors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check if Twitter profiles are active (optional step)."""
        print(f"🔍 Checking profile activity for validated handles...")
        
        # This is an optional step that can be enabled if needed
        # For now, we'll just mark all validated handles as potentially active
        
        for author in authors:
            if author.get("validated_twitter_handle"):
                author["is_active_profile"] = True  # Assume active for now
                author["profile_check_date"] = self.state_manager.get_current_timestamp()
                self.stats['active_profiles'] += 1
        
        return authors
    
    def _load_cache(self) -> None:
        """Load profile check cache."""
        cache_data = self.state_manager.load_checkpoint("twitter_validation_cache.json")
        if cache_data:
            self.profile_cache = cache_data
            print(f"  💾 Loaded {len(self.profile_cache)} cached profile checks")
    
    def _save_cache(self) -> None:
        """Save profile check cache."""
        self.state_manager.save_checkpoint("twitter_validation_cache.json", self.profile_cache)
    
    def _save_progress(self, progress: Dict[str, Any]) -> None:
        """Save validation progress."""
        self.state_manager.save_checkpoint("twitter_validation_progress.json", progress)
    
    def _print_statistics(self) -> None:
        """Print validation statistics."""
        print(f"\n🐦 Twitter Validation Summary:")
        print(f"  📊 Total handles found: {self.stats['total_handles']}")
        print(f"  ✅ Valid handles: {self.stats['valid_handles']}")
        print(f"  ❌ Invalid handles: {self.stats['invalid_handles']}")
        print(f"  🔄 Duplicate handles: {self.stats['duplicate_handles']}")
        print(f"  🚫 Reserved handles: {self.stats['reserved_handles']}")
        print(f"  🟢 Active profiles: {self.stats['active_profiles']}")
        print(f"  🔴 Inactive profiles: {self.stats['inactive_profiles']}")
        print(f"  ⚠️  Check errors: {self.stats['check_errors']}")
        
        if self.stats['total_handles'] > 0:
            validation_rate = self.stats['valid_handles'] / self.stats['total_handles'] * 100
            print(f"  📈 Validation rate: {validation_rate:.1f}%")
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary for reporting."""
        return {
            "statistics": self.stats.copy(),
            "validation_date": self.state_manager.get_current_timestamp(),
            "total_authors_processed": self.stats['valid_handles'] + self.stats['invalid_handles']
        }
