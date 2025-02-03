# Imports
from __future__ import annotations
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel, create_engine
from datetime import datetime

# Check constraints on attributes

""" Naming Conventions:
SQLModel uses python type hints to infer the database schema.
The following classes define the schema of the database.
Since we are using python syntax, it is important to note that Class names are singular and in CamelCase.

We explicitly define the table name using the __tablename__ attribute.
This is done to ensure that the table name is in snake_case and plural form, which is the convention in SQL databases.
"""

#=============================================================================
# Many-to-Many (MtM) Link Tables
#=============================================================================

"""
Many to Many (MtM) relationships are represented using link tables in SQL databases.
These tables contain foreign keys to the primary keys of the tables that are related.

The link tables are named using the following convention:
- Class naming: Class1Class2Link
- Table naming: table1_table2_link

In the SQLModel documentation, these tables are referred to as "link tables".
However, in the context of SQL databases, these tables are also known by other names:
- association table
- secondary table
- junction table
- intermediate table
- join table
- through table
- relationship table
- connection table
- cross-reference table
"""

class DatasetAuthorLink(SQLModel, table=True):
    """
    MtM link table between Dataset and Author
    LOGIC: A dataset can have many authors and an author can have published many datasets.
    """
    __tablename__ = "datasets_authors_link"

    dataset_id: Optional[int] = Field(default=None, foreign_key="datasets.dataset_id", primary_key=True)
    author_id: Optional[int] = Field(default=None, foreign_key="authors.author_id", primary_key=True)


class DatasetMoleculeLink(SQLModel, table=True):
    """
    MtM link table between Dataset and Molecule
    LOGIC: A dataset can have zero or many molecules and if we have a molecule, it is definitely in a dataset.
    """
    __tablename__ = "datasets_molecules_link"

    dataset_id: Optional[int] = Field(default=None, foreign_key="datasets.dataset_id", primary_key=True)
    molecule_id: Optional[int] = Field(default=None, foreign_key="molecules.molecule_id", primary_key=True)


class MoleculeTopologyLink(SQLModel, table=True):
    """
    MtM link table between Molecule and TopologyFile
    LOGIC: A molecule is definitely in one or more topology files and a topology file necessarily has one or more molecules.
    """
    __tablename__ = "molecules_topologies_link"

    molecule_id: Optional[int] = Field(default=None, foreign_key="molecules.molecule_id", primary_key=True)
    file_id: Optional[int] = Field(default=None, foreign_key="topology_files.file_id", primary_key=True)

#=============================================================================
# Main Tables
#=============================================================================

"""
Here we define the main tables of the database schema.
By "main tables" we mean the tables that represent the main entities in the database.
These tables are the ones that have the most attributes and relationships with other tables.
"""

class Dataset(SQLModel, table=True):
    __tablename__ = "datasets"

    # Attributes/Table columns -------------------------------------------------------
    dataset_id: Optional[int] = Field(default=None, primary_key=True)
    origin_id: int = Field(foreign_key="dataset_origins.origin_id")
    id_in_origin: str
    doi: str
    date_created: datetime          # YYYY-MM-DD format
    date_last_modified: datetime    # YYYY-MM-DD format
    date_last_crawled: datetime     #("%Y-%m-%dT%H:%M:%S")
    file_number: int = 0
    download_number: int = 0
    view_number: int = 0
    license: str
    url: str
    title: str
    author_id: int = Field(foreign_key="authors.author_id")
    keywords: Optional[str]         # = Field(index=True) ; keywords separated by ";"
    description: Optional[str] = None
    molecule_id: Optional[int] = Field(default=None, foreign_key="molecules.molecule_id")


    # Relationships: files, origins, authors, molecules ------------------------------

    # A dataset can have many files, authors, and molecules (although it can have zero molecules) 
    # A dataset can have only one origin (not a List)
    file: List[File] = Relationship(back_populates="dataset")
    origin: DatasetOrigin = Relationship(back_populates="dataset")
    author: List[Author] = Relationship(back_populates="dataset", link_model=DatasetAuthorLink)
    molecule: Optional[List[Molecule]] = Relationship(back_populates="dataset", link_model=DatasetMoleculeLink)




class File(SQLModel, table=True):
    __tablename__ = "files"

    # Attributes/Table columns -------------------------------------------------------
    file_id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="datasets.dataset_id")
    name : str
    file_type_id : int = Field(foreign_key="file_types.file_type_id")
    size_in_bytes : int
    md5 : str
    url : str
    is_from_zip_file: bool = Field(index=True)
    parent_zip_file_id: Optional[int] = Field(
        foreign_key='files.file_id',  # notice the lowercase "f" to refer to the database table name
        default=None,
        nullable=True)

    # Relationships: datasets, files, topology_files, parameter_files, trajectory_files, software, file_types
    parent: Optional[File] = Relationship(
        back_populates='children',
        sa_relationship_kwargs=dict(
            remote_side='File.file_id'))  # notice the uppercase "F" to refer to this table class
    children: List[File] = Relationship(back_populates='parent')

    dataset: Dataset = Relationship(back_populates="file")
    topology_file: Optional[TopologyFile] = Relationship(back_populates="file")
    parameter_file: Optional[ParameterFile] = Relationship(back_populates="file")
    trajectory_file: Optional[TrajectoryFile] = Relationship(back_populates="file")
    softwares: Optional[Software] = Relationship(back_populates="file")
    file_type: FileType = Relationship(back_populates="file")


