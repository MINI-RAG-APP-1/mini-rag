from typing import Type, Dict, Union
from .VectorDBEnums import (
    DistanceMetricEnums, 
    VectorDBEnums,
    PgVectorDistanceMetricEnums,
    QdrantDistanceMetricEnums
)
from qdrant_client import models

def get_distance_metrics(vectordb_type: str) -> Dict[str, Union[Type[models.Distance], str]]:
    """
    Get distance metrics mapping for specified vector database.
    
    Args:
        vectordb_type: Type of vector database ("QDRANT" or "PGVECTOR")
        
    Returns:
        Dict mapping DistanceMetricEnums values to appropriate distance metrics
    """
    mapping = {}
    
    if vectordb_type == VectorDBEnums.QDRANT.value:
        qdrant_map = {
            DistanceMetricEnums.COSINE.value: QdrantDistanceMetricEnums.COSINE.value,
            DistanceMetricEnums.DOT.value: QdrantDistanceMetricEnums.DOT.value,
            DistanceMetricEnums.EUCLIDEAN.value: QdrantDistanceMetricEnums.EUCLID.value,
            DistanceMetricEnums.MANHATTAN.value: QdrantDistanceMetricEnums.MANHATTAN.value,
        }
        
        for enum_item in DistanceMetricEnums:
            enum_value = enum_item.value
            if enum_value in qdrant_map:
                mapping[enum_value] = qdrant_map[enum_value]

    
    elif vectordb_type == VectorDBEnums.PGVECTOR.value:
        # PgVector distance operator mappings
        pgvector_map = {
            DistanceMetricEnums.COSINE.value: PgVectorDistanceMetricEnums.COSINE.value,
            DistanceMetricEnums.DOT.value: PgVectorDistanceMetricEnums.DOT.value,
            DistanceMetricEnums.EUCLIDEAN.value: PgVectorDistanceMetricEnums.EUCLIDEAN.value,
            DistanceMetricEnums.MANHATTAN.value: PgVectorDistanceMetricEnums.MANHATTAN.value,
        }
        
        for enum_item in DistanceMetricEnums:
            enum_value = enum_item.value
            if enum_value in pgvector_map:
                mapping[enum_value] = pgvector_map[enum_value]
        
    else:
        raise ValueError(f"Unsupported vector database type: {vectordb_type}")
    
    return mapping
