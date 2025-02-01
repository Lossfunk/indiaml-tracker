import re
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from ..models.models import Base, PaperAuthor
from ..config.d2cc import domain_to_cc
import csv

# Database connection string (adjust the path if needed)
db_path = "sqlite:///venues.db"  # Replace with your actual SQLite file path

# Create a database engine
engine = create_engine(db_path)

# Create all tables (if not already created)
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Regular expression to match ccTLDs (e.g., .us, .uk, .de)
ccTLD_pattern = re.compile(r'\.([a-zA-Z]{2})$')

try:
    # Query all records where affiliation_country is 'UNK'
    results = session.query(PaperAuthor).filter(PaperAuthor.affiliation_country == "UNK").all()

    updated_records = []  # List to store records for CSV

    for record in results:
        domain = record.affiliation_domain.lower() if record.affiliation_domain else ""
        match = ccTLD_pattern.search(domain)
        if match:
            country_code = match.group(1).upper()
        else:
            # Use the predefined mapping
            # Extract the main domain (e.g., from 'sub.domain.com' to 'domain.com')
            main_domain = domain.split('.')[-2] + '.' + domain.split('.')[-1] if '.' in domain else domain
            country_code = domain_to_cc.get(main_domain, "UNK")
        
        # Update the country code if known
        if country_code != "UNK":
            record.affiliation_country = country_code
            print(f"Updated {record.affiliation_name} domain '{record.affiliation_domain}' to country code '{country_code}'")
        else:
            print(f"No mapping found for {record.affiliation_name} with domain '{record.affiliation_domain}'")
        
        # Append the updated record to the list
        updated_records.append((record.affiliation_name, record.affiliation_domain, country_code))
    
    # Commit the updates to the database
    session.commit()

    # Save the updated results to a CSV file
    output_file = "updated_affiliations.csv"
    with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Write header
        csvwriter.writerow(["Affiliation Name", "Affiliation Domain", "Affiliation Country"])
        # Write rows
        csvwriter.writerows(updated_records)

    print(f"Updated results saved to {output_file}")

except Exception as e:
    session.rollback()  # Rollback in case of error
    print(f"An error occurred: {e}")

finally:
    # Close the session
    session.close()
