import aiofiles as aio
from fastapi import APIRouter, UploadFile, status, Depends
from fastapi.responses import JSONResponse

from controllers import DataController, ProjectController, ProcessController
from helpers.config import get_settings, Settings
from helpers.utils import generate_unique_filepath, message_handler
from models import ResponseMessage

from .schemas.data import ProcessResponse

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)

@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, 
                      file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):
    
    
    # Validate file extension
    data_controller = DataController()
    is_valid, message = data_controller.validate_file(file)

    if is_valid == False:
        return JSONResponse(content=message, status_code=status.HTTP_400_BAD_REQUEST)

    project_dir_path = ProjectController().get_project_path(project_id)
    generated_file_info = generate_unique_filepath(file.filename, project_dir_path)
    file_path = generated_file_info.get("path")

    try:
        async with aio.open(file_path, 'wb') as out_file:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await out_file.write(chunk)

    except Exception as e:
        return JSONResponse(content=ResponseMessage.FILE_UPLOADED_ERROR.value.format(filename=generated_file_info.get("filename")), status_code=status.HTTP_400_BAD_REQUEST)
    
    message = message_handler(
        ResponseMessage.FILE_UPLOADED.value.format(filename=generated_file_info.get("filename")),
        file_id=generated_file_info.get("filename")
    )
    return JSONResponse(content=message, status_code=status.HTTP_201_CREATED)

@data_router.post("/process/{project_id}")
async def process_data(project_id: str, 
                       process_request: ProcessResponse):
    
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    
    process_controller = ProcessController(project_id)

    file_content = process_controller.get_file_content(file_id)
    file_chunks = process_controller.process_file_content(
        file_content=file_content,
        chunk_size=chunk_size,
        overlap_size=overlap_size
    )
    
    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            content=message_handler(
                ResponseMessage.FILE_PROCESSING_ERROR.value.format(file_id=file_id)
            ),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    message = message_handler(
        ResponseMessage.FILE_PROCESSING_SUCCESS.value,
        file_id=file_id,
        file_chunks=file_chunks
    )
    return message
