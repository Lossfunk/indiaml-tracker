#!/usr/bin/env python3
"""
Script to add accept_type column to Paper model in SQLite database
and update it for accepted papers using the OpenReview API.

Includes rate limiting to avoid OpenReview API rate limits.
"""

import argparse
import logging
import sqlite3
import time
import random
from openreview.api import OpenReviewClient
from openreview import OpenReviewException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def add_column_if_not_exists(conn, table_name, column_name, column_type):
    """Add a column to a table in SQLite if it doesn't already exist"""
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    
    if column_name not in columns:
        logger.info(f"Adding {column_name} column to {table_name} table...")
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            conn.commit()
            logger.info(f"Column {column_name} added successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error adding column: {e}")
            raise
    else:
        logger.info(f"Column {column_name} already exists in {table_name} table.")


def safe_str_check(value, search_term):
    """Safely check if a string contains a term, handling various types."""
    if value is None:
        return False
    
    # If it's a string, do a simple lowercase check
    if isinstance(value, str):
        return search_term in value.lower()
    
    # If it's a dictionary, convert to string and check
    if isinstance(value, dict):
        # Try to extract text or value if available
        if 'value' in value:
            return safe_str_check(value['value'], search_term)
        if 'text' in value:
            return safe_str_check(value['text'], search_term)
        # Fall back to string representation
        return search_term in str(value).lower()
    
    # For other types, convert to string
    try:
        return search_term in str(value).lower()
    except:
        return False


def fetch_accept_type_from_openreview(client, paper_id, venue_id, retry_delay=2, max_retries=3):
    """
    Fetch the accept type (oral, spotlight, poster) from OpenReview
    based on the paper's notes, decisions, or tags.
    Includes retry logic with exponential backoff for rate limits.
    """
    retries = 0
    
    while retries <= max_retries:
        try:
            # Try to get the note
            paper = client.get_note(paper_id)
            
            # Add a small delay after each API call to avoid rate limits
            time.sleep(retry_delay)
            
            # First check if there's a specific decision note
            decision_invitations = [
                f"{venue_id}/Paper{paper_id.split('/')[-1]}/Decision",
                f"{venue_id}/Paper{paper_id.split('/')[-1]}/Meta_Review",
                f"{venue_id}/Paper{paper_id.split('/')[-1]}/Final_Decision"
            ]
            
            for invitation in decision_invitations:
                try:
                    decisions = client.get_notes(forum=paper_id, invitation=invitation)
                    # Add a small delay after each API call
                    time.sleep(retry_delay)
                    
                    if decisions:
                        decision_note = decisions[0]
                        decision_fields = ['decision', 'recommendation', 'final_decision', 'metareview']
                        
                        for field in decision_fields:
                            if field in decision_note.content:
                                # Use the safe string check
                                if safe_str_check(decision_note.content[field], 'oral'):
                                    return 'oral'
                                elif safe_str_check(decision_note.content[field], 'spotlight'):
                                    return 'spotlight'
                                elif safe_str_check(decision_note.content[field], 'poster'):
                                    return 'poster'
                except Exception as e:
                    logger.debug(f"Error checking invitation {invitation}: {e}")
                    # Don't retry here, just try the next invitation
                    continue
                    
            # Check the paper's content fields
            if hasattr(paper, 'content') and paper.content:
                content_fields = ['decision', 'accept_type', 'venue', 'final_decision']
                for field in content_fields:
                    if field in paper.content:
                        # Use the safe string check
                        if safe_str_check(paper.content[field], 'oral'):
                            return 'oral'
                        elif safe_str_check(paper.content[field], 'spotlight'):
                            return 'spotlight'
                        elif safe_str_check(paper.content[field], 'poster'):
                            return 'poster'
            
            # Check forum tags
            try:
                tags = client.get_tags(forum=paper_id)
                # Add a small delay after each API call
                time.sleep(retry_delay)
                
                for tag in tags:
                    tag_name = tag.tag
                    if isinstance(tag_name, str):
                        tag_name = tag_name.lower()
                        if 'oral' in tag_name:
                            return 'oral'
                        elif 'spotlight' in tag_name:
                            return 'spotlight'
                        elif 'poster' in tag_name:
                            return 'poster'
            except Exception as e:
                logger.debug(f"Error checking tags: {e}")
                pass
                
            # If we got here without returning, we couldn't find the accept type
            return None
            
        except OpenReviewException as e:
            if 'rate' in str(e).lower() and 'limit' in str(e).lower():
                retries += 1
                # Exponential backoff with jitter
                wait_time = (2 ** retries) + random.uniform(0, 1)
                logger.warning(f"Rate limit hit. Retrying in {wait_time:.2f} seconds (attempt {retries}/{max_retries})")
                time.sleep(wait_time)
            else:
                logger.error(f"OpenReview error for paper {paper_id}: {e}")
                return None
        except Exception as e:
            logger.error(f"Error fetching accept type for paper {paper_id}: {e}")
            return None
    
    logger.error(f"Max retries exceeded for paper {paper_id}")
    return None


