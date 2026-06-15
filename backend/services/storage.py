
import os
import shutil
import uuid
from fastapi import UploadFile
from backend.config import config

async def save_upload_file(file: UploadFile) -> tuple[str, str]:
    """
    Saves an uploaded file to the configured upload directory using a UUID.
    Returns a tuple of (original_filename, file_path).
    """
    file_uuid = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1]
    # Enforce xlsx extension if needed, but per requirements just save it.
    # However, logic downstream expects Excel.
    
    saved_filename = f"{file_uuid}{extension}"
    file_path = os.path.join(config.UPLOAD_DIR, saved_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return file.filename, file_path
