import sys
import time
from pathlib import Path

import pandas as pd
from loguru import logger # type: ignore
from sqlalchemy import Engine
from sqlmodel import Session, select
from tqdm import tqdm

from create_engine import engine
from models import (
    Author,
    Barostat,
    Dataset,
    DatasetOrigin,
    File,
    FileType,
    Integrator,
    Keyword,
    ParameterFile,
    Thermostat,
    TopologyFile,
    TrajectoryFile,
)

logger.remove()
# Terminal format
logger.add(sys.stderr,
           format="{time:MMMM D, YYYY - HH:mm:ss} | <lvl>{level} --- {message}</lvl>",
           level="DEBUG"
           )

# Log file format
# Log file will be erased at each run
# Remove mode="w" to keep log file between runs
logger.add(f"{Path(__file__).stem}.log", mode="w",
           format="{time:} | <lvl>{level} | {message}</lvl>",
           level="DEBUG"
           )

# logger.trace("A trace message.")
# logger.debug("A debug message.")
# logger.info("An info message.")
# logger.success("A success message.")
# logger.warning("A warning message.")
# logger.error("An error message.")
# logger.critical("A critical message.")

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
    df['keywords'] = df['keywords'].str.replace(
        ", ", ","
        ).str.replace(
            "; ", ";"
            ).str.replace(
                ",", ";"
                )

    # Normally we'd expect all datasets to have at least one author, but it
    # seems that datasets from OSF might not have an author field.
    # We need to account for that by replacing NaN with an empty string.
    df["author"] = df["author"].apply(
        lambda x: x if pd.notna(x) else ""
        )

    df["keywords"] = df["keywords"].apply(
        lambda x: x if pd.notna(x) else ""
        )

    return df

