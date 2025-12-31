import logging
from typing import List
import json
from sqlalchemy.sql import text as sql_text

from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import (
    DistanceMetricEnums,
    VectorDBEnums,
    PgVectorTableSchemaEnums,
    PgVectorIndexTypeEnums
)
from ..utils import get_distance_metrics
from models.db_schemas import RetrievedDocument

class PgVector(VectorDBInterface):
    def __init__(self, 
                 db_client,
                 default_vector_size: int=786,
                 distance_metric: str=None, 
                 index_threshold: int=100,
                 *args, **kwargs):
        
        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.distance_metric = None
        self.index_threshold = index_threshold
        
        # Get distance metrics mapping for PgVector
        metrics_map = get_distance_metrics(vectordb_type=VectorDBEnums.PGVECTOR.value)
        
        if distance_metric and distance_metric in metrics_map:
            self.distance_metric = metrics_map[distance_metric]
        elif distance_metric:
            raise ValueError(f"Invalid distance metric for PgVector: {distance_metric}")
        else:
            # Default to cosine if not specified
            self.distance_metric = metrics_map[DistanceMetricEnums.COSINE.value]
        
        self.pgvector_table_prefix = PgVectorTableSchemaEnums._PREFIX.value
        self.logger = logging.getLogger('uvicorn')
        self.default_index_name = lambda collection_name: f"{collection_name}_vector_idx"
    
    async def connect(self):
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector;"))
    
    async def disconnect(self):
        pass
    
    async def is_collection_existed(self, collection_name: str) -> bool:
        table_exists = None
        
        async with self.db_client() as session:
            async with session.begin():
                list_table = sql_text(f"SELECT * FROM pg_tables WHERE tablename = :collection_name;")
                results = await session.execute(list_table, {"collection_name": collection_name})
                table_exists = results.scalar_one_or_none()
                
        return table_exists
    
    async def list_collections(self) -> list:
        records = []
        
        async with self.db_client() as session:
            async with session.begin():
                list_tables = sql_text(
                    f"SELECT tablename FROM pg_tables WHERE tablename LIKE '{self.pgvector_table_prefix}%';")
                results = await session.execute(list_tables)
                records = results.scalars().all()
                
        return records
    
    async def get_collection_info(self, collection_name: str) -> dict:
        table_data = None
        count_info = None
        
        async with self.db_client() as session:
            async with session.begin():
                table_info_sql = sql_text(f'''
                        SELECT schemaname, tablename, tableowner, tablespace, hasindexes
                        FROM pg_tables
                        WHERE tablename = :collection_name;
                    ''')
                count_sql = sql_text(f"SELECT COUNT(*) FROM {collection_name};")
                
                table_info = await session.execute(table_info_sql, {"collection_name": collection_name})
                count_info = await session.execute(count_sql)
                
                table_data = table_info.fetchone()
        
        if not table_data:
            return None
        return {
            "table_info": {
                "schemaname": table_data.schemaname,
                "tablename": table_data.tablename,
                "tableowner": table_data.tableowner,
                "tablespace": table_data.tablespace,
                "hasindexes": table_data.hasindexes
            },
            "record_count": count_info.scalar_one()
        }
    
    async def delete_collection(self, collection_name: str):
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f"Deleting collection: {collection_name}")
                delete_sql = sql_text(f"DROP TABLE IF EXISTS {collection_name};")
                await session.execute(delete_sql)
        return True
    
    async def create_collection(self, 
                          collection_name: str, 
                          embedding_size: int, 
                          do_reset: bool=False):
        
        if do_reset:
            await self.delete_collection(collection_name)
        
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.info(f"Creating collection: {collection_name}")
            async with self.db_client() as session:
                async with session.begin():
                    create_sql = sql_text(
                        f"CREATE TABLE {collection_name} ("
                            f"{PgVectorTableSchemaEnums.ID.value} bigserial PRIMARY KEY, "
                            f"{PgVectorTableSchemaEnums.TEXT.value} text, "
                            f"{PgVectorTableSchemaEnums.VECTOR.value} vector({embedding_size}), "
                            f"{PgVectorTableSchemaEnums.METADATA.value} jsonb DEFAULT '{{}}'::jsonb, "
                            f"{PgVectorTableSchemaEnums.CHUNK_ID.value} integer, "
                            f"FOREIGN KEY ({PgVectorTableSchemaEnums.CHUNK_ID.value}) REFERENCES chunks(chunk_id)"
                        ")"
                    )
                    await session.execute(create_sql)
                    
            return True
        self.logger.info(f"Collection already exists: {collection_name}; skipping creation.")
        return False
    
    async def is_index_existed(self, collection_name: str) -> bool:
        results = False
        index_name = self.default_index_name(collection_name=collection_name)
        async with self.db_client() as session:
            async with session.begin():
                ck_sql = sql_text(
                    f"SELECT 1 FROM pg_indexes WHERE tablename = :collection_name "
                    f"AND indexname = :index_name"
                )
                results = await session.execute(ck_sql, {"index_name": index_name, "collection_name": collection_name})
                results = results.scalar_one_or_none() is not None
        return results
    
    
    async def create_vector_index(self, collection_name: str, index_type: str=PgVectorIndexTypeEnums.HNSW.value):
        is_index_existed = await self.is_index_existed(collection_name=collection_name)
        if is_index_existed:
            return False
        
        async with self.db_client() as session:
            async with session.begin():
                count_sql = sql_text(f"SELECT COUNT(*) FROM {collection_name};")
                result = await session.execute(count_sql)
                record_count = result.scalar_one()
                
                if record_count < self.index_threshold:
                    return False
                
                self.logger.info(f"Creating index for collection: {collection_name}")
                index_name = self.default_index_name(collection_name=collection_name)
                
                create_idx_sql = sql_text(
                    f"CREATE INDEX {index_name} ON {collection_name} "
                    f"USING {index_type} ({PgVectorTableSchemaEnums.VECTOR.value} {self.distance_metric});")
                
                await session.execute(create_idx_sql)
                
                self.logger.info(f"Created index: {index_name} for collection: {collection_name}")
    
        return True
    
    async def reset_vector_index(self, collection_name: str, index_type: str=PgVectorIndexTypeEnums.HNSW.value):
        index_name = self.default_index_name(collection_name=collection_name)
        async with self.db_client() as session:
            async with session.begin():
                drop_idx_sql = sql_text(f"DROP INDEX IF EXISTS {index_name};")
                await session.execute(drop_idx_sql)
        
        return await self.create_vector_index(collection_name=collection_name, index_type=index_type)
        
            
    async def insert_one(self, 
                   collection_name: str, 
                   text: str,
                   vector: List[float], 
                   metadata: dict=None, 
                   record_id: str=None):
        
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        
        if not is_collection_existed:
            self.logger.error(f"Collection does not exist: {collection_name}; cannot insert document.")
            return False
        
        if not record_id:
            self.logger.error(f"Cannot insert document without chunk_id: collection: {collection_name}.")
            return False
        
        async with self.db_client() as session:
            async with session.begin():
                insert_sql = sql_text(
                    f"INSERT INTO {collection_name} "
                    f"({PgVectorTableSchemaEnums.TEXT.value}, "
                    f"{PgVectorTableSchemaEnums.VECTOR.value}, "
                    f"{PgVectorTableSchemaEnums.METADATA.value}, "
                    f"{PgVectorTableSchemaEnums.CHUNK_ID.value}) "
                    "VALUES (:text, :vector, :metadata, :chunk_id);"
                )
                await session.execute(insert_sql, {
                    "text": text,
                    "vector": "[" + ",".join(map(str, vector)) + "]",
                    "metadata": json.dumps(metadata, ensure_ascii=False) if metadata else "{}",
                    "chunk_id": record_id
                })
                
        await self.create_vector_index(collection_name=collection_name)
                
        return True

    async def insert_many(self, 
                    collection_name: str, 
                    texts: List[str],
                    vectors: List[List[float]], 
                    metadatas: List[dict]=None, 
                    record_ids: List[str]=None,
                    batch_size: int=50):
        
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Collection does not exist: {collection_name}; cannot insert documents.")
            return False
        
        if len(record_ids) != len(vectors):
            self.logger.error(f"Invalid data items for collection: {collection_name}.")
            return False
        
        if not metadatas or len(metadatas) == 0:
            metadatas = [None]*len(vectors)
        
        async with self.db_client() as session:
            async with session.begin():
                insert_sql = sql_text(
                        f"INSERT INTO {collection_name} "
                        f"({PgVectorTableSchemaEnums.TEXT.value}, "
                        f"{PgVectorTableSchemaEnums.VECTOR.value}, "
                        f"{PgVectorTableSchemaEnums.METADATA.value}, "
                        f"{PgVectorTableSchemaEnums.CHUNK_ID.value}) "
                        "VALUES (:text, :vector, :metadata, :chunk_id)"
                    )
                
                for i in range(0, len(vectors), batch_size):
                    batch_texts = texts[i:i+batch_size]
                    batch_vectors = vectors[i:i+batch_size]
                    batch_metadatas = metadatas[i:i+batch_size]
                    batch_record_ids = record_ids[i:i+batch_size]
                    
                    values = [
                        {
                            "text": t,
                            "vector": "[" + ",".join(map(str, v)) + "]",
                            "metadata": json.dumps(m, ensure_ascii=False) if m else "{}",
                            "chunk_id": r
                        }
                        for t, v, m, r in zip(batch_texts, batch_vectors, batch_metadatas, batch_record_ids)
                    ]
                    
                    await session.execute(insert_sql, values)
                    
        await self.create_vector_index(collection_name=collection_name)
        
        return True
    
    async def search_by_vector(self, 
                         collection_name: str, 
                         query_vector: List[float], 
                         top_k: int=5) -> List[RetrievedDocument]:
        
        is_collection_existed = await self.is_collection_existed(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Collection does not exist: {collection_name}; cannot insert documents.")
            return False
        
        query_vector = "[" + ",".join(map(str, query_vector)) + "]"
        
        async with self.db_client() as session:
            results = None
            
            async with session.begin():
                search_sql = sql_text(
                    f'SELECT {PgVectorTableSchemaEnums.TEXT.value} as text, '
                    f'1 - ({PgVectorTableSchemaEnums.VECTOR.value} <=> :vector) as score ' 
                    f'FROM {collection_name} '
                    'ORDER BY score DESC '
                    f'LIMIT {top_k}'
                )
                
                results = await session.execute(search_sql, {"vector": query_vector})
                
                results = results.fetchall()
            
            if not results or len(results) == 0:
                return None
             
            return [
                RetrievedDocument(
                    text=res.text, 
                    score=res.score
                ) for res in results
            ]
