import pandas as pd
import time

from sqlalchemy import Engine
from sqlmodel import Session, select

from create_engine import engine
from models import (Author, 
                    Dataset, 
                    DatasetOrigin, 
                    File, 
                    FileType,
                    TopologyFile,
                    ParameterFile,
                    TrajectoryFile,
                    Thermostat,
                    Barostat,
                    Integrator)

"""Purpose:
This script takes care of transforming the data from the parquet files
into the SQLModel objects. We will create the following functions:
- create_datasets_authors_origins
- create_files

How it works:
- We load the data from the parquet files into pandas DataFrames.
- We rename the columns to match the SQLModel table columns.
- We transform the data into the SQLModel objects.
- We create the objects in the database.

To launch this script, use the command:
uv run python src/ingest_data.py
"""

# Path to the parquet data files
mdp_path = "data/parquet_files/gromacs_mdp_files.parquet"
gro_path = "data/parquet_files/gromacs_gro_files.parquet"
xtc_path = "data/parquet_files/gromacs_xtc_files.parquet"
files_path = "data/parquet_files/files.parquet"
datasets_path = "data/parquet_files/datasets.parquet"

# Load the data
mdp_data = pd.read_parquet(mdp_path)
gro_data = pd.read_parquet(gro_path)
xtc_data = pd.read_parquet(xtc_path)
files_data = pd.read_parquet(files_path)
datasets_data = pd.read_parquet(datasets_path)

# ============================================================================
# Dataset, Author, DatasetOrigin 
# ============================================================================

def load_datasets_data(parquet_path: str) -> pd.DataFrame:
    """Load parquet file and return a DataFrame with selected columns.

    Rename columns to match the SQLModel table columns.
    """
    df = pd.read_parquet(parquet_path)
    df = df[[
        'dataset_origin',
        'dataset_id',
        'doi',
        'date_creation',
        'date_last_modified',
        'date_fetched',
        'file_number',
        'download_number',
        'view_number',
        'license',
        'dataset_url',
        'title',
        'author',
        'keywords',
        'description'
        ]].rename(columns={
            'dataset_id': 'id_in_origin',
            'date_creation': 'date_created',
            'date_fetched': 'date_last_crawled',
            'dataset_url': 'url'
            })

    # For datasets["author"] column, we can have multiple authors
    # separated by a comma or a semicolon (replace semicolon with comma).
    # We need to split the authors but keep them concatenated.
    # We simply need to remove the space after the comma.
    df['author'] = df['author'].str.replace(", ", ",").str.replace(";", ",")

    # Normally we'd expect all datasets to have at least one author, but it
    # seems that datasets from OSF might not have an author field.
    # We need to account for that by replacing NaN with an empty string.
    df["author"] = df["author"].apply(
        lambda x: x if pd.notna(x) else ""
        )
    
    return df

