"""
Core PDF processing functionality
"""
import base64
import os
from typing import Dict, List, Optional, Any
import fitz  # PyMuPDF

# PDF caching
pdf_cache: Dict[str, fitz.Document] = {}

class PDFProcessor:
    """Handles basic PDF processing operations"""
    
    @staticmethod
    async def get_pdf_document(pdf_path: str) -> fitz.Document:
        """Get cached PDF document or load new one"""
        if pdf_path in pdf_cache:
            return pdf_cache[pdf_path]
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        pdf_cache[pdf_path] = doc
        return doc
    
    @staticmethod
    async def get_metadata(pdf_path: str) -> Dict[str, Any]:
        """Extract PDF metadata"""
        doc = await PDFProcessor.get_pdf_document(pdf_path)
        metadata = doc.metadata
        
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "page_count": len(doc),
            "encrypted": doc.is_encrypted,
            "file_size": os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
        }
    
    @staticmethod
    async def extract_raw_text(pdf_path: str, page_num: Optional[int] = None) -> str:
        """Extract raw text from PDF"""
        doc = await PDFProcessor.get_pdf_document(pdf_path)
        
        if page_num is not None:
            if 0 <= page_num < len(doc):
                return doc[page_num].get_text()
            else:
                raise ValueError(f"Page {page_num} not found in PDF")
        
        # Extract all text
        text = ""
        for page in doc:
            text += page.get_text() + "\n\n"
        return text.strip()
    
    @staticmethod
    async def extract_images(pdf_path: str, page_num: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract images from PDF"""
        doc = await PDFProcessor.get_pdf_document(pdf_path)
        images = []
        
        pages_to_process = [page_num] if page_num is not None else range(len(doc))
        
        for page_idx in pages_to_process:
            if page_idx >= len(doc):
                continue
                
            page = doc[page_idx]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_data = pix.tobytes("png")
                    img_b64 = base64.b64encode(img_data).decode()
                    
                    images.append({
                        "page": page_idx,
                        "index": img_index,
                        "width": pix.width,
                        "height": pix.height,
                        "data": img_b64,
                        "format": "png"
                    })
                
                pix = None
        
        return images
    
    @staticmethod
    async def extract_tables(pdf_path: str, page_num: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract table-like structures from PDF"""
        doc = await PDFProcessor.get_pdf_document(pdf_path)
        tables = []
        
        pages_to_process = [page_num] if page_num is not None else range(len(doc))
        
        for page_idx in pages_to_process:
            if page_idx >= len(doc):
                continue
                
            page = doc[page_idx]
            
            # Find tables using text blocks and positioning
            tabs = page.find_tables()
            for tab_idx, tab in enumerate(tabs):
                table_data = tab.extract()
                tables.append({
                    "page": page_idx,
                    "table_index": tab_idx,
                    "data": table_data,
                    "bbox": tab.bbox
                })
        
        return tables
    
    @staticmethod
    async def extract_annotations(pdf_path: str) -> List[Dict[str, Any]]:
        """Extract annotations/comments from PDF"""
        doc = await PDFProcessor.get_pdf_document(pdf_path)
        annotations = []
        
        for page_idx, page in enumerate(doc):
            for annot in page.annots():
                annotations.append({
                    "page": page_idx,
                    "type": annot.type[1],  # Get annotation type name
                    "content": annot.info.get("content", ""),
                    "author": annot.info.get("title", ""),
                    "rect": list(annot.rect),
                    "created": annot.info.get("creationDate", ""),
                    "modified": annot.info.get("modDate", "")
                })
        
        return annotations
    
    @staticmethod
    async def render_page(pdf_path: str, page_num: int, dpi: int = 150) -> str:
        """Render a PDF page as base64 image"""
        doc = await PDFProcessor.get_pdf_document(pdf_path)
        
        if page_num >= len(doc):
            raise ValueError(f"Page {page_num} not found in PDF")
        
        page = doc[page_num]
        mat = fitz.Matrix(dpi/72, dpi/72)  # Scale factor
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img_b64 = base64.b64encode(img_data).decode()
        
        return img_b64
    
    @staticmethod
    async def get_page_blocks(pdf_path: str, page_num: int) -> List[Dict[str, Any]]:
        """Extract text blocks with positioning for academic processing"""
        doc = await PDFProcessor.get_pdf_document(pdf_path)
        
        if page_num >= len(doc):
            raise ValueError(f"Page {page_num} not found in PDF")
        
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        
        text_blocks = []
        for block in blocks:
            if "lines" in block:  # Text block
                block_text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"]
                    block_text += "\n"
                
                text_blocks.append({
                    "text": block_text.strip(),
                    "bbox": block["bbox"],
                    "block_no": block["number"]
                })
        
        return text_blocks