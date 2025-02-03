"""
Purpose: Create your main app and call SQLModel.metadata.create_all() in app.py
"""

from sqlmodel import SQLModel, create_engine
from . import db

# SQLModel.metadata.create_all(engine)
