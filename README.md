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

# 2) Creating the database

After setting up your environment with `uv`, you can create the databse using:

```sh
uv run -m src.app
```

# 3) Visualizing the database

To explore the database visually, you can use **SQLite Browser**. Run the following command in your terminal:
```sh
sqlitebrowser
```

Then, select **"Open Database"** (equivalent to *Ouvrir une base de données* in French) and choose `database.db` to browse its contents.