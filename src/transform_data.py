import pandas as pd
from datetime import datetime

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
# Main Tables
# ============================================================================

# Datasets --------------------------------------------
datasets = datasets_data[[
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
        'dataset_creation': 'dataset_created',
        'date_fetched': 'date_last_crawled',
        'dataset_url': 'url'
        }).astype({
            'dataset_origin': str,
            'id_in_origin': str,
            'doi': str,
            'date_creation': str,
            'date_last_modified': str,
            'date_last_crawled': str,
            'file_number': int,
            'download_number': int,
            'view_number': int,
            'license': str,
            'url': str,
            'author': str,
            'title': str,
            'keywords': str,
            'description': str
            })

# Change date_creation and date_last_modified to datetime.date
datasets['date_creation'] = pd.to_datetime(datasets['date_creation']).dt.date
datasets['date_last_modified'] = pd.to_datetime(datasets['date_last_modified']).dt.date
# Change date_last_crawled to datetime
datasets['date_last_crawled'] = pd.to_datetime(datasets['date_last_crawled'])

datasets.to_csv('data/datasets.csv', index=False)

# Files -----------------------------------------------
files = files_data[[
    'file_name',
    'file_size',
    'file_md5',
    'file_url',
    'from_zip_file',
    'origin_zip_file'
    ]].rename(columns={
        'file_name': 'name',
        'file_size': 'size_in_bytes',
        'file_md5': 'md5',
        'file_url': 'url',
        'from_zip_file': 'is_from_zip_file',
        'origin_zip_file': 'parent_zip_file_id'
        }).astype({
            'name': str,
            'size_in_bytes': float,
            'md5': str,
            'url': str,
            'is_from_zip_file': bool,
            'parent_zip_file_id': str
            })

# files.to_csv('data/files.csv', index=False)

# Authors ---------------------------------------------

"""
For future iterations of the project:
Currently 05/02/2025, we don'h have the ORCID information in any of the
MDverse Zenodo datasets. Thus, we add the column and inject None values.

Later on, when the orcid information is available in the parquet datasets,
it is important to change the data cleaning/sorting process for 'authors' to
ensure that we have correct ORCIDs.
"""

"""Process:
1) Retrieve the "author" column from the 'datasets_data' DataFrame
2) Rename the column to 'name' and convert the column to string
3) Add a new column 'orcid' with None values
4) Drop duplicates based on both the 'name' and 'orcid' columns.
    Use: We can have multiple people with the John Smith name
    but with different ORCID values.
5) Drop rows with missing values in the 'name' column (this column has to
    be NOT NULL in all cases)
6) Save the authors DataFrame to a CSV file
"""

authors = datasets_data[[
    'author'
    ]].rename(columns={
        'author': 'name'
        }).astype({
            'name': str
            })
authors['orcid'] = None
authors = authors.drop_duplicates(subset=['name', 'orcid'])
authors = authors.dropna(subset=["name"])

authors.to_csv('data/authors.csv', index=False)

# Molecules -------------------------------------------
molecules = pd.DataFrame(columns=[
    'name',
    'formula',
    'sequence'
    ]).astype({
        'name': str,
        'formula': str,
        'sequence': str
        })


# molecules.to_csv('data/molecules.csv', index=False)

# Molecules External DB -------------------------------
# Create the molecules_external_db dataset
molecules_external_db = pd.DataFrame(columns=[
    'id_in_external_db'
    ]).astype({
        'id_in_external_db': str
        })

# molecules_external_db.to_csv('data/molecules_external_db.csv', index=False)

# ============================================================================
# Simulation Files Tables
# ============================================================================

# Topology Files --------------------------------------

topology_files = gro_data[[
    'file_name',
    'atom_number',
    'has_protein',
    'has_nucleic',
    'has_lipid',
    'has_glucid',
    "has_water_ion"
    ]].rename(columns={
        'file_name': 'name'
        }).astype({
            'name': str,
            'atom_number': int,
            'has_protein': bool,
            'has_nucleic': bool,
            'has_lipid': bool,
            'has_glucid': bool,
            'has_water_ion': bool
            })

# topology_files.to_csv('data/topology_files.csv', index=False)

# Parameter Files -------------------------------------

parameter_files = mdp_data[[
    'file_name',
    'dt',
    'nsteps',
    'temperature'
    ]].rename(columns={
        'file_name': 'name'
        }).astype({
            'name': str,
            'dt': float,
            'nsteps': float,
            'temperature': float
            })


# parameter_files.to_csv('data/parameter_files.csv', index=False)

# Trajectory Files ------------------------------------

trajectory_files = xtc_data[[
    'file_name',
    'atom_number',
    'frame_number'
    ]].rename(columns={
        'file_name': 'name'
        }).astype({
            'name': str,
            'atom_number': int,
            'frame_number': int
            })

# trajectory_files.to_csv('data/trajectory_files.csv', index=False)



# ============================================================================
# "Type" Tables
# ============================================================================

# Dataset Origins -------------------------------------

dataset_origins = pd.DataFrame(files_data[
    'dataset_origin'
    ].unique(), columns=[
        'name'
        ])

dataset_origins = dataset_origins.drop_duplicates(subset=['name'])
dataset_origins = dataset_origins.dropna(subset=["name"])

dataset_origins.to_csv('data/dataset_origins.csv', index=False)

# molecule_types.to_csv('data/molecule_types.csv', index=False)

# File Types -----------------------------------------

file_types = pd.DataFrame(files_data[
    'file_type'
    ].unique(), columns=[
        'name'
        ])

file_types = file_types.drop_duplicates(subset=['name'])
file_types = file_types.dropna(subset=['name'])

file_types.to_csv('data/file_types.csv', index=False)

# software.to_csv('data/software.csv', index=False)

# Databases -------------------------------------------

databases = pd.DataFrame(columns=[
    'name'
    ]).astype({
        'name': str
        })

# databases.to_csv('data/databases.csv', index=False)

# Thermostats -----------------------------------------

thermostats = pd.DataFrame(mdp_data[
    'thermostat'
    ].unique(), columns=[
        'name'
        ])

thermostats = thermostats.drop_duplicates(subset=['name'])
thermostats = thermostats.dropna(subset=['name'])

thermostats.to_csv('data/thermostats.csv', index=False)

# Barostats -------------------------------------------

barostats = pd.DataFrame(mdp_data[
    'barostat'
    ].unique(), columns=[
        'name'
        ])

barostats = barostats.drop_duplicates(subset=['name'])
barostats = barostats.dropna(subset=['name'])

barostats.to_csv('data/barostats.csv', index=False)

# Integrators ----------------------------------------

integrators = pd.DataFrame(mdp_data[
    'integrator'
    ].unique(), columns=[
        'name'
        ])

integrators = integrators.drop_duplicates(subset=['name'])
integrators = integrators.dropna(subset=['name'])

integrators.to_csv('data/integrators.csv', index=False)