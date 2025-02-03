"""
Purpose: Create your main app and call SQLModel.metadata.create_all() in app.py
"""

from .db import create_db_and_tables, engine
from .models import *

def main():
    create_db_and_tables()
    # create_heroes()


if __name__ == "__main__":
    main()

# SQLModel.metadata.create_all(engine)
