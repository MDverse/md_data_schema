from typing import Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint, create_engine

# ============================================================================

"""Terminology:
Database = DB
FK = Foreign Key
PK = Primary Key
"""

""" Naming Conventions:
SQLModel uses python type hints to infer the database schema.
The following classes define the schema of the database.
Since we are using python syntax, it is important to note that:
- Class names are singular and in CamelCase.

We explicitly define the table name using the __tablename__ attribute.
This is done to ensure that the table name is in snake_case and plural form,
which is the convention in SQL databases (DBs).

Due to incompatibility issues between:
- SQLModel
- SQLAlchemy (that creates the engine for the database)
We will be writing the code without:
- using the "from __future__ import annotations" syntax
- using the "from typing import List" syntax
Therefore we will also be sure to use 'list["ClassName"]' or 'ClassName' when
defining certain relationships.
"""

# ============================================================================
# Many-to-Many (MtM) Link Tables
# ============================================================================

"""
Many to Many (MtM) relationships are represented using link tables in SQL DBs.
These tables contain FKs to the PKs of the tables that are related.

The link tables are named using the following convention:
- Class naming: Class1Class2Link
- Table naming: table1_table2_link

In the SQLModel documentation, these tables are referred to as "link tables".
However, in the context of SQL DBs, these tables are also known as:
- association table
- secondary table
- junction table
- intermediate table
- join table
- through table
- relationship table
- connection table
- cross-reference table
We will be using the term "link table" for coherence with the SQLModel doc.

Link tables/classes are always initialized at the beginning of the models.
This is necessary because, even with "from __future__ import annotations",
the class won't be recognized if "link_model = Class1Class2Link" is
used BEFORE the class is declared.
"""


class DatasetAuthorLink(SQLModel, table=True):
    """
    MtM link table between Dataset and Author
    LOGIC: A dataset can have many authors and
    an author can have published many datasets.
    """

    __tablename__ = "datasets_authors_link"

    dataset_id: Optional[int] = Field(
        default=None, foreign_key="datasets.dataset_id", primary_key=True
    )
    author_id: Optional[int] = Field(
        default=None, foreign_key="authors.author_id", primary_key=True
    )


class DatasetMoleculeLink(SQLModel, table=True):
    """
    MtM link table between Dataset and Molecule
    LOGIC: A dataset can have 0 or many molecules and if we have a molecule,
    it is definitely in a dataset.
    """

    __tablename__ = "datasets_molecules_link"

    dataset_id: Optional[int] = Field(
        default=None, foreign_key="datasets.dataset_id", primary_key=True
    )
    molecule_id: Optional[int] = Field(
        default=None, foreign_key="molecules.molecule_id", primary_key=True
    )


class MoleculeTopologyLink(SQLModel, table=True):
    """
    MtM link table between Molecule and TopologyFile
    LOGIC: A molecule is definitely in one or more topology files and,
    a topology file necessarily has one or more molecules.
    """

    __tablename__ = "molecules_topologies_link"

    molecule_id: Optional[int] = Field(
        default=None, foreign_key="molecules.molecule_id", primary_key=True
    )
    file_id: Optional[int] = Field(
        default=None, foreign_key="topology_files.file_id", primary_key=True
    )

class DatasetKeywordLink(SQLModel, table=True):
    """
    MtM link table between Dataset and Molecule
    LOGIC: A dataset can have 0 or many keywords and,
    a keyword it is definitely in a dataset or many datasets.
    """

    __tablename__ = "datasets_keywords_link"

    dataset_id: Optional[int] = Field(
        default=None, foreign_key="datasets.dataset_id", primary_key=True
    )
    keyword_id: Optional[int] = Field(
        default=None, foreign_key="keywords.keyword_id", primary_key=True
    )

class DatasetSoftwareLink(SQLModel, table=True):
    """
    MtM link table between Dataset and Software
    LOGIC: A dataset can have 0 or many software and,
    a software it is definitely in a dataset or many datasets.
    """

    __tablename__ = "datasets_softwares_link"

    dataset_id: Optional[int] = Field(
        default=None, foreign_key="datasets.dataset_id", primary_key=True
    )
    software_id: Optional[int] = Field(
        default=None, foreign_key="software.software_id", primary_key=True
    )


# ============================================================================
# Main Tables
# ============================================================================

"""
Here we define the main tables of the database schema.
By "main tables" we mean the ones that represent the main entities in the DB.

These tables are those that have the most attributes
and relationships with other tables.
"""