class Author(SQLModel, table=True):
    __tablename__ = "authors"

    # Attributes/Table columns -------------------------------------------------------
    author_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    orcid: Optional[int] = Field(default=None, unique=True)

    # Relationships: dataset
    dataset: List[Dataset] = Relationship(back_populates="author", link_model=DatasetAuthorLink)


class Molecule(SQLModel, table=True):
    __tablename__ = "molecules"

    # Attributes/Table columns -------------------------------------------------------
    molecule_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    formula: str
    sequence: str

    # Relationships: datasets, topology_files, molecules_external_db, molecule_types -


    dataset: List[Dataset] = Relationship(back_populates="molecule", link_model=DatasetMoleculeLink)
    topolgy_file: List[TopologyFile] = Relationship(back_populates="molecule", link_model=MoleculeTopologyLink)
    molecule_external_db: Optional[List[MoleculeExternalDb]] = Relationship(back_populates="molecule")
    molecule_type: Optional[MoleculeType] = Relationship(back_populates="molecule")


class MoleculeExternalDb(SQLModel, table=True):
    __tablename__ = "molecules_external_db"

    # Attributes/Table columns -------------------------------------------------------
    molecule_external_db_id: Optional[int] = Field(default=None, primary_key=True)
    molecule_id: int = Field(foreign_key="molecules.molecule_id")
    db_name: str = Field(index=True)
    id_in_db: str

    # Relationships: molecules, databases --------------------------------------------


    molecule: Molecule = Relationship(back_populates="molecule_external_db")
    database: Optional[Database] = Relationship(back_populates="molecule_external_db")

#=============================================================================
# Simulation Files Tables
#=============================================================================

"""
These tables correspond to the files that are used in molecular simulations.
The tables are named after the file types that are used in molecular simulations:
- Topology files
- Parameter files
- Trajectory files

These tables have a one-to-one relationship with the `Files` table. 
This means that each record in these tables corresponds to exactly one record in the `Files` table. 
This is why in these tables, the `file_id` is both the primary key and a foreign key.
"""

class TopologyFile(SQLModel, table=True):
    __tablename__ = "topology_files"

    # File id is both the primary key but also a foreign key to the Files table
    file_id: Optional[int] = Field(default=None, primary_key=True, foreign_key="files.file_id")
    atom_number: int
    has_protein: bool
    has_nucleic: bool
    has_lipid: bool
    has_glucid: bool
    has_water_ion: bool
    molecule_id: int = Field(foreign_key="molecules.molecule_id")

    # Relationships: files, molecules
    file: File = Relationship(back_populates="topology_file")
    molecule: List[Molecule] = Relationship(back_populates="topology_file", link_model=MoleculeTopologyLink)


class ParameterFile(SQLModel, table=True):
    __tablename__ = "parameter_files"

    file_id: Optional[int] = Field(default=None, primary_key=True, foreign_key="files.file_id")
    dt: float
    nsteps: int
    temperature: float
    thermostat: str = Field(index=True)
    barostat: str = Field(index=True)
    integrator: str

    # Relationships: files, thermostats, barostats, integrators
    file: File = Relationship(back_populates="parameter_file")
    thermostat: Optional[Thermostat] = Relationship(back_populates="parameter_file")
    barostat: Optional[Barostat] = Relationship(back_populates="parameter_file")
    integrator: Integrator = Relationship(back_populates="parameter_file")


class TrajectoryFile(SQLModel, table=True):
    __tablename__ = "trajectory_files"

    file_id: Optional[int] = Field(default=None, primary_key=True, foreign_key="files.file_id")
    atom_number: int
    frame_number: int
    
    # Relationships: files
    file: File = Relationship(back_populates="trajectory_file")

#=============================================================================
# "Type" Tables
#=============================================================================

"""
These tables are used to store the different types of entities that are used in the database.
For example, the different types of files that are used in molecular simulations, the different types of molecules, etc.
These tables have a one-to-many relationship with the main tables.
"""

class FileType(SQLModel, table=True):
    __tablename__ = "file_types"

    file_type_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: files
    file: List[File] = Relationship(back_populates="file_type")


class MoleculeType(SQLModel, table=True):
    __tablename__ = "molecule_types"

    molecule_type_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: molecules
    molecule: List[Molecule] = Relationship(back_populates="molecule_type")


class Database(SQLModel, table=True):
    __tablename__ = "databases"

    database_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: molecules_external_db
    molecule_external_db: List[MoleculeExternalDb] = Relationship(back_populates="database")


class DatasetOrigin(SQLModel, table=True):
    __tablename__ = "dataset_origins"

    origin_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    id_in_origin: str

    # Relationships: datasets
    dataset: List[Dataset] = Relationship(back_populates="origin")


class Software(SQLModel, table=True):
    __tablename__ = "software"

    software_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: files
    file: List[File] = Relationship(back_populates="softwares")


class Thermostat(SQLModel, table=True):
    __tablename__ = "thermostats"

    thermostat_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: parameter_files
    parameter_file: List[ParameterFile] = Relationship(back_populates="thermostat")


class Barostat(SQLModel, table=True):
    __tablename__ = "barostats"

    barostat_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: parameter_files
    parameter_file: List[ParameterFile] = Relationship(back_populates="barostat")


class Integrator(SQLModel, table=True):
    __tablename__ = "integrators"

    integrator_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: parameter_files
    parameter_file: List[ParameterFile] = Relationship(back_populates="integrator")