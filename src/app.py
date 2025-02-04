"""
Purpose: Create your main app and call SQLModel.metadata.create_all() in app.py
"""
from sqlmodel import Session
import pandas as pd
from .db import create_db_and_tables, engine
from .models import Author

def create_authors():
    authors_path = "data/authors.csv"
    authors_df = pd.read_csv(authors_path)

    # Ensure `orcid` is properly converted to `None`
    # Convert all to string first
    authors_df["orcid"] = authors_df["orcid"].astype(str)
    # Replace 'nan' strings with None
    authors_df["orcid"] = authors_df["orcid"].replace("nan", None)  
    
    # Drop rows where "name" is missing
    authors_df = authors_df.dropna(subset=["name"])
    
    print(authors_df.head())  # Check first rows
    print(authors_df.dtypes)  # Verify column types

    # List comprehension syntax:
    # [expression for item in iterable]
    authors = [
        Author(name=row["name"], orcid=row["orcid"])
        for _, row in authors_df.iterrows()
    ]
    
    with Session(engine) as session:
        session.add_all(authors)
        session.commit()


def main():
    create_db_and_tables()
    create_authors()


if __name__ == "__main__":
    main()
