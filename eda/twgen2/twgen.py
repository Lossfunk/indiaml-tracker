from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func, distinct, desc
from collections import defaultdict
import json
from indiaml.models.models import Author, Paper, PaperAuthor, VenueInfo

# Assuming your models are imported
# from your_models import VenueInfo, Paper, Author, PaperAuthor, Base

# Define Conference Priority
CONFERENCE_PRIORITY = {
    "NEURIPS": 3,
    "ICML": 2,
    "ICLR": 1,
    # Add other conferences with priority 0 or lower if needed
}

# Define Venue Priority for sorting papers within a conference group
VENUE_PRIORITY = {
    "oral": 3,
    "spotlight": 2,
    "poster": 1,
    "unknown": 0,  # Default priority for unspecified or other venues
}

def get_indian_authorship_priority(paper, session, indian_authors_count, total_authors_count):
    """
    Determine Indian authorship priority for sorting
    Returns: 3 for top author from India, 2 for majority authors from India, 1 for others
    """
    # Get the first author (position 0 or 1)
    first_author_query = session.query(PaperAuthor).filter(
        PaperAuthor.paper_id == paper.id,
        PaperAuthor.position <= 1
    ).first()
    
    top_author_from_india = (
        first_author_query and 
        first_author_query.affiliation_country == 'IN'
    )
    
    majority_authors_from_india = (
        indian_authors_count > (total_authors_count / 2)
    )
    
    if top_author_from_india:
        return 3
    elif majority_authors_from_india:
        return 2
    else:
        return 1

def get_conference_priority(conference_name):
    """Get conference priority, defaulting to 0"""
    return CONFERENCE_PRIORITY.get(conference_name.upper() if conference_name else '', 0)

def get_venue_priority(venue_name):
    """Get venue priority, defaulting to 0"""
    return VENUE_PRIORITY.get(venue_name.lower() if venue_name else '', 0)

def sort_papers_by_priority(papers, session, focus_country='IN'):
    """
    Sort papers using the same logic as the React component:
    1. Indian authorship priority (highest first)
    2. Year (newest first) 
    3. Conference priority (highest first)
    4. Venue priority (highest first)
    5. Paper title (alphabetical)
    """
    
    def get_sorting_key(paper):
        # Calculate author counts for this paper
        all_authors = session.query(PaperAuthor).filter(
            PaperAuthor.paper_id == paper.id
        ).all()
        
        total_authors_count = len(all_authors)
        indian_authors_count = len([
            author for author in all_authors 
            if author.affiliation_country == focus_country
        ])
        
        # Calculate priorities
        authorship_priority = get_indian_authorship_priority(
            paper, session, indian_authors_count, total_authors_count
        )
        
        # Get venue info to determine year and conference if not set
        year = getattr(paper, 'year', 2025)  # Default to 2025 if not set
        conference = getattr(paper, 'conference', 'ICML')  # Default to ICML if not set
        
        conference_priority = get_conference_priority(conference)
        venue_priority = get_venue_priority(paper.accept_type)
        
        return (
            -authorship_priority,  # Negative for descending order (higher priority first)
            -year,                 # Negative for descending order (newer first)
            -conference_priority,  # Negative for descending order (higher priority first)
            -venue_priority,       # Negative for descending order (higher priority first)
            paper.title.lower()    # Alphabetical order
        )
    
    return sorted(papers, key=get_sorting_key)