class Dataset(SQLModel, table=True):
    __tablename__ = "datasets"

    # Attributes/Table columns -----------------------------------------------
    dataset_id: Optional[int] = Field(default=None, primary_key=True)
    origin_id: int = Field(foreign_key="dataset_origins.origin_id")
    id_in_origin: str
    doi: Optional[str] = Field(default=None)
    date_created: str  # YYYY-MM-DD format
    date_last_modified: str  # YYYY-MM-DD format
    date_last_crawled: str  # ("%Y-%m-%dT%H:%M:%S")
    file_number: int = 0
    download_number: int = 0
    view_number: int = 0
    license: Optional[str] = Field(default=None)
    url: str
    title: str
    description: Optional[str] = None

    # Relationships: files, origins, authors, molecules, keywords, software --

    # A dataset can have many files, authors, keywords, software and molecules
    # (although it can have zero molecules)
    # A dataset can have only one origin (not a list)
    file: list["File"] = Relationship(back_populates="dataset", cascade_delete=True)
    origin: Optional["DatasetOrigin"] = Relationship(back_populates="dataset")
    author: list["Author"] = Relationship(
        back_populates="dataset", link_model=DatasetAuthorLink
    )
    molecule: Optional[list["Molecule"]] = Relationship(
        back_populates="dataset", link_model=DatasetMoleculeLink
    )
    keyword: Optional[list["Keyword"]] = Relationship(
        back_populates="dataset", link_model=DatasetKeywordLink
    )
    software: Optional[list["Software"]] = Relationship(
        back_populates="dataset", link_model=DatasetSoftwareLink
    )


class File(SQLModel, table=True):
    __tablename__ = "files"

    # Attributes/Table columns -----------------------------------------------
    file_id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="datasets.dataset_id", ondelete="CASCADE")
    name: str
    file_type_id: int = Field(foreign_key="file_types.file_type_id")
    size_in_bytes: Optional[float] = Field(default=None)
    # files that belong to a zip file don't have md5
    md5: Optional[str] = Field(default=None)
    # files that belong to a zip file don't have url
    url: Optional[str] = Field(default=None)
    is_from_zip_file: bool = Field(index=True)
    parent_zip_file_id: Optional[int] = Field(
        # notice the lowercase "f" to refer to the database table name
        foreign_key="files.file_id",
        default=None,
        nullable=True,
    )

    # Relationships: datasets, files, topology_files, parameter_files, -------
    # trajectory_files, file_types

    parent: Optional["File"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs=dict(remote_side="File.file_id"),
    )  # notice the uppercase "F" to refer to this table class
    children: list["File"] = Relationship(back_populates="parent")

    dataset: Dataset = Relationship(back_populates="file")
    topology_file: Optional["TopologyFile"] = Relationship(back_populates="file", cascade_delete=True)
    parameter_file: Optional["ParameterFile"] = Relationship(back_populates="file", cascade_delete=True)
    trajectory_file: Optional["TrajectoryFile"] = Relationship(back_populates="file", cascade_delete=True)
    file_type: "FileType" = Relationship(back_populates="file")


class Author(SQLModel, table=True):
    __tablename__ = "authors"
    __table_args__ = (UniqueConstraint("name", "orcid"),)

    # Attributes/Table columns -----------------------------------------------
    author_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    orcid: Optional[str] = Field(default=None)

    # Relationships: dataset
    dataset: list[Dataset] = Relationship(
        back_populates="author", link_model=DatasetAuthorLink
    )


class Molecule(SQLModel, table=True):
    __tablename__ = "molecules"

    # Attributes/Table columns -----------------------------------------------
    molecule_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    formula: str
    sequence: str
    molecule_type_id: Optional[int] = Field(
        foreign_key="molecule_types.molecule_type_id"
    )

    # Relationships: datasets, topology_files, -------------------------------
    # molecules_external_db, molecule_types

    dataset: list[Dataset] = Relationship(
        back_populates="molecule", link_model=DatasetMoleculeLink)
    topology_file: list["TopologyFile"] = Relationship(
        back_populates="molecule", link_model=MoleculeTopologyLink
    )
    mol_ext_db: Optional[list["MoleculeExternalDb"]] = Relationship(
        back_populates="molecule"
    )
    molecule_type: Optional["MoleculeType"] = Relationship(back_populates="molecule")


class MoleculeExternalDb(SQLModel, table=True):
    __tablename__ = "molecules_external_db"

    # Attributes/Table columns -----------------------------------------------
    mol_ext_db_id: Optional[int] = Field(default=None, primary_key=True)
    molecule_id: int = Field(foreign_key="molecules.molecule_id")
    db_name: str = Field(index=True)
    id_in_external_db: str
    database_id: Optional[int] = Field(foreign_key="databases.database_id")

    # Relationships: molecules, databases ------------------------------------

    molecule: Molecule = Relationship(back_populates="mol_ext_db")
    database: Optional["Database"] = Relationship(back_populates="mol_ext_db")


# ============================================================================
# Simulation Files Tables
# ============================================================================