def create_datasets_tables(datasets_df: pd.DataFrame, engine: Engine)-> None:
    # The session is used to interact with the database—querying, adding,
    # and committing changes.
    with Session(engine) as session:
        for _, row in datasets_df.iterrows():

            # --- Handle DatasetOrigin (one-to-many relationship) ---
            origin_name = row["dataset_origin"]

            # We create a SQL statement to find the records in DatasetOrigin
            # with the same name as in the current row. This could give us
            # multiple rows from DasetOrigin, but we only need one (.first()).
            # origin_obj will be an instance of DatasetOrigin if the origin
            # already exists, or None if it doesn't.
            statement = select(DatasetOrigin).where(
                DatasetOrigin.name == origin_name
                )
            origin_obj = session.exec(statement).first()

            if not origin_obj:
                # Basically if the origin doesn't exist, we create a new one
                # in the DatasetOrigin table and commit the changes.
                origin_obj = DatasetOrigin(name=origin_name)
                session.add(origin_obj)
                session.commit()  # Commit so origin_obj gets its origin_id
                session.refresh(origin_obj)

            # --- Handle Author(s) (many-to-many relationship) ---
            # If there are multiple authors separated by a delimiter (","),
            # split and process them accordingly.
            # This also removes any leading/trailing whitespace from each name
            author_names = [
                name.strip()
                for name in row["author"].split(",")
                ]
            authors = [] # List stores Author objects for the current dataset.
            for name in author_names:
                statement = select(Author).where(Author.name == name)
                author_obj = session.exec(statement).first()
                if not author_obj:
                    author_obj = Author(name=name)
                    session.add(author_obj)
                    session.commit()  # Commit to get author_obj.author_id
                    session.refresh(author_obj)
                # After we have an Author object (either retrieved from the
                # database or newly created), we use the following command to
                # add the Author object to our authors list (list of Author
                # objects for the current dataset).
                authors.append(author_obj)

            # --- Create the Dataset ---
            dataset_obj = Dataset(
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
                # use .get() if the field might be missing
                keywords=row.get("keywords"),
                description=row.get("description"),
                origin=origin_obj,   # assign the related origin
            )

            # Assign the many-to-many relationship for authors:
            # In our Dataset model, we have defined an attribute called author
            # that represents a MtM relationship with the Author model.
            # When we write the following, we are assigning the list of Author
            # objects (collected in the authors list) to the dataset’s author
            # attribute. This informs SQLModel/SQLAlchemy to create the
            # appropriate link table entries so that the dataset is
            # related to all these authors.
            dataset_obj.author = authors

            session.add(dataset_obj)
            session.commit()

# ============================================================================
# File, FileType
# ============================================================================


def load_files_data(parquet_path: str) -> pd.DataFrame:
    """Load parquet file and return a DataFrame with selected columns.

    Rename columns to match the SQLModel table columns.
    """
    df = pd.read_parquet(parquet_path)
    df = df[[
        'dataset_origin',
        'dataset_id',
        'file_type',
        'file_name',
        'file_size',
        'file_md5',
        'file_url',
        'from_zip_file',
        'origin_zip_file'
        ]].rename(columns={
            'dataset_id': 'dataset_id_in_origin',
            'file_type': 'type',
            'file_name': 'name',
            'file_size': 'size_in_bytes',
            'file_md5': 'md5',
            'file_url': 'url',
            'from_zip_file': 'is_from_zip_file',
            'origin_zip_file': 'parent_zip_file_name'
            })
    return df


