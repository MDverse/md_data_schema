"""
Purpose: Create your main app and call SQLModel.metadata.create_all() in app.py
"""
from sqlmodel import Session
import pandas as pd
from .db import create_db_and_tables, engine
from .models import Author, DatasetOrigin, Barostat, Thermostat, Integrator, FileType, Dataset


def create_authors():
    authors_path = "data/authors.csv"
    authors_df = pd.read_csv(authors_path).dropna(subset=["name"])

    authors = [
        Author(name=row["name"], orcid=row["orcid"])
        for _, row in authors_df.iterrows()
    ]

    with Session(engine) as session:
        session.add_all(authors)
        session.commit()


def create_dataset_origins():
    dataset_origins_path = "data/dataset_origins.csv"
    dataset_origins_df = pd.read_csv(dataset_origins_path)

    origins = [
        DatasetOrigin(name=row["name"])
        for _, row in dataset_origins_df.iterrows()
    ]

    with Session(engine) as session:
        session.add_all(origins)
        session.commit()


def create_file_types():
    file_types_path = "data/file_types.csv"
    file_types_df = pd.read_csv(file_types_path)

    file_types = [
        FileType(name=row["name"])
        for _, row in file_types_df.iterrows()
    ]

    with Session(engine) as session:
        session.add_all(file_types)
        session.commit()


def create_barostats():
    barostats_path = "data/barostats.csv"
    barostats_df = pd.read_csv(barostats_path)

    barostats = [
        Barostat(name=row["name"])
        for _, row in barostats_df.iterrows()
    ]

    with Session(engine) as session:
        session.add_all(barostats)
        session.commit()

def create_thermostats():
    thermostats_path = "data/thermostats.csv"
    thermostats_df = pd.read_csv(thermostats_path)

    thermostats = [
        Thermostat(name=row["name"])
        for _, row in thermostats_df.iterrows()
    ]

    with Session(engine) as session:
        session.add_all(thermostats)
        session.commit()

def create_integrators():
    integrators_path = "data/integrators.csv"
    integrators_df = pd.read_csv(integrators_path)

    integrators = [
        Integrator(name=row["name"])
        for _, row in integrators_df.iterrows()
    ]

    with Session(engine) as session:
        session.add_all(integrators)
        session.commit()


def create_datasets():
    datasets_path = "data/datasets.csv"
    datasets_df = pd.read_csv(datasets_path)                                                                                                                                                                                                                                                                                                                                                                                                
    
    # Fetch all dataset origins and authors from the database
    with Session(engine) as session:
        dataset_origins = {
            origin.name: origin.origin_id
            for origin in session.exec(DatasetOrigin).all()
            }
        author_ids = {
            author.name: author.author_id 
            for author in session.exec(Author).all()
            }


    datasets = [
        Dataset(
            id_in_origin=row["id_in_origin"],
            doi=row["doi"],
            date_created=row["date_created"],
            date_last_modified=row["date_last_modified"],
            date_last_crawled=row["date_last_crawled"],
            file_number=row["file_number"],
            download_number=row["download_number"],
            view_number=row["view_number"],
            license=row["license"],
            url=row["url"],
            title=row["title"],
            keywords=row["keywords"],
            description=row["description"],
            origin_id=dataset_origins.get(row["dataset_origin"]),
            author_id=author_ids.get(row["author"])
        )
        for _, row in datasets_df.iterrows()
    ]

    with Session(engine) as session:
        session.add_all(datasets)
        session.commit()
    
    pass


def main():
    create_db_and_tables()
    create_dataset_origins()
    create_authors()
    # create_datasets()

    create_barostats()
    create_thermostats()
    create_integrators()
    create_file_types()


if __name__ == "__main__":
    main()
