#!/usr/bin/env python3
"""
Rating Validation and Normalization Module

This module provides functions to validate and normalize rating values from different scales
to the expected 1-5 scale used by the database.

Based on analysis of NeurIPS data, the source uses a 1-10 scale (observed range: 2-9)
which needs to be normalized to the database's 1-5 scale.
"""

import logging
from typing import Optional, Union

def normalize_rating_1_10_to_1_5(rating: Union[int, float]) -> int:
    """
    Normalize a 1-10 scale rating to 1-5 scale using proportional mapping.
    
    Formula: new_rating = round(((old_rating - 1) * 4 / 9) + 1)
    
    Examples:
        1 -> 1, 2 -> 1, 3 -> 2, 4 -> 2, 5 -> 3, 6 -> 3, 7 -> 4, 8 -> 4, 9 -> 5, 10 -> 5
    
    Args:
        rating: Original rating on 1-10 scale
        
    Returns:
        Normalized rating on 1-5 scale
    """
    if rating <= 1:
        return 1
    elif rating >= 10:
        return 5
    else:
        # Proportional mapping: (rating-1) * 4/9 + 1
        normalized = ((rating - 1) * 4 / 9) + 1
        return max(1, min(5, round(normalized)))

def validate_and_normalize_rating(rating: Optional[Union[int, float]], 
                                paper_id: str = None, 
                                reviewer_id: str = None,
                                logger: logging.Logger = None) -> Optional[int]:
    """
    Validate and normalize rating values to 1-5 scale.
    
    Based on NeurIPS data analysis, ALL ratings are on 1-10 scale and need normalization.
    
    This function:
    1. Handles None/empty values
    2. Assumes all input ratings are on 1-10 scale (based on data analysis)
    3. Applies normalization to 1-5 scale
    4. Logs transformations for transparency
    5. Ensures final value is within 1-5 range
    
    Args:
        rating: Original rating value (assumed to be on 1-10 scale)
        paper_id: Paper ID for logging context
        reviewer_id: Reviewer ID for logging context  
        logger: Logger instance for recording transformations
        
    Returns:
        Normalized rating (1-5) or None if input was None
    """
    if rating is None:
        return None
    
    try:
        # Convert to float for processing
        original_rating = float(rating)
        
        # Based on analysis, ALL ratings in NeurIPS data are on 1-10 scale
        # So we always normalize, regardless of the value
        normalized = normalize_rating_1_10_to_1_5(original_rating)
        
        # Log the transformation if it actually changed the value
        if logger and normalized != original_rating:
            logger.info(f"Rating normalized: {original_rating} → {normalized} "
                       f"(paper: {paper_id}, reviewer: {reviewer_id})")
        
        return normalized
            
    except (ValueError, TypeError) as e:
        if logger:
            logger.error(f"Invalid rating value: {rating} → None "
                        f"(paper: {paper_id}, reviewer: {reviewer_id}, error: {e})")
        return None

def validate_confidence(confidence: Optional[Union[int, float]], 
                       paper_id: str = None, 
                       reviewer_id: str = None,
                       logger: logging.Logger = None) -> Optional[int]:
    """
    Validate confidence values (already on 1-5 scale based on analysis).
    
    Args:
        confidence: Original confidence value
        paper_id: Paper ID for logging context
        reviewer_id: Reviewer ID for logging context
        logger: Logger instance for recording any issues
        
    Returns:
        Validated confidence (1-5) or None if input was None
    """
    if confidence is None:
        return None
    
    try:
        confidence_val = float(confidence)
        
        # Confidence should already be 1-5, just validate and clamp
        if confidence_val < 1:
            if logger:
                logger.warning(f"Confidence below minimum: {confidence_val} → 1 "
                             f"(paper: {paper_id}, reviewer: {reviewer_id})")
            return 1
        elif confidence_val > 5:
            if logger:
                logger.warning(f"Confidence above maximum: {confidence_val} → 5 "
                             f"(paper: {paper_id}, reviewer: {reviewer_id})")
            return 5
        else:
            return int(round(confidence_val))
            
    except (ValueError, TypeError) as e:
        if logger:
            logger.error(f"Invalid confidence value: {confidence} → None "
                        f"(paper: {paper_id}, reviewer: {reviewer_id}, error: {e})")
        return None

def test_rating_normalization():
    """Test the rating normalization function with known values."""
    print("Testing rating normalization (1-10 → 1-5):")
    print("=" * 50)
    
    test_cases = [
        (1, 1), (2, 1), (3, 2), (4, 2), (5, 3), 
        (6, 3), (7, 4), (8, 4), (9, 5), (10, 5),
        (0, 1), (11, 5), (2.5, 2), (6.7, 4), (8.9, 5)
    ]
    
    for original, expected in test_cases:
        result = validate_and_normalize_rating(original)
        status = "✅" if result == expected else "❌"
        print(f"{status} {original} → {result} (expected: {expected})")
    
    print("\nTesting edge cases:")
    print("-" * 30)
    edge_cases = [None, "invalid", -5, 15, 3.14159]
    for case in edge_cases:
        result = validate_and_normalize_rating(case)
        print(f"Input: {case} → Output: {result}")

if __name__ == "__main__":
    test_rating_normalization()