def update_papers_accept_type(db_path, openreview_username=None, openreview_password=None, delay=2):
    """
    Update the accept_type field for all accepted papers in the SQLite database.
    Uses a delay between API calls to avoid rate limits.
    """
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add the accept_type column if it doesn't exist
        add_column_if_not_exists(conn, 'papers', 'accept_type', 'TEXT')
        
        # Create OpenReview client
        client = OpenReviewClient(baseurl='https://api2.openreview.net')
        if openreview_username and openreview_password:
            try:
                client.login(openreview_username, openreview_password)
                logger.info("Successfully logged in to OpenReview")
            except Exception as e:
                logger.warning(f"Failed to log in to OpenReview: {e}")
                logger.info("Continuing with anonymous access")
        
        # Get all accepted papers without an accept_type
        cursor.execute("""
            SELECT p.id, v.conference, v.year, v.track 
            FROM papers p
            JOIN venue_infos v ON p.venue_info_id = v.id
            WHERE p.status = 'accepted' AND (p.accept_type IS NULL OR p.accept_type = '')
        """)
        papers = cursor.fetchall()
        
        total_papers = len(papers)
        logger.info(f"Found {total_papers} accepted papers to update.")
        
        # Update each paper with a delay between API calls
        updated_count = 0
        for i, paper_data in enumerate(papers):
            paper_id, conference, year, track = paper_data
            venue_id = f"{conference}/{year}/{track}"
            
            logger.info(f"Processing paper {i+1}/{total_papers}: {paper_id}")
            
            # Get accept type from OpenReview
            accept_type = fetch_accept_type_from_openreview(client, paper_id, venue_id, retry_delay=delay)
            
            if accept_type:
                logger.info(f"  Setting accept_type to {accept_type}")
                cursor.execute(
                    "UPDATE papers SET accept_type = ? WHERE id = ?",
                    (accept_type, paper_id)
                )
                updated_count += 1
            else:
                logger.info(f"  Could not determine accept_type")
            
            # Commit after each paper to save progress
            conn.commit()
            
            # Progress update every 10 papers
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i+1}/{total_papers} papers processed ({(i+1)/total_papers*100:.1f}%)")
        
        logger.info(f"Database update completed. Updated {updated_count} out of {total_papers} papers.")
        
        # Show stats of papers by accept_type
        cursor.execute("""
            SELECT accept_type, COUNT(*) 
            FROM papers 
            WHERE status = 'accepted' AND accept_type IS NOT NULL 
            GROUP BY accept_type
        """)
        stats = cursor.fetchall()
        logger.info("Papers by accept_type:")
        for accept_type, count in stats:
            logger.info(f"  {accept_type}: {count}")
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        logger.error(f"Error updating database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def main():
    """Main function to run the script"""
    parser = argparse.ArgumentParser(description='Update accept_type for papers in SQLite database')
    parser.add_argument('--db-path', type=str, required=True, 
                        help='Path to SQLite database file')
    parser.add_argument('--openreview-username', type=str, help='OpenReview username')
    parser.add_argument('--openreview-password', type=str, help='OpenReview password')
    parser.add_argument('--delay', type=float, default=2.0,
                        help='Delay in seconds between API calls (default: 2.0)')
    parser.add_argument('--resume-from', type=str, default=None,
                        help='Resume from a specific paper ID (useful if script stopped)')
    
    args = parser.parse_args()
    
    # Update the papers with accept_type
    update_papers_accept_type(
        args.db_path,
        openreview_username=args.openreview_username,
        openreview_password=args.openreview_password,
        delay=args.delay
    )


if __name__ == '__main__':
    main()