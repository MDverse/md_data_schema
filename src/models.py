# Imports
from __future__ import annotations
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel, create_engine
from datetime import datetime

class Dataset(SQLModel, table=True):
    __tablename__ = "dataset"

    dataset_id: Optional[int] = Field(default=None, primary_key=True)
    origin_id: int = Field(foreign_key="dataset_origin.origin_id")
    id_in_origin: str
    doi: str
    date_created: datetime # ("%Y/%m/%d") = Field(index=True) # We only want to index the year
    date_last_modified: datetime #("%Y/%m/%d")
    date_last_crawled: datetime #("%Y-%m-%dT%H:%M:%S")
    file_number: int = 0
    download_number: int = 0
    view_number: int = 0
    license: str
    url: str
    title: str
    author_id: int = Field(foreign_key="author.id")
    keywords: Optional[str] = Field(index=True) # keywords separated by ";"
    description: Optional[str] = None
    molecule_id: Optional[int] = Field(default=None, foreign_key="molecule.id")

    # Relationships: file, origin, author, molecule
    file: List[File] = Relationship(back_populates="dataset")
    origin: DatasetOrigin = Relationship(back_populates="dataset")
    author: List[Author] = Relationship(back_populates="dataset", link_table="datasets_authors") # CHECK THIS
    molecule: List[Molecule] = Relationship(back_populates="dataset", link_table="datasets_molecules") # CHECK THIS
    pass

class File(SQLModel, table=True):
    __tablename__ = "file"

    file_id: int = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="dataset.id")
    name : str
    file_type_id : int = Field(foreign_key="file_type.id")
    size_in_bytes : int
    md5 : str
    url : str
    is_from_zip_file: bool = Field(index=True)
    from_zip_file_id: Optional[int] = Field(default=None, foreign_key="file.file_id")

    # Enforce the rule at the database level
    __table_args__ = (
        "CHECK ((is_from_zip_file = 1 AND from_zip_file_id IS NOT NULL) OR (is_from_zip_file = 0 AND from_zip_file_id IS NULL))",
    )

    # Relationships: dataset, file, topology_file, parameter_file, trajectory_file, software, file_type
    files: List[File] = Relationship(back_populates="file") # CHECK THIS
    zip_files: List[File] = Relationship(back_populates="file") # CHECK THIS

    datasets: Dataset = Relationship(back_populates="file")
    topology_file: Optional[TopologyFile] = Relationship(back_populates="file")
    parameter_file: Optional[ParameterFile] = Relationship(back_populates="file")
    trajectory_file: Optional[TrajectoryFile] = Relationship(back_populates="file")
    software: Optional[Software] = Relationship(back_populates="file")
    file_type: FileType = Relationship(back_populates="file")
    pass

class Author(SQLModel, table=True):
    __tablename__ = "author"

    author_id: int = Field(default=None, primary_key=True)
    name: str
    orcid: Optional[int] = Field(default=None, unique=True)

    # Relationships: dataset
    datasets: List[Dataset] = Relationship(back_populates="author") # CHECK THIS
    pass

class Molecule(SQLModel, table=True):
    __tablename__ = "molecule"

    molecule_id: int = Field(default=None, primary_key=True)
    name: str
    formula: str
    sequence: str

    # Relationships: dataset, topology_file, molecule_external_db, molecule_type
    dataset: List[Dataset] = Relationship(back_populates="molecule", link_table="datasets_molecules") # CHECK THIS
    topolgy_file: List[TopologyFile] = Relationship(back_populates="molecule", link_table="molecules_gro") # CHECK THIS
    molecule_external_db: Optional[List[MoleculeExternalDb]] = Relationship(back_populates="molecule")
    molecule_type: Optional[MoleculeType] = Relationship(back_populates="molecule")
    pass

class MoleculeExternalDb(SQLModel, table=True):
    __tablename__ = "molecule_external_db"

    molecule_external_db_id: int = Field(default=None, primary_key=True)
    molecule_id: int = Field(foreign_key="molecule.id")
    db_name: str = Field(index=True)
    id_in_db: str

    # Relationships: molecule, database
    molecule: Molecule = Relationship(back_populates="molecule_external_db")
    database: Optional[Database] = Relationship(back_populates="molecule_external_db")

################################
### Gromacs Specific Classes ###
################################

