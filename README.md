# MDverse database

# 1) Environment setup with UV

For this project, we will be using **UV** to create and manage our environments.

### Why UV and not Conda?
1. **Speed** – UV is significantly faster than Conda for package installation and dependency resolution.
2. **Lightweight** – Unlike Conda, UV does not require a separate package manager and works efficiently with `pyproject.toml` (configuration file used to define dependencies, build system settings, and project metadata).
3. **Better Dependency Management** – UV offers improved dependency resolution and reproducibility compared to Conda.

For more details, visit the **[UV Documentation](https://astral.sh/uv/)**.

---

## A) How to install UV

### **On macOS and Linux:**
```sh
curl -LSsf https://astral.sh/uv/install.sh | sh
```

### **On Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### **Or install from PyPI:**
```sh
# Using pip
pip install uv

# Using pipx
pipx install uv
```

After installation, you can update UV with:
```sh
uv self update
```

For more installation details, check the [UV GitHub page](https://github.com/astral-sh/uv).

---

## B) Clone the Git Repository

```sh
git clone git@github.com:MDverse/md_data_schema.git
cd md_data_schema
```

---

## C) Sync Dependencies

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

### Why `uv run -m src.app` and not `python -m src.app`?

Because this is a larger project with a **Python package** and not a single Python file, we **cannot** call it just by passing a single file name like in the example below:
```sh
uv run app.py
```
Instead, we have to tell Python that we want it to execute a **module** that is part of a package:
```sh
uv run -m src.app
```
The `-m` flag tells Python to call a **module** inside a package.
This ensures Python correctly resolves dependencies and imports.

Using `uv run` instead of `python` ensures that the command runs within the **UV-managed environment**, preventing conflicts with global Python installations and ensuring dependency consistency.


# 3) Visualizing the Database

To explore the database visually, you can use **SQLite Browser**. Run the following command in your terminal:
```sh
sqlitebrowser
```

Then, select **"Open Database"** (equivalent to *Ouvrir une base de données* in French) and choose `database.db` to browse its contents.

For more details on SQLite Browser, visit: [https://sqlitebrowser.org](https://sqlitebrowser.org)