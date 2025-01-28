# Imports
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel, create_engine
from datetime import datetime

class Dataset(SQLModel, table=True):
    __tablename__ = "datasets"

    dataset_id: int = Field(default=None, primary_key=True)
    origin: str = Field(index=True)
    id_in_origin: str
    doi: str
    date_created: datetime # ("%Y/%m/%d") = Field(index=True) # We only want to index the year
    date_last_modified: datetime #("%Y/%m/%d")
    date_fetched: datetime #("%Y-%m-%dT%H:%M:%S")
    file_number: int
    download_number: int
    view_number: int
    license: str
    url: str
    title: str
    author_id: int = Field(foreign_key="authors.id")
    keywords: str = Field(index=True) # keywords separated by ";"
    description: str
    molecule_id: int | None = Field(default=None, foreign_key="molecules.id")


    # Relationships: files, authors, molecules
    files: list["File"] = Relationship(back_populates="datasets")
    authors: list["Author"] = Relationship(back_populates="datasets", link_table="datasets_authors")
    molecules: list["Molecule"] = Relationship(back_populates="datasets", link_table="datasets_molecules")

class File(SQLModel, table=True):
    __tablename__ = "files"

    file_id: int = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="datasets.id")
    name : str
    type : str = Field(index=True)
    size_in_bytes : int
    md5 : str
    url : str
    is_from_zip_file : bool = Field(index=True)
    from_zip_file_id: int | None = Field(default=None, foreign_key="files.id") # If the file is from a zip file, this field will be the id of the zip file


    # Relationships: datasets, files, gromacs_gro_files, gromacs_mdp_files, gromacs_xtc_files
    files: list["File"] = Relationship(back_populates="files")
    zip_files: list["File"] = Relationship(back_populates="files") 

    datasets: Dataset = Relationship(back_populates="files")
    gromacs_gro_files: list["GromacsGroFile"] = Relationship(back_populates="files")
    gromacs_mdp_files: list["GromacsMdpFile"] = Relationship(back_populates="files")
    gromacs_xtc_files: list["GromacsXtcFile"] = Relationship(back_populates="files")
    pass

class Author(SQLModel, table=True):
    __tablename__ = "authors"

    author_id: int = Field(default=None, primary_key=True)
    name: str
    orcid: int | None = Field(default=None, unique=True)


    # Relationships: datasets
    datasets: list[Dataset] = Relationship(back_populates="authors")

class Molecule(SQLModel, table=True):
    __tablename__ = "molecules"

    molecule_id: int = Field(default=None, primary_key=True)
    name: str
    formula: str
    sequence: str


    # Relationships: datasets, gromacs_gro_files, molecules_external_db
    datasets: list[Dataset] = Relationship(back_populates="molecules", link_table="datasets_molecules")
    gromacs_gro_files: list["GromacsGroFile"] = Relationship(back_populates="molecules", link_table="molecules_gro")
    molecules_external_db: list["MoleculeExternalDb"] = Relationship(back_populates="molecules")
    pass

class MoleculeExternalDb(SQLModel, table=True):
    __tablename__ = "molecules_external_db"

    molecule_external_db_id: int = Field(default=None, primary_key=True)
    molecule_id: int = Field(foreign_key="molecules.id")
    db_name: str = Field(index=True)
    id_in_db: str

    # Relationships: molecules
    molecules: Molecule = Relationship(back_populates="molecules_external_db")
    pass

################################
### Gromacs Specific Classes ###
################################

class GromacsGroFile(SQLModel, table=True):
    __tablename__ = "gromacs_gro_files"

    # File id is both the primary key but also a foreign key to the Files table
    file_id: int = Field(default=None, primary_key=True, foreign_key="files.id")
    atom_number: int
    has_protein: bool
    has_nucleic: bool
    has_lipid: bool
    has_glucid: bool
    has_water_ion: bool
    molecule_id: int = Field(foreign_key="molecules.id")

    # Relationships: files, molecules
    files: File = Relationship(back_populates="gromacs_gro_files")
    molecules: Molecule = Relationship(back_populates="gromacs_gro_files", link_table="molecules_gro")
    pass

class GromacsMdpFile(SQLModel, table=True):
    __tablename__ = "gromacs_mdp_files"

    file_id: int = Field(default=None, primary_key=True, foreign_key="files.id")
    dt: float
    nsteps: int
    temperature: float
    thermostat: str = Field(index=True)
    barostat: str = Field(index=True)
    integrator: str

    # Relationships: files
    files: File = Relationship(back_populates="gromacs_mdp_files")
    pass

class GromacsXtcFile(SQLModel, table=True):
    __tablename__ = "gromacs_xtc_files"

    file_id: int = Field(default=None, primary_key=True, foreign_key="files.id")
    atom_number: int
    frame_number: int
    
    # Relationships: files
    files: File = Relationship(back_populates="gromacs_xtc_files")
    pass

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
