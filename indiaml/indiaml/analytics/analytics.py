import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

# Import your models (adjust import path according to your project structure)
from ..models.models import Base, Paper, VenueInfo, PaperAuthor



from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class AuthorSchema(BaseModel):
    name: str
    position: int
    organization: Optional[str] = None
    country: Optional[str] = None

class ConferenceSchema(BaseModel):
    venue: str
    track: str
    year: int

class PaperSchema(BaseModel):
    id: str
    title: str
    paper_url: Optional[str] = None
    conference: ConferenceSchema
    authors: List[AuthorSchema]

class PapersResponse(BaseModel):
    papers: List[PaperSchema]

# To generate JSON Schema:
# print(PaperSchema.model_json_schema())
# print(PapersResponse.model_json_schema())



def generate_papers_json(output_path='papers_output.json'):
    # Initialize database connection
    engine = create_engine('sqlite:///venues.db')  # Update with your DB URL
    Session = sessionmaker(bind=engine)
    session = Session()

    # Query all papers with related data
    papers = session.query(Paper).options(
        joinedload(Paper.venue_info),
        joinedload(Paper.authors).joinedload(PaperAuthor.author)
    ).all()


    output_data = []
    for paper in papers:
        # Build conference information
        conference = ConferenceSchema(
            venue=paper.venue_info.conference,
            track=paper.venue_info.track,
            year=paper.venue_info.year
        )
        
        # Build authors list
        authors = [
            AuthorSchema(
                name=pa.author.full_name,
                position=pa.position,
                organization=pa.affiliation_name,
                country=pa.affiliation_country
            ) for pa in sorted(paper.authors, key=lambda x: x.position)
        ]
        
        # Create PaperSchema instance
        paper_entry = PaperSchema(
            id=paper.id,
            title=paper.title,
            paper_url="https://openreview.net"+paper.pdf_url,
            conference=conference,
            authors=authors
        )
        
        output_data.append(paper_entry.model_dump())
    
    # Validate and create f
    response = PapersResponse(papers=output_data)
    # Write to JSON file
    with open(output_path, 'w') as f:
        f.write(response.model_dump_json(indent=2))

    session.close()
    print(f"Successfully generated {len(output_data)} papers in {output_path}")





if __name__ == '__main__':
    generate_papers_json()