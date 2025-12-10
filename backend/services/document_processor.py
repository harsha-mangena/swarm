"""Document processing service using Google API"""

import os
from typing import List, Dict, Optional
from pathlib import Path
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    HAS_GOOGLE_AI = True
except ImportError:
    HAS_GOOGLE_AI = False


class DocumentProcessor:
    """Process documents using Google Generative AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if self.api_key and HAS_GOOGLE_AI:
            genai.configure(api_key=self.api_key)
        elif not HAS_GOOGLE_AI:
            print("Warning: google-generativeai not installed. Document processing will be limited.")
    
    async def process_file(self, file_path: str) -> Dict[str, any]:
        """Process a single file and extract text content"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = path.suffix.lower()
        
        try:
            # For images
            if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                return await self._process_image(file_path)
            
            # For PDFs and documents
            elif file_ext in ['.pdf', '.doc', '.docx']:
                return await self._process_document(file_path)
            
            # For text files
            elif file_ext in ['.txt', '.md']:
                return await self._process_text_file(file_path)
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_ext}",
                    "content": ""
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }
    
    async def _process_image(self, file_path: str) -> Dict[str, any]:
        """Process image files using Google Vision"""
        if not HAS_GOOGLE_AI or not self.api_key:
            return {
                "success": False,
                "error": "Google AI not configured",
                "content": ""
            }
        try:
            model = genai.GenerativeModel('gemini-pro-vision')
            
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            # Upload image
            uploaded_file = genai.upload_file(path=file_path)
            
            # Extract text from image
            response = model.generate_content([
                "Extract all text from this image. Return only the text content, no explanations.",
                uploaded_file
            ])
            
            content = response.text if response.text else ""
            
            # Clean up uploaded file
            genai.delete_file(uploaded_file.name)
            
            return {
                "success": True,
                "content": content,
                "type": "image"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }
    
    async def _process_document(self, file_path: str) -> Dict[str, any]:
        """Process PDF and document files"""
        if not HAS_GOOGLE_AI or not self.api_key:
            return {
                "success": False,
                "error": "Google AI not configured",
                "content": ""
            }
        try:
            # Upload file to Google
            uploaded_file = genai.upload_file(path=file_path)
            
            # Use Gemini to extract text
            model = genai.GenerativeModel('gemini-pro')
            
            response = model.generate_content([
                f"Extract all text content from this document: {uploaded_file.name}. "
                "Return only the extracted text, maintaining structure where possible."
            ])
            
            content = response.text if response.text else ""
            
            # Clean up uploaded file
            genai.delete_file(uploaded_file.name)
            
            return {
                "success": True,
                "content": content,
                "type": "document"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }
    
    async def _process_text_file(self, file_path: str) -> Dict[str, any]:
        """Process plain text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "type": "text"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }
    
    async def process_files(self, file_paths: List[str]) -> List[Dict[str, any]]:
        """Process multiple files"""
        results = []
        for file_path in file_paths:
            result = await self.process_file(file_path)
            result["file_path"] = file_path
            results.append(result)
        return results


# Global instance
_processor: Optional[DocumentProcessor] = None


def get_document_processor() -> DocumentProcessor:
    """Get document processor instance"""
    global _processor
    if _processor is None:
        _processor = DocumentProcessor()
    return _processor