def generate_icml_india_thread(database_url, focus_country='IN'):
    """
    Generate a tweet thread about India's participation in ICML 2025
    Based on the dashboard format showing: Accepted Papers, Spotlights, Authors, Global Rank
    
    Args:
        database_url: SQLAlchemy database URL
        focus_country: Two-letter ISO country code (default: 'IN' for India)
    """
    
    # Database setup
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get ICML 2025 venue info
        venue_info = session.query(VenueInfo).filter(
            VenueInfo.conference == 'ICML',
            VenueInfo.year == 2025
        ).first()
        
        if not venue_info:
            return ["❌ No ICML 2025 data found in database"]
        
        # Calculate KPIs matching the dashboard
        
        # 1. ACCEPTED PAPERS - Papers with Indian authors
        indian_papers_query = session.query(Paper).join(PaperAuthor).filter(
            Paper.venue_info_id == venue_info.id,
            PaperAuthor.affiliation_country == focus_country
        ).distinct()
        
        indian_papers = indian_papers_query.all()
        accepted_papers = len(indian_papers)
        
        # Sort papers using the same logic as the React component
        sorted_indian_papers = sort_papers_by_priority(indian_papers, session, focus_country)
        
        # 2. SPOTLIGHTS - Papers with accept_type indicating spotlight/oral 
        spotlights = session.query(Paper).join(PaperAuthor).filter(
            Paper.venue_info_id == venue_info.id,
            PaperAuthor.affiliation_country == focus_country,
            Paper.accept_type.in_(['spotlight', 'oral', 'Spotlight', 'Oral'])
        ).distinct().count()
        
        # 3. AUTHORS - Unique Indian authors
        authors_count = session.query(distinct(PaperAuthor.author_id)).join(Paper).filter(
            Paper.venue_info_id == venue_info.id,
            PaperAuthor.affiliation_country == focus_country
        ).count()
        
        # 4. GLOBAL RANK - Calculate India's rank by paper count
        # Get paper counts by country
        country_paper_counts = session.query(
            PaperAuthor.affiliation_country,
            func.count(distinct(Paper.id)).label('paper_count')
        ).join(Paper).filter(
            Paper.venue_info_id == venue_info.id,
            PaperAuthor.affiliation_country.isnot(None)
        ).group_by(PaperAuthor.affiliation_country).order_by(desc('paper_count')).all()
        
        # Find India's rank
        global_rank = None
        for rank, (country, count) in enumerate(country_paper_counts, 1):
            if country == focus_country:
                global_rank = rank
                break
        
        # Get detailed breakdown for tweet
        accept_breakdown = {}
        accept_type_counts = session.query(
            Paper.accept_type,
            func.count(distinct(Paper.id)).label('count')
        ).join(PaperAuthor).filter(
            Paper.venue_info_id == venue_info.id,
            PaperAuthor.affiliation_country == focus_country,
            Paper.accept_type.isnot(None)
        ).group_by(Paper.accept_type).all()
        
        for accept_type, count in accept_type_counts:
            accept_breakdown[accept_type.lower() if accept_type else 'unknown'] = count
        
        # Calculate oral + spotlight for the main KPI
        oral_count = accept_breakdown.get('oral', 0)
        spotlight_count = accept_breakdown.get('spotlight', 0)
        poster_count = accept_breakdown.get('poster', 0)
        
        # Generate tweets
        tweets = []
        
        # First tweet: India's KPIs (matching dashboard format) with breakdown
        breakdown_text = ""
        if oral_count > 0:
            breakdown_text += f" ({oral_count} oral"
            if spotlight_count > 0:
                breakdown_text += f", {spotlight_count} spotlight)"
            else:
                breakdown_text += ")"
        elif spotlight_count > 0:
            breakdown_text += f" ({spotlight_count} spotlight)"
        
        first_tweet = f"""🇮🇳 India at #ICML2025! 

📄 ACCEPTED PAPERS: {accepted_papers}
💡 SPOTLIGHTS: {spotlights}{breakdown_text}  
👥 AUTHORS: {authors_count}
🏆 GLOBAL RANK: #{global_rank}

Thread with all papers & Indian authors below 👇

#MachineLearning #IndiaAI #Research"""
        
        tweets.append(first_tweet)
        
        # Generate paper tweets (showing ALL papers)
        for i, paper in enumerate(sorted_indian_papers, 1):
            # Get all authors for this paper (Indian and non-Indian)
            all_authors_data = session.query(PaperAuthor, Author).join(Author).filter(
                PaperAuthor.paper_id == paper.id
            ).order_by(PaperAuthor.position).all()
            
            # Format paper tweet
            paper_tweet = f"""📄 Paper {i}/{len(sorted_indian_papers)}: "{paper.title}"
"""
            
            # Add all authors with Indian flag for Indian authors
            author_lines = []
            for paper_author, author in all_authors_data:
                if paper_author.affiliation_country == focus_country:
                    author_line = f"🇮🇳 {author.full_name}"
                else:
                    author_line = f"   {author.full_name}"
                
                # Add affiliation for context
                if paper_author.affiliation_name:
                    # Abbreviate long affiliation names
                    affiliation = paper_author.affiliation_name
                    if len(affiliation) > 25:
                        affiliation = affiliation[:22] + "..."
                    author_line += f" ({affiliation})"
                
                # Add social/academic links for Indian authors
                if paper_author.affiliation_country == focus_country:
                    links = []
                    if author.linkedin:
                        links.append(f"LinkedIn: {author.linkedin}")
                    if author.google_scholar_link:
                        links.append(f"Scholar: {author.google_scholar_link}")
                    if author.homepage:
                        links.append(f"Web: {author.homepage}")
                    
                    if links:
                        # Add links on a new line with proper indentation
                        author_line += f"\n    {' | '.join(links[:2])}"  # Limit to 2 links to avoid tweet length issues
                
                author_lines.append(author_line)
            
            # Add authors (limit to avoid tweet length issues)
            if len(author_lines) <= 4:
                paper_tweet += "\n".join(author_lines)
            else:
                paper_tweet += "\n".join(author_lines[:3])
                paper_tweet += f"\n+{len(author_lines)-3} more authors"
            
            # Add paper accept type if available
            if paper.accept_type and paper.accept_type.lower() in ['spotlight', 'oral']:
                paper_tweet += f"\n\n⭐ {paper.accept_type.upper()}"
            elif paper.accept_type and paper.accept_type.lower() == 'poster':
                paper_tweet += f"\n\n📋 POSTER"
            
            # Add paper link if available
            if paper.pdf_url:
                # Prepend OpenReview URL if not already present
                if paper.pdf_url.startswith('http'):
                    paper_url = paper.pdf_url
                else:
                    paper_url = f"https://openreview.net{paper.pdf_url}"
                paper_tweet += f"\n\n📖 {paper_url}"
            
            tweets.append(paper_tweet)
        
        # Final summary tweet highlighting achievements
        final_tweet = f"""🎯 Complete list of India's papers at #ICML2025:

✨ {accepted_papers} total papers with Indian authors
⭐ {oral_count} oral presentations  
⭐ {spotlight_count} spotlight presentations
📋 {poster_count} poster presentations
🌟 {authors_count} researchers contributing
🏆 Ranked #{global_rank} globally

Growing stronger in AI research! 🚀

#IndiaAI #MachineLearning #ICML2025"""
        
        tweets.append(final_tweet)
        
        return tweets
        
    except Exception as e:
        return [f"❌ Error generating thread: {str(e)}"]
    
    finally:
        session.close()

