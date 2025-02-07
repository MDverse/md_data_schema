import time

from sqlalchemy import func
from sqlmodel import Session, select

from .db import engine
from .models import Dataset, DatasetOrigin

start_time = time.time()

def print_dataset_origin_summary():
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
        header = f"{
            'Dataset_origin':<15
            }{
                'Number of datasets':<20
                }{
                    'First_dataset':<15
                    }{
                        'Last_dataset':<15
                        }"
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
        print(f"{'total':<15}{total_count:<20}{'None':<15}{'None':<15}")

def main():
    print_dataset_origin_summary()

if __name__ == "__main__":
    main()

end_time = time.time()
execution_time = end_time - start_time
print(f"Query execution time: {execution_time:.2f} seconds")
