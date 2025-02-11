import pandas as pd
from sqlmodel import Session, select

from .db import engine
from .models import (Author, 
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

DATASETS = datasets_data[[
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
# separated by a comma.
# We need to split the authors but keep them concatenated.
# We simply need to remove the space after the comma.
DATASETS['author'] = DATASETS['author'].str.replace(", ", ",")

# Normally we'd expect all datasets to have at least one author, but it
# seems that datasets from OSF might not have an author field.
# We need to account for that by replacing NaN with an empty string.
DATASETS["author"] = DATASETS["author"].apply(
    lambda x: x if pd.notna(x) else ""
    )

def create_datasets_authors_origins():
    # The session is used to interact with the database—querying, adding,
    # and committing changes.
    with Session(engine) as session:
        for _, row in DATASETS.iterrows():

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
                for name in row["author"].replace(";", ",").split(",")
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

FILES = files_data[[
    'dataset_origin',
    'dataset_id',
    'file_name',
    'file_size',
    'file_md5',
    'file_url',
    'from_zip_file',
    'origin_zip_file'
    ]].rename(columns={
        'dataset_id': 'dataset_id_in_origin',
        'file_name': 'name',
        'file_size': 'size_in_bytes',
        'file_md5': 'md5',
        'file_url': 'url',
        'from_zip_file': 'is_from_zip_file',
        'origin_zip_file': 'parent_zip_file_name'
        })

def create_files():

    # Create a dictionary to store files by their name (if they are zip files)
    parent_files_by_name = {}

    with Session(engine) as session:
        for _, row in FILES.iterrows():

            # --- Handle FileType (one-to-many relationship) ---
            file_type_name = row["file_type"]
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
            dataset_id = row["dataset_id"]
            dataset_origin = row["dataset_origin"]
            statement = select(Dataset).join(DatasetOrigin).where(
                Dataset.id_in_origin == dataset_id,
                DatasetOrigin.name == dataset_origin
                )
            dataset_obj = session.exec(statement).first()


            # --- Handle Recursive File (parent-child relationship) ---
            # We have a column "parent_zip_file_name". For files that are from a zip file, use this to find the parent file.
            parent_zip_file_name = row.get("parent_zip_file_name", None)
            parent_zip_file_id = None  # default is None
            if row["is_from_zip_file"]:
                # Look up parent by name. You may already have created it earlier.
                # Option 1: use the in-memory dictionary:
                if parent_zip_file_name in parent_files_by_name:
                    parent_zip_file_id = parent_files_by_name[parent_zip_file_name].file_id
                else:
                    # Option 2: query the database by file name (assuming parent's name is unique)
                    parent_statement = select(File).where(File.name == parent_zip_file_name)
                    parent_obj = session.exec(parent_statement).first()
                    if parent_obj:
                        parent_zip_file_id = parent_obj.file_id
                        # Optionally, store it in the dictionary for later use
                        parent_files_by_name[parent_zip_file_name] = parent_obj
                    else:
                        print(f"Parent file {parent_zip_file_name} not found for child {row['name']}.")



            file_obj = File(
                dataset_id=dataset_obj,
                name=row["name"],
                file_type_id=type_obj,
                size_in_bytes=row["size_in_bytes"],
                md5=row["md5"],
                url=row["url"],
                is_from_zip_file=row["is_from_zip_file"],
                #parent_zip_file_id=parent_zip_obj
            )

    pass

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

def create_simulation_files():
    pass