"""
These tables correspond to the files that are used in molecular simulations.
The tables are named after the file types:
- Topology files
- Parameter files
- Trajectory files

These tables have a one-to-one relationship with the `Files` table.
This means that each record in these tables
corresponds to exactly one record in the `Files` table.
This is why in these tables, the `file_id` is both the PK and a FK.
"""


class TopologyFile(SQLModel, table=True):
    __tablename__ = "topology_files"

    # File id is both the PK but also a FK to the Files table
    file_id: Optional[int] = Field(
        default=None, primary_key=True, foreign_key="files.file_id", ondelete="CASCADE"
    )
    atom_number: int
    has_protein: bool
    has_nucleic: bool
    has_lipid: bool
    has_glucid: bool
    has_water_ion: bool

    # Relationships: files, molecules
    file: File = Relationship(back_populates="topology_file")
    molecule: list[Molecule] = Relationship(
        back_populates="topology_file", link_model=MoleculeTopologyLink
    )


class ParameterFile(SQLModel, table=True):
    __tablename__ = "parameter_files"

    file_id: Optional[int] = Field(
        default=None, primary_key=True, foreign_key="files.file_id", ondelete="CASCADE"
    )
    dt: Optional[float] = Field(default=None)
    nsteps: Optional[int] = Field(default=None)
    temperature: Optional[float] = Field(default=None)
    thermostat_id: Optional[int] = Field(foreign_key="thermostats.thermostat_id")
    barostat_id: Optional[int] = Field(foreign_key="barostats.barostat_id")
    integrator_id: Optional[int] = Field(foreign_key="integrators.integrator_id")

    # Relationships: files, thermostats, barostats, integrators
    file: File = Relationship(back_populates="parameter_file")
    thermostat: Optional["Thermostat"] = Relationship(back_populates="parameter_file")
    barostat: Optional["Barostat"] = Relationship(back_populates="parameter_file")
    integrator: Optional["Integrator"] = Relationship(back_populates="parameter_file")


class TrajectoryFile(SQLModel, table=True):
    __tablename__ = "trajectory_files"

    file_id: Optional[int] = Field(
        default=None, primary_key=True, foreign_key="files.file_id", ondelete="CASCADE"
    )
    atom_number: int
    frame_number: int

    # Relationships: files
    file: File = Relationship(back_populates="trajectory_file")


# ============================================================================
# "Type" Tables
# ============================================================================

"""
These tables are used to store the, what we call,
"type" of the entities in the database.

For example, the different types of files that are used in molecular
simulations, the different types of molecules, etc.

These tables have a one-to-many relationship with the main tables.
"""

class Keyword(SQLModel, table=True):
    __tablename__ = "keywords"

    # Attributes/Table columns -----------------------------------------------
    keyword_id: Optional[int] = Field(default=None, primary_key=True)
    entry: str = Field(unique=True)

    # Relationships: datasets
    dataset: list[Dataset] = Relationship(
        back_populates="keyword", link_model=DatasetKeywordLink
        )

class FileType(SQLModel, table=True):
    __tablename__ = "file_types"

    file_type_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: files
    file: list[File] = Relationship(back_populates="file_type")


class MoleculeType(SQLModel, table=True):
    __tablename__ = "molecule_types"

    molecule_type_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: molecules
    molecule: list[Molecule] = Relationship(back_populates="molecule_type")


class Database(SQLModel, table=True):
    __tablename__ = "databases"

    database_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: molecules_external_db
    mol_ext_db: list[MoleculeExternalDb] = Relationship(back_populates="database")


class DatasetOrigin(SQLModel, table=True):
    __tablename__ = "dataset_origins"

    origin_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: datasets
    dataset: list[Dataset] = Relationship(back_populates="origin")


class Software(SQLModel, table=True):
    __tablename__ = "software"
    __table_args__ = (UniqueConstraint("name", "version"),)


    software_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    version: Optional[str] = Field(default=None)

    # Relationships: files
    dataset: list[Dataset] = Relationship(
        back_populates="software", link_model=DatasetSoftwareLink
    )


class Thermostat(SQLModel, table=True):
    __tablename__ = "thermostats"

    thermostat_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: parameter_files
    parameter_file: list[ParameterFile] = Relationship(back_populates="thermostat")


class Barostat(SQLModel, table=True):
    __tablename__ = "barostats"

    barostat_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: parameter_files
    parameter_file: list[ParameterFile] = Relationship(back_populates="barostat")


class Integrator(SQLModel, table=True):
    __tablename__ = "integrators"

    integrator_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    # Relationships: parameter_files
    parameter_file: list[ParameterFile] = Relationship(back_populates="integrator")


# ============================================================================
# Engine
# ============================================================================

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