def get_author_links(author):
    """
    Format author links for tweets
    """
    links = []
    if author.openreview_id:
        links.append(f"OR: {author.openreview_id}")
    if author.google_scholar_link:
        # Extract short identifier from Google Scholar link
        links.append("GS: [profile]")
    if author.linkedin:
        links.append("LI: [profile]")
    if author.homepage:
        links.append("Web: [link]")
    
    return " | ".join(links[:2])  # Limit to 2 links for space

def print_tweet_thread(tweets):
    """
    Print the tweet thread in a readable format matching the dashboard style
    """
    print("=" * 60)
    print("🇮🇳 ICML 2025 INDIA TWEET THREAD")
    print("=" * 60)
    
    for i, tweet in enumerate(tweets, 1):
        print(f"\n📱 TWEET {i}:")
        print("-" * 40)
        print(tweet)
        print(f"\nCharacter count: {len(tweet)}")
        if len(tweet) > 280:
            print("⚠️  WARNING: Tweet exceeds 280 characters!")
        print("-" * 40)

def save_tweets_to_file(tweets, filename="icml_india_tweets.txt"):
    """
    Save tweets to a text file
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("ICML 2025 INDIA TWEET THREAD\n")
        f.write("=" * 60 + "\n\n")
        
        for i, tweet in enumerate(tweets, 1):
            f.write(f"TWEET {i}:\n")
            f.write(tweet + "\n")
            f.write(f"Character count: {len(tweet)}\n")
            f.write("-" * 40 + "\n\n")
    
    print(f"💾 Tweets saved to {filename}")

def get_accept_type_breakdown(database_url, focus_country='IN', year=2025, conference='ICML'):
    """
    Get breakdown of papers by accept_type for a specific country
    """
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        venue_info = session.query(VenueInfo).filter(
            VenueInfo.conference == conference,
            VenueInfo.year == year
        ).first()
        
        if not venue_info:
            return {}
        
        accept_type_counts = session.query(
            Paper.accept_type,
            func.count(distinct(Paper.id)).label('count')
        ).join(PaperAuthor).filter(
            Paper.venue_info_id == venue_info.id,
            PaperAuthor.affiliation_country == focus_country,
            Paper.accept_type.isnot(None)
        ).group_by(Paper.accept_type).all()
        
        return {accept_type: count for accept_type, count in accept_type_counts}
        
    finally:
        session.close()

# Additional utility function to generate country ranking
def get_country_rankings(database_url, year=2025, conference='ICML'):
    """
    Get global country rankings for the conference
    """
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        venue_info = session.query(VenueInfo).filter(
            VenueInfo.conference == conference,
            VenueInfo.year == year
        ).first()
        
        if not venue_info:
            return []
        
        country_rankings = session.query(
            PaperAuthor.affiliation_country,
            func.count(distinct(Paper.id)).label('paper_count'),
            func.count(distinct(PaperAuthor.author_id)).label('author_count')
        ).join(Paper).filter(
            Paper.venue_info_id == venue_info.id,
            PaperAuthor.affiliation_country.isnot(None)
        ).group_by(PaperAuthor.affiliation_country).order_by(desc('paper_count')).all()
        
        return country_rankings
        
    finally:
        session.close()

def main():
    """
    Main CLI function
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate ICML 2025 India tweet thread from database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python script.py data.db
  python script.py data.db --country US
  python script.py data.db --country IN --year 2024
  python script.py data.db --rankings-only
  python script.py data.db --breakdown
  python script.py data.db --country IN --breakdown --output tweets.txt
        """
    )
    
    parser.add_argument(
        '--breakdown',
        action='store_true',
        help='Show detailed breakdown by accept type (oral/spotlight/poster)'
    )
    
    parser.add_argument(
        'database', 
        help='Path to SQLite database file'
    )
    
    parser.add_argument(
        '--country', 
        default='IN',
        help='Two-letter ISO country code (default: IN for India)'
    )
    
    parser.add_argument(
        '--year',
        type=int,
        default=2025,
        help='Conference year (default: 2025)'
    )
    
    parser.add_argument(
        '--conference',
        default='ICML',
        help='Conference name (default: ICML)'
    )
    
    parser.add_argument(
        '--output',
        help='Output file path for tweets (optional)'
    )
    
    parser.add_argument(
        '--rankings-only',
        action='store_true',
        help='Only show country rankings, do not generate tweets'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress tweet output, only save to file'
    )
    
    args = parser.parse_args()
    
    # Construct database URL
    database_url = f"sqlite:///{args.database}"
    
    try:
        if args.rankings_only:
            # Only show country rankings
            print(f"🏆 {args.conference.upper()} {args.year} COUNTRY RANKINGS:")
            print("="*60)
            rankings = get_country_rankings(database_url, args.year, args.conference)
            
            if not rankings:
                print(f"❌ No data found for {args.conference} {args.year}")
                return
            
            for rank, (country, papers, authors) in enumerate(rankings, 1):
                emoji = "🇮🇳" if country == args.country else "  "
                highlight = ">>> " if country == args.country else "    "
                print(f"{highlight}{rank:2d}. {emoji} {country}: {papers} papers, {authors} authors")
            
            return
        
        # Generate tweet thread
        print(f"🔍 Generating {args.conference} {args.year} tweet thread for {args.country}...")
        tweets = generate_icml_india_thread(database_url, args.country)
        
        if tweets and tweets[0].startswith("❌"):
            print(tweets[0])
            return
        
        # Print tweets unless quiet mode
        if not args.quiet:
            print_tweet_thread(tweets)
        
        # Save to file if specified
        if args.output:
            save_tweets_to_file(tweets, args.output)
        elif not args.quiet:
            # Default save
            filename = f"{args.conference.lower()}_{args.year}_{args.country.lower()}_tweets.txt"
            save_tweets_to_file(tweets, filename)
        
        # Show detailed breakdown if requested
        if args.breakdown:
            print(f"\n📊 {args.country} ACCEPT TYPE BREAKDOWN:")
            print("-" * 40)
            breakdown = get_accept_type_breakdown(database_url, args.country, args.year, args.conference)
            
            if breakdown:
                total_papers = sum(breakdown.values())
                for accept_type, count in breakdown.items():
                    percentage = (count / total_papers * 100) if total_papers > 0 else 0
                    emoji = "⭐" if accept_type.lower() in ['oral', 'spotlight'] else "📋"
                    print(f"{emoji} {accept_type.upper()}: {count} ({percentage:.1f}%)")
            else:
                print("No accept_type data available")
        
        # Show country rankings at the end
        if not args.quiet:
            print("\n" + "="*60)
            print(f"🏆 TOP 10 COUNTRIES AT {args.conference.upper()} {args.year}:")
            rankings = get_country_rankings(database_url, args.year, args.conference)
            for rank, (country, papers, authors) in enumerate(rankings[:10], 1):
                emoji = "🇮🇳" if country == args.country else "  "
                highlight = ">>> " if country == args.country else "    "
                print(f"{highlight}{rank:2d}. {emoji} {country}: {papers} papers, {authors} authors")
        
        print(f"\n✅ Successfully generated tweet thread for {args.country} at {args.conference} {args.year}!")
        print(f"\n📋 Paper Sorting Logic Applied:")
        print("   1. Indian authorship priority (top author > majority authors > others)")
        print("   2. Year (newest first)")
        print("   3. Conference priority (NeurIPS > ICML > ICLR > others)")
        print("   4. Venue priority (oral > spotlight > poster)")
        print("   5. Paper title (alphabetical)")
        
    except FileNotFoundError:
        print(f"❌ Error: Database file '{args.database}' not found")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# Example usage
if __name__ == "__main__":
    main()
