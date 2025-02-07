import pandas as pd

# from datetime import datetime, date

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

# Datasets ===================================================================
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
        'date_creation': 'date_created',
        'date_fetched': 'date_last_crawled',
        'dataset_url': 'url'
        }).astype({
            'dataset_origin': str,
            'id_in_origin': str,
            'doi': str,
            'date_created': str,
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
datasets['date_creatd'] = pd.to_datetime(
    datasets['date_created']
    ).dt.strftime(
        '%Y-%m-%d'
        )
datasets['date_last_modified'] = pd.to_datetime(
    datasets['date_last_modified']
    ).dt.strftime(
        '%Y-%m-%d'
        )
# Change date_last_crawled to datetime
datasets['date_last_crawled'] = pd.to_datetime(
    datasets['date_last_crawled']
    ).dt.strftime(
        '%Y-%m-%dT%H:%M:%S'
        )

# For datasets["author"] column, we can have multiple authors
# separated by a comma.
# We need to split the authors but keep them concatenated.
# We simply need to remove the space after the comma.
datasets['author'] = datasets['author'].str.replace(", ", ",")

datasets.to_csv('data/datasets.csv', index=False)

# Files ======================================================================
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

files.to_csv('data/files.csv', index=False)

# Topology Files =============================================================

topology_files = gro_data[[
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
        }).astype({
            'dataset_origin': str,
            'dataset_id': str,
            'name': str,
            'atom_number': int,
            'has_protein': bool,
            'has_nucleic': bool,
            'has_lipid': bool,
            'has_glucid': bool,
            'has_water_ion': bool
            })

topology_files.to_csv('data/topology_files.csv', index=False)

# Parameter Files ============================================================

parameter_files = mdp_data[[
    'dataset_origin',
    'dataset_id',
    'file_name',
    'dt',
    'nsteps',
    'temperature'
    ]].rename(columns={
        'file_name': 'name'
        }).astype({
            'dataset_origin': str,
            'dataset_id': str,
            'name': str,
            'dt': float,
            'nsteps': float,
            'temperature': float
            })


parameter_files.to_csv('data/parameter_files.csv', index=False)

# Trajectory Files ===========================================================

trajectory_files = xtc_data[[
    'dataset_origin',
    'dataset_id',
    'file_name',
    'atom_number',
    'frame_number'
    ]].rename(columns={
        'file_name': 'name'
        }).astype({
            'dataset_origin': str,
            'dataset_id': str,
            'name': str,
            'atom_number': int,
            'frame_number': int
            })

trajectory_files.to_csv('data/trajectory_files.csv', index=False)
