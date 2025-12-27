from enum import Enum

class DatabaseType(Enum):
    """Enum for supported database types"""
    MONGODB = "mongodb"
    POSTGRES = "postgres"
