import time

from db import create_db_and_tables
# from ingest_data import create_datasets_authors_origins, create_files

"""Purpose:
This script takes care of creating the database and tables, and ingesting the data.
We measure the script execution time in order to get an idea of how long it takes
to complete the data ingestion process.

To launch this script, use the command:
uv run python src./app.py
"""

start = time.perf_counter()


def main():
    # Create the database and tables
    create_db_and_tables()

    # Ingest the data into the database
    #create_datasets_authors_origins()
    #create_files()


if __name__ == "__main__":
    main()

execution_time = time.perf_counter() - start
print(f"Script execution time: {execution_time:.2f} seconds")
