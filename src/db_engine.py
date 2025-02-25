"""
Purpose: Create the engine object in a file db.py
"""

from sqlmodel import SQLModel, create_engine

from db_models import (
    Author,  # noqa: F401
    Barostat,  # noqa: F401
    Database,  # noqa: F401
    Dataset,  # noqa: F401
    DatasetAuthorLink,  # noqa: F401
    DatasetKeywordLink,  # noqa: F401
    DatasetMoleculeLink,  # noqa: F401
    DatasetOrigin,  # noqa: F401
    File,  # noqa: F401
    FileType,  # noqa: F401
    Integrator,  # noqa: F401
    Keyword,  # noqa: F401
    Molecule,  # noqa: F401
    MoleculeExternalDb,  # noqa: F401
    MoleculeTopologyLink,  # noqa: F401
    MoleculeType,  # noqa: F401
    ParameterFile,  # noqa: F401
    Thermostat,  # noqa: F401
    TopologyFile,  # noqa: F401
    TrajectoryFile,  # noqa: F401
)

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
