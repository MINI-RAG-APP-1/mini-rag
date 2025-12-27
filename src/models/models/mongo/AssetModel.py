from ..BaseDataModel import BaseDataModel
from ...db_schemas import AssetMongo as Asset
from ...enums.DataBaseEnum import DataBaseEnum
from typing import List


class AssetModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.counters_collection = None
    
    
    @classmethod
    async def create_instance(cls, db_client):
        isinstance = cls(db_client)
        await isinstance.init_collection()
        return isinstance
    
    
    async def init_collection(self):
        collection_name = DataBaseEnum.COLLECTION_ASSET_NAME.value
        all_collections = await self.db_client.list_collection_names()
        self.collection = self.db_client[collection_name]
        self.counters_collection = self.db_client["counters"]
        
        if collection_name not in all_collections:
            print(f"⏳ Initializing collection: '{collection_name}'")
            indexes = Asset.get_indexes()
            for index in indexes:
                await self.collection.create_index(**index)
    
    
    async def _get_next_asset_id(self) -> str:
        """Get the next auto-incremented asset_id as a string"""
        result = await self.counters_collection.find_one_and_update(
            {"_id": "asset_id"},
            {"$inc": {"sequence_value": 1}},
            upsert=True,
            return_document=True
        )
        return str(result["sequence_value"])
    
         
    async def create_asset(self, asset: Asset) -> Asset:
        # Generate auto-increment ID if not provided
        if asset.asset_id is None:
            asset.asset_id = await self._get_next_asset_id()
        
        result = await self.collection.insert_one(asset.model_dump(by_alias=True, exclude_unset=True))
        asset.id = result.inserted_id
        return asset
    
    
    async def get_all_assets(self, 
                             asset_project_id: str, 
                             asset_type: str) -> List[Asset]:
        
        records =  await self.collection.find({
            "asset_project_id": asset_project_id,
            "asset_type": asset_type
            }).to_list(length=None)
        
        return [Asset(**record) for record in records]
    
    async def count_assets(self, 
                           asset_project_id: str, 
                           asset_type: str) -> int:
        
        return await self.collection.count_documents({
            "asset_project_id": asset_project_id,
            "asset_type": asset_type
        })
    
    async def get_asset_by_name(self, 
                                asset_name: str, 
                                asset_project_id: str) -> Asset:
        
        asset_data = await self.collection.find_one({
            "asset_name": asset_name,
            "asset_project_id": asset_project_id
        })
        return Asset(**asset_data) if asset_data else None
