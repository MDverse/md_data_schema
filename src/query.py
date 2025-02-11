import time

from sqlalchemy import func
from sqlmodel import Session, select


from .models import Dataset, DatasetOrigin
from .db import engine

import pandas as pd

"""Purpose
This script demonstrates how to query the database to extract and print
information. There currently are two functions in this script:
1. print_dataset_origin_summary: Prints a summary of the dataset origins.
2. save_dataset_origin_zenodo: Extracts and saves all datasets with origin
"zenodo" as a pandas dataframe.

We also measure the execution time of the script in order to get an idea of
how long it takes to complete a query on the database.

To launch this script, use the command uv run -m src.query
"""

start = time.perf_counter()

def print_dataset_origin_summary():
    """
    Prints a summary of the dataset origins. For each origin,
    it prints the number of datasets, the first dataset creation date,
    and the last dataset creation date.

    This is used mainly to demonstrate that the data was loaded correctly.
    The results are printed to the console and compared to the original data
    that can be found on https://mdverse.streamlit.app/
    """

    with Session(engine) as session:
        # Build a query that joins DatasetOrigin and Dataset,
        # groups by origin name, and aggregates the data.
        statement = (
            select(
                DatasetOrigin.name.label("dataset_origin"),
                func.count(Dataset.dataset_id).label("number_of_datasets"),
                func.min(Dataset.date_created).label("first_dataset"),
                func.max(Dataset.date_created).label("last_dataset")
            )
            # We join on the relationship: dataset_origin.origin_id == dataset.origin_id
            .join(Dataset, Dataset.origin_id == DatasetOrigin.origin_id)
            .group_by(DatasetOrigin.name)
        )

        results = session.exec(statement).all()

        # Print header
        header = f"{'Dataset_origin':<15}{'Number of datasets':<20}{'First_dataset':<15}{'Last_dataset':<15}"
        print(header)
        print("-" * len(header))

        # Print each origin row.
        total_count = 0
        for row in results:
            total_count += row.number_of_datasets

            first_date = row.first_dataset if row.first_dataset else "None"
            last_date = row.last_dataset if row.last_dataset else "None"
            print(f"{row.dataset_origin:<15}{row.number_of_datasets:<20}{first_date:<15}{last_date:<15}")

        # Add a totals row.
        print("-" * len(header))
        print(f"{'total':<15}{total_count:<20}{'None':<15}{'None':<15}\n")

def save_dataset_origin_zenodo():
    with Session(engine) as session:
        # Build a statement that selects Dataset records,
        # joins to DatasetOrigin on the origin_id,
        # and filters to only those with DatasetOrigin.name == "zenodo"
        statement = (
            select(Dataset)
            .join(DatasetOrigin, Dataset.origin_id == DatasetOrigin.origin_id)
            .where(DatasetOrigin.name == "zenodo")
        )
        results = session.exec(statement).all() # This returns SQLModel objects
        
        # Convert the SQLModel objects into dictionaries so that pandas can work with them.
        data = [dataset.model_dump() for dataset in results]
        df = pd.DataFrame(data)

        # Print some information about the extracted dataframe
        print(df.head(), "\n")
        print(df.dtypes, "\n")
        print(df.columns, "\n")

def main():
    print_dataset_origin_summary()
    save_dataset_origin_zenodo()

if __name__ == "__main__":
    main()

execution_time = time.perf_counter() - start
print(f"Query execution time: {execution_time:.2f} seconds")
