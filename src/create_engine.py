"""
Purpose: Create the engine object in a file db.py
"""

from sqlmodel import SQLModel, create_engine
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
                    Integrator,
                    Molecule,
                    MoleculeExternalDb,
                    MoleculeType,
                    Database,
                    DatasetAuthorLink,
                    DatasetMoleculeLink,
                    MoleculeTopologyLink)

sqlite_file_name = "database_test.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
