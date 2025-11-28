from helpers.config import Settings
from .utils import get_all_vector_dbs
from controllers.BaseController import BaseController

class VectorDBFactory:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._registry = get_all_vector_dbs()
        self.base_controller = BaseController()
    
    def create(self, provider: str):
        Provider = self._registry.get(provider)
        
        if not Provider:
            return None
        
        db_path = self.base_controller.get_database_path(db_name=self.settings.VECTOR_DB_PATH_NAME)
        
        return Provider(
            db_path=db_path,
            distance_metric=self.settings.VECTOR_DB_DISTANCE_METRIC
        )
