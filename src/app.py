"""
Purpose: Create your main app and call SQLModel.metadata.create_all() in app.py
"""
from sqlmodel import Session, select
import pandas as pd
# from datetime import datetime
from .db import create_db_and_tables, engine
from .models import Author, DatasetOrigin, Dataset
import time 

start_time = time.time() 

def create_datasets():
    datasets_path = "data/datasets.csv"
    datasets_df = pd.read_csv(datasets_path)
    # Normally we'd expect all datasets to have at least one author, but it
    # seems that datasets from OSF might not have an author field.
    # We need to account for that by replacing NaN with an empty string.
    datasets_df["author"] = datasets_df["author"].apply(lambda x: x if pd.notna(x) else "")

    # The session is used to interact with the database—querying, adding, 
    # and committing changes.
    with Session(engine) as session:
        for _, row in datasets_df.iterrows():

            # --- Handle DatasetOrigin (one-to-many relationship) ---
            origin_name = row["dataset_origin"] # Retrieves the origin name from the row.
            
            # We create a SQL statement to find the records in DatasetOrigin 
            # with the same name as in the current row. This could give us 
            # multiple rows from DasetOrigin, but we only need one (.first()).
            # origin_obj will be an instance of DatasetOrigin if the origin already exists,
            # or None if it doesn't.
            statement = select(DatasetOrigin).where(DatasetOrigin.name == origin_name)
            origin_obj = session.exec(statement).first()

            if not origin_obj:
                # Basically if the origin doesn't exist, we create a new one in
                # the DatasetOrigin table and commit the changes.
                origin_obj = DatasetOrigin(name=origin_name)
                session.add(origin_obj)
                session.commit()  # Commit so origin_obj gets its origin_id
                session.refresh(origin_obj)

            # --- Handle Author(s) (many-to-many relationship) ---
            # If there are multiple authors separated by a delimiter (like ","),
            # split and process them accordingly.
            # This also removes any leading/trailing whitespace from each name.
            author_names = [name.strip() for name in row["author"].replace(";", ",").split(",")]
            authors = [] # List will store the Author objects for the current dataset.
            for name in author_names:
                statement = select(Author).where(Author.name == name)
                author_obj = session.exec(statement).first()
                if not author_obj:
                    author_obj = Author(name=name)
                    session.add(author_obj)
                    session.commit()  # Commit to get author_obj.author_id
                    session.refresh(author_obj)
                # After we have an Author object (either retrieved from the 
                # database or newly created), we use the following command to 
                # add the Author object to our authors list (list of Author 
                # objects for the current dataset).
                authors.append(author_obj)

            # --- Create the Dataset ---
            dataset_obj = Dataset(
                id_in_origin=row["id_in_origin"],
                doi=row["doi"],
                date_created=row["date_created"],
                date_last_modified=row["date_last_modified"],
                date_last_crawled=row["date_last_crawled"],
                file_number=row["file_number"],
                download_number=row["download_number"],
                view_number=row["view_number"],
                license=row["license"],
                url=row["url"],
                title=row["title"],
                keywords=row.get("keywords"),  # use .get() if the field might be missing
                description=row.get("description"),
                origin=origin_obj,   # assign the related origin
            )

            # Assign the many-to-many relationship for authors:
            # In our Dataset model, we have defined an attribute called author
            # that represents a many-to-many relationship with the Author model.
            # When we write the following, we are assigning the list of Author
            # objects (collected in the authors list) to the dataset’s author 
            # attribute. This informs SQLModel/SQLAlchemy to create the 
            # appropriate link table entries so that the dataset is 
            # related to all these authors.
            dataset_obj.author = authors

            session.add(dataset_obj)
            session.commit()

def main():
    create_db_and_tables()
    create_datasets()

if __name__ == "__main__":
    main()

end_time = time.time()
execution_time = end_time - start_time
print(f"Script execution time: {execution_time:.2f} seconds")