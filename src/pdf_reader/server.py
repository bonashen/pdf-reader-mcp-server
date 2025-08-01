import asyncio
import base64
import json
import os
from typing import Dict, List, Optional, Any
import uuid

import fitz  # PyMuPDF
from mcp.server.fastmcp import FastMCP
import mcp.types as types

# PDF file storage and caching
pdf_files: Dict[str, Dict[str, Any]] = {}
pdf_cache: Dict[str, fitz.Document] = {}

# Create FastMCP server
mcp_server = FastMCP("pdf-reader")

class PDFProcessor:
    """Handles all PDF processing operations"""
    
    @staticmethod
    async def extract_text(pdf_path: str, page_num: Optional[int] = None) -> str:
        """Extract text from PDF, optionally from specific page"""
        doc = await PDFProcessor._get_pdf_document(pdf_path)
        
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
        doc = await PDFProcessor._get_pdf_document(pdf_path)
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
    async def get_metadata(pdf_path: str) -> Dict[str, Any]:
        """Extract PDF metadata"""
        doc = await PDFProcessor._get_pdf_document(pdf_path)
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
    async def extract_tables(pdf_path: str, page_num: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract table-like structures from PDF"""
        doc = await PDFProcessor._get_pdf_document(pdf_path)
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
        doc = await PDFProcessor._get_pdf_document(pdf_path)
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
        doc = await PDFProcessor._get_pdf_document(pdf_path)
        
        if page_num >= len(doc):
            raise ValueError(f"Page {page_num} not found in PDF")
        
        page = doc[page_num]
        mat = fitz.Matrix(dpi/72, dpi/72)  # Scale factor
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img_b64 = base64.b64encode(img_data).decode()
        
        return img_b64
    
    @staticmethod
    async def _get_pdf_document(pdf_path: str) -> fitz.Document:
        """Get cached PDF document or load new one"""
        if pdf_path in pdf_cache:
            return pdf_cache[pdf_path]
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        pdf_cache[pdf_path] = doc
        return doc

# MCP Tools
@mcp_server.tool()
async def load_pdf(file_path: str, name: str = None) -> str:
    """Load a PDF file for processing"""
    if not file_path:
        raise ValueError("file_path is required")
    
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")
    
    display_name = name or os.path.basename(file_path)
    
    # Get metadata and cache the file
    metadata = await PDFProcessor.get_metadata(file_path)
    file_id = str(uuid.uuid4())
    
    pdf_files[file_id] = {
        "path": file_path,
        "name": display_name,
        "page_count": metadata["page_count"],
        "metadata": metadata
    }
    
    return f"Loaded PDF: {display_name}\nPages: {metadata['page_count']}\nFile ID: {file_id}"

@mcp_server.tool()
async def extract_text(file_path: str, page: int = None) -> str:
    """Extract text from PDF"""
    text = await PDFProcessor.extract_text(file_path, page)
    page_info = f" (page {page})" if page is not None else " (all pages)"
    return f"Text extracted from {os.path.basename(file_path)}{page_info}:\n\n{text}"

@mcp_server.tool()
async def extract_images(file_path: str, page: int = None) -> str:
    """Extract images from PDF"""
    images = await PDFProcessor.extract_images(file_path, page)
    
    result = f"Found {len(images)} images in {os.path.basename(file_path)}"
    if page is not None:
        result += f" (page {page})"
    
    if images:
        result += "\n\nImage details:\n"
        for img in images:
            result += f"- Page {img['page']}, Index {img['index']}: {img['width']}x{img['height']} pixels\n"
        
        # Return first few images as base64 (limit to avoid huge responses)
        if len(images) <= 3:
            result += "\nImage data (base64 PNG):\n"
            for i, img in enumerate(images):
                result += f"\nImage {i+1}: data:image/png;base64,{img['data'][:100]}...\n"
    
    return result

@mcp_server.tool()
async def get_metadata(file_path: str) -> str:
    """Get PDF metadata and document information"""
    metadata = await PDFProcessor.get_metadata(file_path)
    return f"PDF Metadata for {os.path.basename(file_path)}:\n\n{json.dumps(metadata, indent=2)}"

@mcp_server.tool()
async def extract_tables(file_path: str, page: int = None) -> str:
    """Extract tables from PDF"""
    tables = await PDFProcessor.extract_tables(file_path, page)
    
    result = f"Found {len(tables)} tables in {os.path.basename(file_path)}"
    if page is not None:
        result += f" (page {page})"
    
    if tables:
        result += "\n\nTable data:\n"
        for i, table in enumerate(tables):
            result += f"\nTable {i+1} (Page {table['page']}):\n"
            result += json.dumps(table['data'], indent=2)
            result += "\n"
    
    return result

@mcp_server.tool()
async def extract_annotations(file_path: str) -> str:
    """Extract annotations and comments from PDF"""
    annotations = await PDFProcessor.extract_annotations(file_path)
    
    result = f"Found {len(annotations)} annotations in {os.path.basename(file_path)}"
    
    if annotations:
        result += "\n\nAnnotations:\n"
        for i, annotation in enumerate(annotations):
            result += f"\n{i+1}. Type: {annotation['type']}\n"
            result += f"   Page: {annotation['page']}\n"
            result += f"   Author: {annotation['author']}\n"
            result += f"   Content: {annotation['content']}\n"
    
    return result

@mcp_server.tool()
async def render_page(file_path: str, page: int, dpi: int = 150) -> str:
    """Render a PDF page as an image"""
    if page is None:
        raise ValueError("page number is required")
    
    img_b64 = await PDFProcessor.render_page(file_path, page, dpi)
    
    return f"Rendered page {page} from {os.path.basename(file_path)} at {dpi} DPI\n\nImage data (base64 PNG):\ndata:image/png;base64,{img_b64[:100]}...\n\nFull image data length: {len(img_b64)} characters"

# MCP Resources
@mcp_server.resource("file://{path}")
async def read_pdf_resource(path: str) -> str:
    """Read PDF content by file path"""
    pdf_path = path
    
    try:
        # Return basic PDF info and first page text
        metadata = await PDFProcessor.get_metadata(pdf_path)
        first_page_text = await PDFProcessor.extract_text(pdf_path, 0)
        
        return json.dumps({
            "metadata": metadata,
            "first_page_preview": first_page_text[:1000] + "..." if len(first_page_text) > 1000 else first_page_text
        }, indent=2)
    except Exception as e:
        raise ValueError(f"Error reading PDF: {str(e)}")

# MCP Prompts
@mcp_server.prompt()
async def summarize_pdf(file_path: str, style: str = "brief") -> types.PromptMessage:
    """Create a summary of a PDF document"""
    try:
        metadata = await PDFProcessor.get_metadata(file_path)
        text_content = await PDFProcessor.extract_text(file_path)
        
        style_instruction = {
            "brief": "Provide a concise summary focusing on key points.",
            "detailed": "Provide a comprehensive summary with detailed analysis.",
            "technical": "Focus on technical aspects, data, and methodology."
        }.get(style, "Provide a balanced summary.")
        
        content = f"""Please analyze and summarize this PDF document.

{style_instruction}

Document Metadata:
- Title: {metadata.get('title', 'N/A')}
- Author: {metadata.get('author', 'N/A')}
- Pages: {metadata.get('page_count', 'N/A')}
- Creation Date: {metadata.get('creation_date', 'N/A')}

Full Text Content:
{text_content}"""
        
        return types.PromptMessage(
            role="user",
            content=types.TextContent(type="text", text=content)
        )
    except Exception as e:
        raise ValueError(f"Error processing PDF for summarization: {str(e)}")

@mcp_server.prompt()
async def analyze_pdf_structure(file_path: str) -> types.PromptMessage:
    """Analyze the structure and layout of a PDF"""
    try:
        metadata = await PDFProcessor.get_metadata(file_path)
        annotations = await PDFProcessor.extract_annotations(file_path)
        
        content = f"""Please analyze the structure and layout of this PDF document.

Document Information:
- File: {os.path.basename(file_path)}
- Pages: {metadata.get('page_count', 'N/A')}
- Title: {metadata.get('title', 'N/A')}
- Author: {metadata.get('author', 'N/A')}
- Encrypted: {metadata.get('encrypted', False)}
- File Size: {metadata.get('file_size', 0):,} bytes

Annotations Found: {len(annotations)}

Please provide insights about:
1. Document organization and structure
2. Content types present (text, images, tables, etc.)
3. Overall layout and formatting
4. Any special features or elements
"""
        
        return types.PromptMessage(
            role="user",
            content=types.TextContent(type="text", text=content)
        )
    except Exception as e:
        raise ValueError(f"Error processing PDF for structure analysis: {str(e)}")

def main():
    """Main entry point for MCP server with HTTP transport"""
    # Use the MCP SDK's built-in HTTP server with SSE transport
    mcp_server.run(transport="sse")

if __name__ == "__main__":
    main()