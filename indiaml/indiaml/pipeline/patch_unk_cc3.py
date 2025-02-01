from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models.models import Base, PaperAuthor
from ..config.name2cc import affiliation_to_country as name_to_cc
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

try:
    # Query records where affiliation_country is 'UNK' and affiliation_name is not 'Unknown'
    results = (
        session.query(PaperAuthor)
        .filter(
            PaperAuthor.affiliation_country == "UNK",
            PaperAuthor.affiliation_name != "Unknown"
        )
        .all()
    )

    updated_records = []  # List to store records for CSV

    for record in results:
        name = record.affiliation_name
        country_code = name_to_cc.get(name, "UNK")  # Lookup the name-to-CC mapping

        # Update the country code if a mapping is found
        if country_code != "UNK":
            record.affiliation_country = country_code
            print(f"Updated {record.affiliation_name} to country code '{country_code}'")
        else:
            print(f"No mapping found for {record.affiliation_name}")

        # Append the updated record to the list for CSV
        updated_records.append((record.affiliation_name, record.affiliation_country))

    # Commit the updates to the database
    session.commit()

    # # Save the updated results to a CSV file
    # output_file = "updated_affiliations.csv"
    # with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
    #     csvwriter = csv.writer(csvfile)
    #     # Write header
    #     csvwriter.writerow(["Affiliation Name", "Affiliation Country"])
    #     # Write rows
    #     csvwriter.writerows(updated_records)

    # print(f"Updated results saved to {output_file}")

except Exception as e:
    session.rollback()  # Rollback in case of error
    print(f"An error occurred: {e}")

finally:
    # Close the session
    session.close()