def create_datasets_tables(datasets_df: pd.DataFrame, engine: Engine): # ADD RETURN TYPES
    """
    Create or update dataset-related tables in the database.

    This function processes a DataFrame containing dataset information and
    updates the database accordingly. It handles the creation and updating
    of Dataset, Author, DatasetOrigin, and Keyword entries.

    Args:
        datasets_df (pd.DataFrame): DataFrame containing dataset information.
        engine (Engine): SQLAlchemy Engine instance to connect to the database.

    Returns:
        None

    Process:
        - Inserts new records into the Dataset, Author, DatasetOrigin,
        and Keyword tables.
        - Updates existing records if changes are detected.
        - Logs the number of records created, updated, or ignored.

    """
    total_rows = len(datasets_df)
    logger.info(
        "Starting to create datasets tables: Dataset, Author, DatasetOrigin, Keyword."
        )

    # Counters for the number of records created, updated, or ignored.
    datsets_created_count = 0
    datasets_updated_count = 0
    datasets_ignored_count = 0

    datasets_ids_new = []
    datasets_ids_unchanged = []
    datasets_ids_deleted = []

    # The session is used to interact with the database—querying, adding,
    # and committing changes.
    with Session(engine) as session:
        for _, row in tqdm(
            datasets_df.iterrows(),
            total=total_rows,
            desc="Processing rows",
            unit="row"
            ):

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


            # --- Handle Keyword(s) (many-to-many relationship) ---
            # If there are multiple keywords separated by a delimiter (";"),
            # split and process them accordingly.
            # This also removes any leading/trailing whitespace
            # from between each keyword.
            keywords = [
                keyword.strip()
                for keyword in row["keywords"].split(";")
                ]
            keyword_entries = []  # List stores Keyword objects for the current dataset.
            for keyword in keywords:
                statement = select(Keyword).where(Keyword.entry == keyword)
                keyword_obj = session.exec(statement).first()
                if not keyword_obj:
                    keyword_obj = Keyword(entry=keyword)
                    session.add(keyword_obj)
                    session.commit()
                    session.refresh(keyword_obj)
                if keyword_obj not in keyword_entries:
                    keyword_entries.append(keyword_obj)


            # --- Check if the Dataset already exists ---
            # Uniqueness is determined by (origin, id_in_origin)
            dataset_stmt = select(Dataset).where(
                (Dataset.id_in_origin == row["id_in_origin"]) &
                (Dataset.origin_id == origin_obj.origin_id)
            )
            existing_dataset = session.exec(dataset_stmt).first()

            if not existing_dataset: # If the dataset doesn't exist, create it.
            # --- Create the new Dataset entry ---
                new_dataset_obj = Dataset(
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
                new_dataset_obj.author = authors

                # Assign the many-to-many relationship for keywords:
                new_dataset_obj.keyword = keyword_entries

                session.add(new_dataset_obj)
                session.commit()
                session.refresh(new_dataset_obj)
                datsets_created_count += 1
                datasets_ids_new.append(new_dataset_obj.dataset_id)

            else: # If the dataset already exists, update it or ignore it.
                # Compare fields to decide whether to update or ignore.
                changed = False # We don't know yet if the dataset has changed info.

                # Compare simple fields
                fields_to_check = [
                    "doi",
                    "date_created",
                    "date_last_modified",
                    "date_last_crawled",
                    "file_number",
                    # "download_number",
                    # "view_number",
                    "license",
                    "url",
                    "title",
                    'description',
                ]

                for field in fields_to_check:
                    # "new_value" is the value from the current row in the DataFrame
                    # It doesn't mean that it's new, it's just the value we're
                    # comparing to the existing dataset.
                    new_value = row[field]
                    current_value = getattr(existing_dataset, field)
                    # This is equivalent to writing existing_dataset.field if we knew
                    # the field name ahead of time, but since field is a variable,
                    # getattr is used

                    if new_value != current_value: # If the field has changed
                        setattr(existing_dataset, field, new_value) # Update it
                        changed = True # Mark the dataset as changed

                # Compare keywords (as sets of keyword entries)
                # Keywords in the database
                existing_keywords = {kw.entry for kw in existing_dataset.keyword}
                # Keywords in the current row
                new_keywords = {kw.entry for kw in keyword_entries}

                if existing_keywords != new_keywords:
                    existing_dataset.keyword = keyword_entries
                    changed = True

                # Compare authors (as sets of author names)
                # Authors in the database
                existing_authors = {author.name for author in existing_dataset.author}
                # Authors in the current row
                new_authors = {author.name for author in authors}

                if existing_authors != new_authors:
                    existing_dataset.author = authors
                    changed = True


                if changed: # If changed == True, update the dataset
                    session.add(existing_dataset)
                    session.commit()
                    datasets_updated_count += 1
                    datasets_ids_deleted.append(existing_dataset.dataset_id)
                    
                    # Delete all files associated with the existing dataset
                    file_stmt = select(File).join(Dataset).where(
                        File.dataset_id == existing_dataset.dataset_id
                    )
                    files_from_existing_dataset = session.exec(file_stmt).all()
                    if not files_from_existing_dataset:
                        logger.debug(
                            f"No files found for dataset {existing_dataset.dataset_id}."
                            )
                        continue
                    else:
                        for file in files_from_existing_dataset:
                            session.delete(file)
                            total_files_deleted += 1
                        session.commit()
                else:
                    datasets_ignored_count += 1
                    datasets_ids_unchanged.append(existing_dataset.dataset_id)

    logger.success("Completed creating datasets tables.")
    logger.info(f"Entries created: {datsets_created_count}")
    logger.info(f"Entries updated: {datasets_updated_count}")
    logger.info(
        f"Entries ignored because they already exist in the database: {datasets_ignored_count}"
        )
    
    return datasets_ids_new, datasets_ids_unchanged, datasets_ids_deleted


# def create_dataset_entries(
#         dataframe_row: pd.Series,
#         session: Session,
#         keyword_entries: list[Keyword],
#         authors: list[Author],
#         origin_obj: DatasetOrigin,
#         ) -> None:
#     # --- Create the new Dataset entry ---
#     new_dataset_obj = Dataset(
#         id_in_origin=dataframe_row["id_in_origin"],
#         doi=dataframe_row["doi"],
#         date_created=dataframe_row["date_created"],
#         date_last_modified=dataframe_row["date_last_modified"],
#         date_last_crawled=dataframe_row["date_last_crawled"],
#         file_number=dataframe_row["file_number"],
#         download_number=dataframe_row["download_number"],
#         view_number=dataframe_row["view_number"],
#         license=dataframe_row["license"],
#         url=dataframe_row["url"],
#         title=dataframe_row["title"],
#         # use .get() if the field might be missing
#         keywords=dataframe_row.get("keywords"),
#         description=dataframe_row.get("description"),
#         origin=origin_obj,   # assign the related origin
#     )

#     # Assign the many-to-many relationship for authors:
#     # In our Dataset model, we have defined an attribute called author
#     # that represents a MtM relationship with the Author model.
#     # When we write the following, we are assigning the list of Author
#     # objects (collected in the authors list) to the dataset’s author
#     # attribute. This informs SQLModel/SQLAlchemy to create the
#     # appropriate link table entries so that the dataset is
#     # related to all these authors.
#     new_dataset_obj.author = authors

#     # Assign the many-to-many relationship for keywords:
#     new_dataset_obj.keyword = keyword_entries

#     session.add(new_dataset_obj)
#     session.commit()
#     session.refresh(new_dataset_obj)

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

def create_files_tables(
        files_df: pd.DataFrame,
        engine: Engine,
        datasets_ids_new: list[int],
        datasets_ids_unchanged: list[int], 
        datasets_ids_deleted: list[int],
        ) -> None:
    """Create the FileType and File records in the database.

    We need to handle the FileType, Dataset, and recursive File relationships.
    """
    total_rows = len(files_df)
    logger.info("Starting to create files tables: FileType, File, Software.")

    # Counters for the number of records created, updated, or ignored.
    files_created_count = 0
    files_updated_count = 0
    files_ignored_count = 0

    # Create a dictionary to store files by their name (if they are zip files)
    parent_files_by_name = {} # key: (dataset_id, file_name), value: File file_id

    with Session(engine) as session:
        for _, row in tqdm(
            files_df.iterrows(),
            total=total_rows,
            desc="Processing rows",
            unit="row"
            ):

            # --- Check if the File record already exists ---
            dataset_id_in_origin = row["dataset_id_in_origin"]
            dataset_origin = row["dataset_origin"]
            dataset_stmt = select(Dataset).join(DatasetOrigin).where(
                Dataset.id_in_origin == dataset_id_in_origin,
                DatasetOrigin.name == dataset_origin,
            )
            current_dataset = session.exec(dataset_stmt).first()
            if not current_dataset:
                    logger.debug(
                        f"Dataset with id_in_origin {dataset_id_in_origin}",
                        f" and origin {dataset_origin} not found."
                        )
                    continue  # Skip if not found

            # # If there's no file from this dataset, it means that the files
            # # are new or were deleted previously
            # file_stmt = select(File).where(
            #     File.dataset_id == current_dataset.dataset_id,
            # )
            # existing_file = session.exec(file_stmt).first()

            existing_file = True
            if current_dataset.dataset_id in datasets_ids_new:
                # If the dataset is new, then all files are new
                existing_file = False
            
            if current_dataset.dataset_id in datasets_ids_deleted:
                # If the dataset was deleted, then all files are new
                existing_file = False


            if not existing_file:
                # File does not exist: create a new record with everything associated

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

                # --- Handle Recursive File (parent-child relationship) ---
                # We have a column "parent_zip_file_name".
                # For files that are from a zip file, use this to find
                # the parent file file_id.
                parent_zip_file_name = row.get("parent_zip_file_name", None)
                parent_zip_file_id = None  # default is None

                # If the file is from a zip file, we need to find the parent file file_id
                if row["is_from_zip_file"] and parent_zip_file_name:
                    # Construct a key that combines the dataset id and parent's file name.
                    # Takes the dataset_id of the child file and the parent zip file_name
                    key = (current_dataset.dataset_id, parent_zip_file_name)

                    # Option 1: Check if we have already found the parent file in the cache.
                    parent_zip_file_id = parent_files_by_name.get(key, None)

                    if not parent_zip_file_id:
                        logger.debug(
                            f"Parent file with dataset id {current_dataset.dataset_id}",
                            f" and file name {parent_zip_file_name} not found in cache.")
                        logger.debug("Searching in the database...")

                        # Option 2: Query the DB using both the file name and dataset id.
                        parent_statement = (
                            select(File)
                            # Find the parent file by name
                            .where(File.name == parent_zip_file_name)
                            # Make sure it's in the same dataset_id as the child file
                            .where(File.dataset_id == current_dataset.dataset_id)
                        )
                        parent_obj = session.exec(parent_statement).first()
                        if parent_obj:
                            parent_zip_file_id = parent_obj.file_id
                            # Cache the found parent file for later use.
                            parent_files_by_name[key] = parent_obj
                        else:
                            logger.error(
                                f"Parent file '{parent_zip_file_name}' not found for child"
                                f"'{row['name']}' with dataset_id {current_dataset.dataset_id}."
                                )

                # --- Handle Software (which we have no data for currently 11/02/2025) ---
                # We can simply leave it as None (or set to a default value if needed)
                software_id = None

                new_file_obj = File(
                    name=row["name"],
                    size_in_bytes=row["size_in_bytes"],
                    md5=row["md5"],
                    url=row["url"],
                    is_from_zip_file=row["is_from_zip_file"],
                    software_id=software_id,
                    # use the integer id from the Dataset record
                    dataset_id=current_dataset.dataset_id,
                    # use the file type id from FileType record
                    file_type_id=type_obj.file_type_id,
                    parent_zip_file_id = parent_zip_file_id
                )

                session.add(new_file_obj)
                session.commit()
                session.refresh(new_file_obj) # Refresh because we need the file_id for the parent zip file
                files_created_count += 1

                # If this file is a parent file (i.e. not extracted from a zip),
                # then store it in the cache using its dataset_id and name.
                if not row["is_from_zip_file"] and type_obj.name == "zip":
                    key = (current_dataset.dataset_id, row["name"])
                    parent_files_by_name[key] = new_file_obj.file_id
                
            else:
                # File exists: we ignore it.
                files_ignored_count += 1
    
    logger.success("Completed creating files tables.")
    logger.info(f"Entries created: {files_created_count}")
    logger.info(
        f"Entries ignored because they already exist in the database: {files_ignored_count}"
        )

# ============================================================================
# TopologyFile, Parameter,File, TrajectoryFile
# Thermostat, Barostat, Integrator
# ============================================================================

def load_topology_data(parquet_path_topology: str) -> pd.DataFrame:
    """Load parquet file and return DataFrame with selected columns.

    Rename columns to match the SQLModel table columns.
    """
    topology_df = pd.read_parquet(parquet_path_topology)

    topology_df = topology_df[[
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
            'dataset_id': 'dataset_id_in_origin',
            'file_name': 'name'
            })

    return topology_df

def load_parameter_data(parquet_path_parameters: str) -> pd.DataFrame:
    """Load parquet file and return DataFrame with selected columns.

    Rename columns to match the SQLModel table columns.
    """
    parameter_df = pd.read_parquet(parquet_path_parameters)

    parameter_df = parameter_df[[
        'dataset_origin',
        'dataset_id',
        'file_name',
        'dt',
        'nsteps',
        'temperature',
        'thermostat',
        'barostat',
        'integrator'
        ]].rename(columns={
            'dataset_id': 'dataset_id_in_origin',
            'file_name': 'name'
            })

    return parameter_df

def load_trajectory_data(parquet_path_trajectory: str) -> pd.DataFrame:
    """Load parquet file and return DataFrame with selected columns.

    Rename columns to match the SQLModel table columns.
    """
    trajectory_df = pd.read_parquet(parquet_path_trajectory)

    trajectory_df = trajectory_df[[
    'dataset_origin',
    'dataset_id',
    'file_name',
    'atom_number',
    'frame_number'
    ]].rename(columns={
        'dataset_id': 'dataset_id_in_origin',
        'file_name': 'name'
        })

    return trajectory_df


def create_topology_table(topology_df: pd.DataFrame, engine: Engine) -> None:
    """Create the TopologyFile records in the database."""

    with Session(engine) as session:
        for _, row in topology_df.iterrows():

            dataset_id_in_origin = row["dataset_id_in_origin"]
            dataset_origin = row["dataset_origin"]
            statement_dataset = select(Dataset).join(DatasetOrigin).where(
                Dataset.id_in_origin == dataset_id_in_origin,
                DatasetOrigin.name == dataset_origin
                )
            dataset_obj = session.exec(statement_dataset).first()
            if not dataset_obj:
                print(
                    f"Dataset with id_in_origin {dataset_id_in_origin}"
                    f" and origin {dataset_origin} not found."
                    )
                continue  # Skip if not found
            dataset_id = dataset_obj.dataset_id

            gro_file_name = row["name"]
            statement_file = select(File).join(FileType).where(
                # Here we filter out the .gro files to go faster but when
                # we'll have more than just .gro files in the topology table,
                # we'll remove this or refine
                FileType.name == "gro",
                File.name == gro_file_name,
                File.dataset_id == dataset_id
            )
            file_obj = session.exec(statement_file).first()
            if not file_obj:
                print(
                    f"File with dataset_id {dataset_obj.dataset_id}"
                    f" and file name {gro_file_name} not found."
                    )
                continue  # Skip if not found
            file_id_in_files = file_obj.file_id


            # -- Create the TopologyFile --
            topology_obj = TopologyFile(
                file_id=file_id_in_files,
                atom_number=row["atom_number"],
                has_protein=row["has_protein"],
                has_nucleic=row["has_nucleic"],
                has_lipid=row["has_lipid"],
                has_glucid=row["has_glucid"],
                has_water_ion=row["has_water_ion"]
            )

            session.add(topology_obj)
            session.commit()

def create_parameters_table(param_df: pd.DataFrame, engine: Engine) -> None:
    """
    Create the ParameterFile records in the database.
    At the same time, create the Thermostat, Barostat, and Integrator records.
    """

    with Session(engine) as session:
        for _, row in param_df.iterrows():

            dataset_id_in_origin = row["dataset_id_in_origin"]
            dataset_origin = row["dataset_origin"]
            statement = select(Dataset).join(DatasetOrigin).where(
                Dataset.id_in_origin == dataset_id_in_origin,
                DatasetOrigin.name == dataset_origin
                )
            dataset_obj = session.exec(statement).first()
            if not dataset_obj:
                print(
                    f"Dataset with id_in_origin {dataset_id_in_origin}"
                    f" and origin {dataset_origin} not found."
                    )
                continue  # Skip if not found
            dataset_id = dataset_obj.dataset_id

            mdp_file_name = row["name"]
            statement_file = select(File).join(FileType).where(
                # Here we filter out the .mdp files to go faster but when
                # we'll have more than just .mdp files in the parameters table,
                # we'll remove this or refine
                FileType.name == "mdp",
                File.name == mdp_file_name,
                File.dataset_id == dataset_id
            )
            file_obj = session.exec(statement_file).first()
            if not file_obj:
                print(
                    f"File with dataset_id {dataset_obj.dataset_id}"
                    f" and file name {mdp_file_name} not found."
                    )
                continue  # Skip if not found
            file_id_in_files = file_obj.file_id


            # -- Handle Thermostat, Barostat, Integrator --
            # Thermostat
            thermostat = row.get("thermostat", None)
            statement_thermostat = select(Thermostat).where(
                Thermostat.name == thermostat
                )
            thermostat_obj = session.exec(statement_thermostat).first()
            if not thermostat_obj:
                thermostat_obj = Thermostat(name=thermostat)
                session.add(thermostat_obj)
                session.commit()
                session.refresh(thermostat_obj)

            # Barostat
            barostat = row.get("barostat", None)
            statement_barostat = select(Barostat).where(
                Barostat.name == barostat
                )
            barostat_obj = session.exec(statement_barostat).first()
            if not barostat_obj:
                barostat_obj = Barostat(name=barostat)
                session.add(barostat_obj)
                session.commit()
                session.refresh(barostat_obj)

            # Integrator
            integrator = row.get("integrator", None)
            statement_integrator = select(Integrator).where(
                Integrator.name == integrator
                )
            integrator_obj = session.exec(statement_integrator).first()
            if not integrator_obj:
                integrator_obj = Integrator(name=integrator)
                session.add(integrator_obj)
                session.commit()
                session.refresh(integrator_obj)


            # -- Create the ParameterFile --
            parameter_obj = ParameterFile(
                file_id=file_id_in_files,
                dt=row["dt"],
                nsteps=row["nsteps"],
                temperature=row["temperature"],
                thermostat_id=thermostat_obj.thermostat_id,
                barostat_id=barostat_obj.barostat_id,
                integrator_id=integrator_obj.integrator_id
            )

            session.add(parameter_obj)
            session.commit()

def create_trajectory_table(traj_df: pd.DataFrame, engine: Engine) -> None:
    """Create the TrajectoryFile records in the database."""

    with Session(engine) as session:
        missing_files = 0
        for index, row in traj_df.iterrows():
            xtc_file_name = row["name"]

            dataset_id_in_origin = row["dataset_id_in_origin"]
            dataset_origin = row["dataset_origin"]
            statement = select(Dataset).join(DatasetOrigin).where(
                Dataset.id_in_origin == dataset_id_in_origin,
                DatasetOrigin.name == dataset_origin
                )
            dataset_obj = session.exec(statement).first()
            if not dataset_obj:
                logger.debug(
                    f"Dataset with id_in_origin {dataset_id_in_origin}"
                    f" and origin {dataset_origin} not found.\n",
                    f"Skipping {xtc_file_name} (index: {index})..."
                    )
                missing_files += 1
                continue  # Skip if not found
            dataset_id = dataset_obj.dataset_id

            statement_file = select(File).join(FileType).where(
                # Here we filter out the .xtc files to go faster but when
                # we'll have more than just .xtc files in the trajectory table,
                # we'll remove this or refine
                FileType.name == "xtc",
                File.name == xtc_file_name,
                File.dataset_id == dataset_id
            )
            file_obj = session.exec(statement_file).first()
            if not file_obj:
                logger.debug(
                    f"File with dataset_id {dataset_obj.dataset_id}"
                    f" and file name {xtc_file_name} not found.\n",
                    f"Skipping {xtc_file_name} (index: {index})..."
                    )
                missing_files += 1
                continue  # Skip if not found
            file_id_in_files = file_obj.file_id


            # -- Create the TrajectoryFile --
            traj_obj = TrajectoryFile(
                file_id=file_id_in_files,
                atom_number=row["atom_number"],
                frame_number=row["frame_number"]
            )

            session.add(traj_obj)
            session.commit()
    logger.info("Completed creating trajectory table.")
    logger.debug(f"Number of missing files: {missing_files}")


def delete_simulation_tables():
    with Session(engine) as session:
        statement = select(TopologyFile)
        topology_files = session.exec(statement).all()
        for topology_file in topology_files:
            session.delete(topology_file)

        statement = select(ParameterFile)
        parameter_files = session.exec(statement).all()
        for parameter_file in parameter_files:
            session.delete(parameter_file)
        session.commit()

        statement = select(TrajectoryFile)
        trajectory_files = session.exec(statement).all()
        for trajectory_file in trajectory_files:
            session.delete(trajectory_file)
        session.commit()

# ============================================================================

def data_ingestion():
    start_1 = time.perf_counter()
    start_4 = time.perf_counter()

    # Load the datasets data
    datasets_df = load_datasets_data(datasets_path)
    new_datasets, unchanged_datasets, deleted_datasets = create_datasets_tables(datasets_df, engine)
    execution_time_1 = time.perf_counter() - start_1
    logger.info(f"Datasets ingestion time: {execution_time_1:.2f} seconds\n")

    start_2 = time.perf_counter()

    # Load the files data
    files_df = load_files_data(files_path)
    create_files_tables(files_df, engine, new_datasets, unchanged_datasets, deleted_datasets)
    execution_time_2 = time.perf_counter() - start_2
    print(f"Files ingestion time: {execution_time_2:.2f} seconds\n")

    # delete_simulation_tables()

    # start_3 = time.perf_counter()

    # # Create the topology, parameters, and trajectory tables
    # topology_df = load_topology_data(gro_path)
    # parameter_df = load_parameter_data(mdp_path)
    # trajectory_df = load_trajectory_data(xtc_path)

    # create_trajectory_table(trajectory_df, engine)
    # create_parameters_table(parameter_df, engine)
    # create_topology_table(topology_df, engine)

    # execution_time_3 = time.perf_counter() - start_3
    # print(f"Simulation files ingestion time: {execution_time_3:.2f} seconds\n")

    # Measure the total execution time
    execution_time_4 = time.perf_counter() - start_4
    hours, rem = divmod(execution_time_4, 3600)
    minutes, seconds = divmod(rem, 60)
    logger.info(f"Data ingestion time: {int(hours):02}:{int(minutes):02}:{seconds:05.2f}")
    logger.success("Data ingestion complete.")
    pass

if __name__ == "__main__":
    data_ingestion()
