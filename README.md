# MDverse database

# 1) Environment setup with UV

For this project, we will be using **UV** to create and manage our environments.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

## A) Clone the git repository

```sh
git clone git@github.com:MDverse/md_data_schema.git
cd md_data_schema
```

---

## B) Sync dependencies

Once inside the repository, sync the environment with:
```sh
uv sync
```

This will install all necessary dependencies from `pyproject.toml`.

# 2) Data retrieval

After setting up your environment with `uv`, we're going to need to retrieve data for the database (the parquet files are avaialble on [Zenodo](https://doi.org/10.5281/zenodo.7856523)). For this, you can run the following command:

```sh
uv run src/download_data.py
```
The output path has already been specified and will create the directory `data/parquet_files` with the following structure:

```
data
└── parquet_files
    ├── datasets.parquet
    ├── files.parquet
    ├── gromacs_gro_files.parquet
    ├── gromacs_mdp_files.parquet
    ├── gromacs_xtc_files.parquet
```

# 3) Creating the database

Now that we retrieved the necessary data, we need to create the database with all the different tables.
To do this, run:

```sh
uv run python src/create_database.py
```

# 4) Ingest the data

Finally, we need to ingest the data into the database. This will populate the tables with the data from the parquet data files we retrieved earlier.


To ingest the data, run the following command:
```sh
uv run python src/ingest_data.py
```

# 5) Visualizing the database

To explore the database visually, you can use **SQLite Browser**. Run the following command in your terminal:
```sh
sqlitebrowser
```

Then, select **"Open Database"** (equivalent to *Ouvrir une base de données* in French) and choose `database.db` to browse its contents.