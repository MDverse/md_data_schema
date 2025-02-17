# MDverse database

## Setup environment

We use [uv](https://docs.astral.sh/uv/getting-started/installation/)
to manage dependencies and the project environment.

Clone the GitHub repository:

```sh
git clone git@github.com:MDverse/md_data_schema.git
cd md_data_schema
```

Sync dependencies:

```sh
uv sync
```


## Retrieve data

Download parquet files from [Zenodo](https://doi.org/10.5281/zenodo.7856523) to build the database:

```sh
uv run src/download_data.py
```

Files will be downloaded to `data/parquet_files`:

```
data
└── parquet_files
    ├── datasets.parquet
    ├── files.parquet
    ├── gromacs_gro_files.parquet
    ├── gromacs_mdp_files.parquet
    ├── gromacs_xtc_files.parquet
```

## Build the database

Create the empty database:

```sh
uv run src/create_database.py
```

Populate the tables with the data from parquet files:

```sh
uv run src/ingest_data.py
```