class TopologyFile(SQLModel, table=True):
    __tablename__ = "topology_file"

    # File id is both the primary key but also a foreign key to the Files table
    file_id: int = Field(default=None, primary_key=True, foreign_key="file.id")
    atom_number: int
    has_protein: bool
    has_nucleic: bool
    has_lipid: bool
    has_glucid: bool
    has_water_ion: bool
    molecule_id: int = Field(foreign_key="molecule.id")

    # Relationships: file, molecule
    files: File = Relationship(back_populates="topology_file")
    molecules: Molecule = Relationship(back_populates="topology_file", link_table="molecules_gro") # CHECK THIS
    pass

class ParameterFile(SQLModel, table=True):
    __tablename__ = "parameter_file"

    file_id: int = Field(default=None, primary_key=True, foreign_key="file.id")
    dt: float
    nsteps: int
    temperature: float
    thermostat: str = Field(index=True)
    barostat: str = Field(index=True)
    integrator: str

    # Relationships: file, thermostat, barostat, integrator
    file: File = Relationship(back_populates="topology_file")
    thermostat: Optional[Thermostat] = Relationship(back_populates="parameter_file")
    barostat: Optional[Barostat] = Relationship(back_populates="parameter_file")
    integrator: Integrator = Relationship(back_populates="parameter_file")

class TrajectoryFile(SQLModel, table=True):
    __tablename__ = "trajectory_file"

    file_id: int = Field(default=None, primary_key=True, foreign_key="file.id")
    atom_number: int
    frame_number: int
    
    # Relationships: file
    file: File = Relationship(back_populates="trajectory_file")

######################
### "Types" Tables ###
######################

class FileType(SQLModel, table=True):
    __tablename__ = "file_type"

    file_type_id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: file
    file: List[File] = Relationship(back_populates="file")

class MoleculeType(SQLModel, table=True):
    __tablename__ = "molecule_types"

    molecule_type_id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: molecule
    molecule: List[Molecule] = Relationship(back_populates="molecule_type")

class Database(SQLModel, table=True):
    __tablename__ = "databases"

    database_id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: molecule_external_db
    molecule_external_db: List[MoleculeExternalDb] = Relationship(back_populates="database")

class DatasetOrigin(SQLModel, table=True):
    __tablename__ = "dataset_origin"

    origin_id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: dataset
    dataset: List[Dataset] = Relationship(back_populates="origin")

class Software(SQLModel, table=True):
    __tablename__ = "software"

    software_id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: file
    file: List[File] = Relationship(back_populates="software")

class Thermostat(SQLModel, table=True):
    __tablename__ = "thermostat"

    thermostat_id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: parameter_file
    parameter_files: List[ParameterFile] = Relationship(back_populates="thermostat")

class Barostat(SQLModel, table=True):
    __tablename__ = "barostat"

    barostat_id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: parameter_file
    parameter_files: List[ParameterFile] = Relationship(back_populates="barostat")

class Integrator(SQLModel, table=True):
    __tablename__ = "integrator"

    integrator_id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: parameter_file
    parameter_files: List[ParameterFile] = Relationship(back_populates="integrator")

######################################
### Many-to-Many (MtM) Link Tables ###
######################################

class DatsetAuthor(SQLModel, table=True):
    """
    MtM link table between Datasets and Authors 
    LOGIC: A dataset can have many authors and an author can have published many datasets.
    """
    __tablename__ = "datasets_authors"

    dataset_id: int = Field(foreign_key="datasets.id", primary_key=True)
    author_id: int = Field(foreign_key="authors.id", primary_key=True)


class DatasetMolecule(SQLModel, table=True):
    """
    MtM link table between Datasets and Molecules
    LOGIC: A dataset can have zero or many molecules and if we have a molecule, it is definitely in a dataset.
    """
    __tablename__ = "datasets_molecules"

    dataset_id: int = Field(foreign_key="datasets.id", primary_key=True)
    molecule_id: Optional[int] = Field(default=None, foreign_key="molecules.id", primary_key=True)


class MoleculeGro(SQLModel, table=True):
    """
    MtM link table between Molecules and GromacsGroFiles
    LOGIC: A molecule is definitely in one or more GRO files and a GRO file necessarily has one or more molecules.
    """
    __tablename__ = "molecules_gro"

    molecule_id: int = Field(foreign_key="molecules.id", primary_key=True)
    file_id: int = Field(foreign_key="files.id", primary_key=True)
