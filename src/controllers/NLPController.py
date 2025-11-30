from typing import List
from .BaseController import BaseController
from models.db_schemas import Project, DataChunk
from stores.vectordb import VectorDBInterface
from stores.llm import LLMInterface
from stores.llm.LLMEnums import DocumentTypeEnums
import json

class NLPController(BaseController):
    def __init__(self, vectordb_client, generation_client, embedding_client):
        super().__init__()
        
        self.vectordb_client: VectorDBInterface = vectordb_client
        self.generation_client: LLMInterface = generation_client
        self.embedding_client: LLMInterface = embedding_client
        
    def generate_collection_name(self, project_id: str):
        return f"collection_{project_id}".strip()
    
    def reset_db_collection(self, project: Project):
        collection_name = self.generate_collection_name(project_id=project.project_id)
        return self.vectordb_client.delete_collection(collection_name=collection_name)
        
    def get_vector_collection_info(self, project: Project):
        collection_name = self.generate_collection_name(project_id=project.project_id)
        collection_info = self.vectordb_client.get_collection_info(collection_name=collection_name)
        return json.loads(
            json.dumps(collection_info, default=lambda o: o.__dict__)
            )
    
    def index_into_vector_db(self, project: Project, chunks: List[DataChunk],
                             chunks_ids: List[int], do_reset: bool=False):
        
        # get collection name
        collection_name = self.generate_collection_name(project_id=project.project_id)
        
        # manage items
        filtered_items = [(c.chunk_text, c.chunk_metadata) for c in chunks] # get texts and metadatas
        texts, metadatas = zip(*filtered_items) # transpose into two tiples
        vectors = [
            self.embedding_client.embed_text(text=text, document_type=DocumentTypeEnums.DOCUMENT.value) 
            for text in texts 
            ]
        
        # create collection
        self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset
        )
        
        
        # insert into db
        self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=list(texts),
            vectors=vectors,
            metadatas=list(metadatas),
            record_ids=chunks_ids
        )
        
        return True

    def search_vector_db(self, project: Project, query_text: str, top_k: int =5):
        collection_name = self.generate_collection_name(project_id=project.project_id)
        
        query_vector = self.embedding_client.embed_text(
            text=query_text,
            document_type=DocumentTypeEnums.QUERY.value
        )
        
        if not query_vector or len(query_vector) == 0:
            return False
        
        results = self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            query_vector=query_vector,
            top_k=top_k
        )
        
        if not results:
            return False
        
        return json.loads(
            json.dumps(results, default=lambda o: o.__dict__)
            )
