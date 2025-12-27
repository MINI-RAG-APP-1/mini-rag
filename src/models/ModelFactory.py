from enum import Enum
from typing import Type, Union
from .models.BaseDataModel import BaseDataModel
from .enums import DatabaseType


class ModelFactory:
    """
    Factory class for creating database model instances.
    Supports MongoDB and PostgreSQL database models.
    """
    
    @staticmethod
    async def create_project_model(
        db_type: Union[DatabaseType, str], 
        db_client: object
    ) -> BaseDataModel:
        """
        Create a ProjectModel instance for the specified database type.
        
        Args:
            db_type: Database type (DatabaseType enum or string 'mongodb'/'postgres')
            db_client: Database client instance (Motor client for MongoDB, SQLAlchemy session for Postgres)
            
        Returns:
            ProjectModel instance for the specified database
            
        Raises:
            ValueError: If database type is not supported
        """
        if isinstance(db_type, str):
            db_type = DatabaseType(db_type.lower())
        
        if db_type == DatabaseType.MONGODB:
            from .models.mongo import ProjectModel
            return await ProjectModel.create_instance(db_client)
        elif db_type == DatabaseType.POSTGRES:
            from .models.postgres import ProjectModel
            return await ProjectModel.create_instance(db_client)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    
    @staticmethod
    async def create_asset_model(
        db_type: Union[DatabaseType, str], 
        db_client: object
    ) -> BaseDataModel:
        """
        Create an AssetModel instance for the specified database type.
        
        Args:
            db_type: Database type (DatabaseType enum or string 'mongodb'/'postgres')
            db_client: Database client instance (Motor client for MongoDB, SQLAlchemy session for Postgres)
            
        Returns:
            AssetModel instance for the specified database
            
        Raises:
            ValueError: If database type is not supported
        """
        if isinstance(db_type, str):
            db_type = DatabaseType(db_type.lower())
        
        if db_type == DatabaseType.MONGODB:
            from .models.mongo import AssetModel
            return await AssetModel.create_instance(db_client)
        elif db_type == DatabaseType.POSTGRES:
            from .models.postgres import AssetModel
            return await AssetModel.create_instance(db_client)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    
    @staticmethod
    async def create_chunk_model(
        db_type: Union[DatabaseType, str], 
        db_client: object
    ) -> BaseDataModel:
        """
        Create a ChunkModel instance for the specified database type.
        
        Args:
            db_type: Database type (DatabaseType enum or string 'mongodb'/'postgres')
            db_client: Database client instance (Motor client for MongoDB, SQLAlchemy session for Postgres)
            
        Returns:
            ChunkModel instance for the specified database
            
        Raises:
            ValueError: If database type is not supported
        """
        if isinstance(db_type, str):
            db_type = DatabaseType(db_type.lower())
        
        if db_type == DatabaseType.MONGODB:
            from .models.mongo import ChunkModel
            return await ChunkModel.create_instance(db_client)
        elif db_type == DatabaseType.POSTGRES:
            from .models.postgres import ChunkModel
            return await ChunkModel.create_instance(db_client)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    
    @staticmethod
    async def create_all_models(
        db_type: Union[DatabaseType, str], 
        db_client: object
    ) -> dict:
        """
        Create all model instances for the specified database type.
        
        Args:
            db_type: Database type (DatabaseType enum or string 'mongodb'/'postgres')
            db_client: Database client instance
            
        Returns:
            Dictionary containing all model instances:
            {
                'project': ProjectModel instance,
                'asset': AssetModel instance,
                'chunk': ChunkModel instance
            }
            
        Raises:
            ValueError: If database type is not supported
        """
        return {
            'project': await ModelFactory.create_project_model(db_type, db_client),
            'asset': await ModelFactory.create_asset_model(db_type, db_client),
            'chunk': await ModelFactory.create_chunk_model(db_type, db_client)
        }
