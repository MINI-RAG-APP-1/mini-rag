from .BaseController import BaseController
from typing import Union
import os


class ProjectController(BaseController):
    def __init__(self):
        super().__init__()
    
    
    def get_project_path(self, project_id: Union[str, int]) -> str:
        project_path = os.path.join(self.file_dir, str(project_id))
        os.makedirs(project_path, exist_ok=True)
        return project_path
