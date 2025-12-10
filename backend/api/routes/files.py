"""File upload API routes"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
import aiofiles
import os
from pathlib import Path
try:
    from backend.services.document_processor import get_document_processor
except ImportError:
    # Fallback if document processor not available
    def get_document_processor():
        class DummyProcessor:
            async def process_file(self, file_path):
                return {"success": False, "error": "Document processor not available", "content": ""}
        return DummyProcessor()

router = APIRouter(prefix="/api/files", tags=["files"])

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.txt', '.md',
    '.png', '.jpg', '.jpeg', '.gif', '.webp'
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload files for knowledge base and process them"""
    
    uploaded = []
    processor = get_document_processor()
    
    for file in files:
        # Validate file extension
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue
        
        # Validate file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            continue
        
        # Save file
        file_path = UPLOAD_DIR / f"{file.filename}"
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Process document in background
        processed_content = ""
        try:
            result = await processor.process_file(str(file_path))
            if result.get("success"):
                processed_content = result.get("content", "")
        except Exception as e:
            # If processing fails, still return file info
            print(f"Document processing failed: {e}")
        
        uploaded.append({
            "filename": file.filename,
            "size": len(content),
            "type": file.content_type,
            "path": str(file_path),
            "processed_content": processed_content,
            "processing_success": bool(processed_content)
        })
    
    return {"files": uploaded}


@router.get("/{filename}")
async def get_file(filename: str):
    """Retrieve uploaded file"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(file_path)