def create_files_tables(files_df: pd.DataFrame, engine: Engine) -> None:
    """Create the FileType and File records in the database.

    We need to handle the FileType, Dataset, and recursive File relationships.
    """
    # Create a dictionary to store files by their name (if they are zip files)
    parent_files_by_name = {} # key: (dataset_id, file_name), value: File file_id

    with Session(engine) as session:
        for _, row in files_df.iterrows():

            # --- Handle FileType (one-to-many relationship) ---
            file_type_name = row["type"]
            statement = select(FileType).where(
                FileType.name == file_type_name
                )
            type_obj = session.exec(statement).first()

            if not type_obj:
                type_obj = FileType(name=file_type_name)
                session.add(type_obj)
                session.commit()
                session.refresh(type_obj)


            # --- Handle Dataset (one-to-many relationship) ---
            dataset_id_in_origin = row["dataset_id_in_origin"]
            dataset_origin = row["dataset_origin"]
            statement = select(Dataset).join(DatasetOrigin).where(
                Dataset.id_in_origin == dataset_id_in_origin,
                DatasetOrigin.name == dataset_origin
                )
            dataset_obj = session.exec(statement).first()
            if not dataset_obj:
                print(f"Dataset with id_in_origin {dataset_id_in_origin} and origin {dataset_origin} not found.")
                continue  # Skip if not found


            # --- Handle Recursive File (parent-child relationship) ---
            # We have a column "parent_zip_file_name". 
            # For files that are from a zip file, use this to find 
            # the parent file file_id.
            parent_zip_file_name = row.get("parent_zip_file_name", None)
            parent_zip_file_id = None  # default is None

            # If the file is from a zip file, we need to find the parent file file_id
            if row["is_from_zip_file"] and parent_zip_file_name:
                # Construct a key that combines the dataset id and parent's file name.
                key = (dataset_obj.dataset_id, parent_zip_file_name) # Takes the dataset_id of the child file and the parent zip file_name
                
                # Option 1: Check if we have already found the parent file in the cache.
                parent_zip_file_id = parent_files_by_name.get(key, None)
                
                if not parent_zip_file_id:
                    print("Parent file not found in cache.\n Searching in the database...")
                    # Option 2: Query the database using both the file name and matching dataset id.
                    parent_statement = (
                        select(File)
                        .where(File.name == parent_zip_file_name) # Find the parent file by name
                        .where(File.dataset_id == dataset_obj.dataset_id) # Make sure it's in the same dataset_id as the current child file
                    )
                    parent_obj = session.exec(parent_statement).first()
                    if parent_obj:
                        parent_zip_file_id = parent_obj.file_id
                        # Cache the found parent file for later use.
                        parent_files_by_name[key] = parent_obj
                    else:
                        print(f"Parent file '{parent_zip_file_name}' not found for child '{row['name']}' with dataset_id {dataset_obj.dataset_id}.")

            # --- Handle Software (which we have no data for currently 11/02/2025) ---
            # We can simply leave it as None (or set to a default value if needed)
            software_id = None

            file_obj = File(
                name=row["name"],
                size_in_bytes=row["size_in_bytes"],
                md5=row["md5"],
                url=row["url"],
                is_from_zip_file=row["is_from_zip_file"],
                software_id=software_id,
                dataset_id=dataset_obj.dataset_id,  # use the actual integer id from the Dataset record
                file_type_id=type_obj.file_type_id,  # use the actual file type id from FileType record
                parent_zip_file_id = parent_zip_file_id
            )

            session.add(file_obj)
            session.commit()
            session.refresh(file_obj)

            # If this file is a parent file (i.e. not extracted from a zip),
            # then store it in the cache using its dataset_id and name.
            if not row["is_from_zip_file"] and type_obj.name == "zip":
                key = (dataset_obj.dataset_id, row["name"])
                parent_files_by_name[key] = file_obj.file_id

# ============================================================================
# TopologyFile, Parameter,File, TrajectoryFile
# Thermostat, Barostat, Integrator
# ============================================================================

TOPOLOGY_FILES = gro_data[[
    'dataset_origin',
    'dataset_id',
    'file_name',
    'atom_number',
    'has_protein',
    'has_nucleic',
    'has_lipid',
    'has_glucid',
    "has_water_ion"
    ]].rename(columns={
        'file_name': 'name'
        })

PARAMETER_FILES = mdp_data[[
    'dataset_origin',
    'dataset_id',
    'file_name',
    'dt',
    'nsteps',
    'temperature'
    ]].rename(columns={
        'file_name': 'name'
        })

TRAJECTORY_FILES = xtc_data[[
    'dataset_origin',
    'dataset_id',
    'file_name',
    'atom_number',
    'frame_number'
    ]].rename(columns={
        'file_name': 'name'
        })

def create_simulation_tables():
    pass

# ============================================================================

def data_ingestion():
    start_1 = time.perf_counter()
    start_3 = time.perf_counter()

    # Load the datasets data
    datasets_df = load_datasets_data(datasets_path)
    create_datasets_tables(datasets_df, engine)
    execution_time = time.perf_counter() - start_1
    print(f"Datasets ingestion time: {execution_time:.2f} seconds\n")

    start_2 = time.perf_counter()

    # Load the files data
    files_df = load_files_data(files_path)
    create_files_tables(files_df, engine)
    execution_time = time.perf_counter() - start_2
    print(f"Files ingestion time: {execution_time:.2f} seconds\n")


    # Create the simulation tables
    # create_simulation_tables()
    execution_time = time.perf_counter() - start_3
    print(f"Data ingestion time: {execution_time:.2f} seconds")
    print("Data ingestion complete.")

if __name__ == "__main__":
    data_ingestion()