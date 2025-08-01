"""
Academic PDF Reader MCP Server with enhanced capabilities
"""
import json
import os
from typing import Dict, Any
import uuid

from mcp.server.fastmcp import FastMCP
import mcp.types as types

from .core.pdf_processor import PDFProcessor
from .academic.text_processor import AcademicTextProcessor
from .academic.section_detector import SectionDetector
from .academic.citation_parser import CitationParser

# PDF file storage
pdf_files: Dict[str, Dict[str, Any]] = {}

# Create FastMCP server
mcp_server = FastMCP("academic-pdf-reader")

# Basic PDF Tools
@mcp_server.tool()
async def load_pdf(file_path: str, name: str = None) -> str:
    """Load a PDF file for processing"""
    if not file_path or not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")
    
    display_name = name or os.path.basename(file_path)
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
async def get_metadata(file_path: str) -> str:
    """Get PDF metadata and document information"""
    metadata = await PDFProcessor.get_metadata(file_path)
    return f"PDF Metadata:\n{json.dumps(metadata, indent=2)}"

@mcp_server.tool()
async def extract_images(file_path: str, page: int = None) -> str:
    """Extract images from PDF"""
    images = await PDFProcessor.extract_images(file_path, page)
    
    result = f"Found {len(images)} images"
    if page is not None:
        result += f" on page {page}"
    
    if images:
        result += "\n\nImage details:\n"
        for img in images:
            result += f"- Page {img['page']}: {img['width']}x{img['height']} pixels\n"
    
    return result

@mcp_server.tool()
async def render_page(file_path: str, page: int, dpi: int = 150) -> str:
    """Render a PDF page as an image"""
    img_b64 = await PDFProcessor.render_page(file_path, page, dpi)
    return f"Rendered page {page} at {dpi} DPI\nImage size: {len(img_b64)} characters"

# Academic Enhancement Tools
@mcp_server.tool()
async def extract_academic_text(file_path: str, page: int = None) -> str:
    """Extract text with proper academic reading order and formatting"""
    if page is not None:
        result = await AcademicTextProcessor._process_single_page(file_path, page)
        text_info = f"Page {page} processed text:\n{result['processed_text']}"
        
        if result['math_formulas']:
            text_info += f"\n\nMath formulas found: {len(result['math_formulas'])}"
            for i, formula in enumerate(result['math_formulas'][:3]):
                text_info += f"\n  Formula {i+1}: {formula}"
        
        return text_info
    else:
        result = await AcademicTextProcessor.extract_academic_text(file_path)
        return f"Full document processed:\n\n{result['full_text'][:2000]}{'...' if len(result['full_text']) > 2000 else ''}"

@mcp_server.tool()
async def detect_sections(file_path: str) -> str:
    """Detect and extract academic paper sections"""
    sections_data = await SectionDetector.detect_sections(file_path)
    sections = sections_data["sections"]
    
    if not sections:
        return "No academic sections detected in this PDF."
    
    result = f"Detected {len(sections)} academic sections:\n\n"
    
    for section_name, section_data in sections.items():
        content_preview = section_data["content"][:200]
        result += f"**{section_name.upper()}** ({section_data['word_count']} words)\n"
        result += f"{content_preview}{'...' if len(section_data['content']) > 200 else ''}\n\n"
    
    return result

@mcp_server.tool()
async def extract_abstract(file_path: str) -> str:
    """Extract the abstract from an academic paper"""
    abstract_data = await SectionDetector.extract_abstract(file_path)
    
    if not abstract_data["found"]:
        return "No abstract found in this PDF."
    
    result = f"Abstract ({abstract_data['word_count']} words):\n\n"
    result += abstract_data["abstract"]
    
    if "method" in abstract_data:
        result += f"\n\n[Extracted using {abstract_data['method']} method]"
    
    return result

@mcp_server.tool() 
async def extract_key_sections(file_path: str) -> str:
    """Extract key academic sections optimized for agent understanding"""
    key_sections = await SectionDetector.extract_key_sections(file_path)
    
    if not key_sections:
        return "No key academic sections found."
    
    result = "Key sections extracted for analysis:\n\n"
    
    for section_name, content in key_sections.items():
        result += f"**{section_name.upper()}**\n{content}\n\n---\n\n"
    
    return result

@mcp_server.tool()
async def extract_citations(file_path: str) -> str:
    """Extract citations and references from the academic paper"""
    citation_data = await CitationParser.extract_citations(file_path)
    
    result = f"Citation Analysis:\n"
    result += f"- In-text citations: {citation_data['citation_count']}\n"
    result += f"- Reference list entries: {citation_data['reference_count']}\n"
    result += f"- Citation style: {citation_data['citation_style']}\n\n"
    
    if citation_data["in_text_citations"]:
        result += "Sample in-text citations:\n"
        for citation in citation_data["in_text_citations"][:5]:
            result += f"  {citation['citation']} - {citation['type']}\n"
    
    if citation_data["references"]:
        result += f"\nFirst few references:\n"
        for ref in citation_data["references"][:3]:
            result += f"  [{ref['reference_number']}] {ref['raw_text'][:100]}...\n"
    
    return result

@mcp_server.tool()
async def chunk_content(file_path: str, chunk_size: int = 1000) -> str:
    """Break PDF content into agent-friendly chunks"""
    chunks = await AcademicTextProcessor.chunk_academic_content(file_path, chunk_size)
    
    result = f"Content chunked into {len(chunks)} segments:\n\n"
    
    for i, chunk in enumerate(chunks[:5]):  # Show first 5 chunks
        result += f"**Chunk {i+1}** (Pages {chunk['page_start']}-{chunk['page_end']}, {chunk['word_count']} words)\n"
        result += f"{chunk['text'][:200]}...\n\n"
    
    if len(chunks) > 5:
        result += f"... and {len(chunks) - 5} more chunks\n"
    
    return result

@mcp_server.tool()
async def analyze_document_structure(file_path: str) -> str:
    """Analyze the overall structure and characteristics of the academic document"""
    section_summary = await SectionDetector.get_section_summary(file_path)
    citation_summary = await CitationParser.get_citation_summary(file_path)
    metadata = await PDFProcessor.get_metadata(file_path)
    
    result = f"Document Structure Analysis:\n\n"
    result += f"**Document Type**: {section_summary['estimated_structure']}\n"
    result += f"**Total Pages**: {metadata['page_count']}\n"
    result += f"**Academic Sections Found**: {section_summary['total_sections']}\n\n"
    
    result += "**Section Coverage**:\n"
    for section, present in section_summary.items():
        if section.startswith('has_') and present:
            section_name = section.replace('has_', '').replace('_', ' ').title()
            result += f"  ✓ {section_name}\n"
    
    result += f"\n**Citation Profile**:\n"
    result += f"  - Total citations: {citation_summary['total_citations']}\n"
    result += f"  - Reference count: {citation_summary['total_references']}\n"
    result += f"  - Citation style: {citation_summary['citation_style']}\n"
    
    if citation_summary['reference_years']['min_year']:
        result += f"  - Reference span: {citation_summary['reference_years']['min_year']}-{citation_summary['reference_years']['max_year']}\n"
        result += f"  - Recent refs (2015+): {citation_summary['reference_years']['recent_references']}\n"
    
    return result

# Academic Prompts
@mcp_server.prompt()
async def summarize_academic_paper(file_path: str, focus: str = "general") -> types.PromptMessage:
    """Create an intelligent summary of an academic paper"""
    key_sections = await SectionDetector.extract_key_sections(file_path)
    metadata = await PDFProcessor.get_metadata(file_path)
    citation_summary = await CitationParser.get_citation_summary(file_path)
    
    focus_instructions = {
        "general": "Provide a comprehensive overview suitable for researchers",
        "methodology": "Focus on research methods, data collection, and analysis approaches",
        "results": "Emphasize findings, results, and statistical outcomes",
        "implications": "Highlight conclusions, implications, and future research directions"
    }
    
    instruction = focus_instructions.get(focus, focus_instructions["general"])
    
    content = f"""Please provide an academic summary of this research paper focusing on {focus}.

{instruction}

Document Information:
- Title: {metadata.get('title', 'N/A')}
- Author: {metadata.get('author', 'N/A')}
- Pages: {metadata.get('page_count', 'N/A')}
- Citations: {citation_summary['total_citations']} in-text, {citation_summary['total_references']} references

Key Sections Available:
"""
    
    for section_name, section_content in key_sections.items():
        content += f"\n**{section_name.upper()}:**\n{section_content}\n"
    
    return types.PromptMessage(
        role="user",
        content=types.TextContent(type="text", text=content)
    )

@mcp_server.prompt()
async def analyze_research_methodology(file_path: str) -> types.PromptMessage:
    """Analyze the research methodology of an academic paper"""
    sections = await SectionDetector.detect_sections(file_path)
    methods_content = ""
    
    if "methods" in sections["sections"]:
        methods_content = sections["sections"]["methods"]["content"]
    
    content = f"""Please analyze the research methodology of this academic paper.

Focus on:
1. Research design and approach
2. Data collection methods
3. Sample size and characteristics  
4. Statistical analysis methods
5. Limitations and validity considerations

Methods Section:
{methods_content if methods_content else "Methods section not clearly identified - please analyze the full document for methodological information."}
"""
    
    return types.PromptMessage(
        role="user", 
        content=types.TextContent(type="text", text=content)
    )

# Resources
@mcp_server.resource("file://{path}")
async def read_pdf_resource(path: str) -> str:
    """Read PDF with academic structure awareness"""
    try:
        key_sections = await SectionDetector.extract_key_sections(path)
        metadata = await PDFProcessor.get_metadata(path)
        
        return json.dumps({
            "metadata": metadata,
            "key_sections": key_sections,
            "document_type": "academic_paper" if key_sections else "general_pdf"
        }, indent=2)
    except Exception as e:
        raise ValueError(f"Error reading PDF: {str(e)}")

def main():
    """Main entry point for Academic PDF Reader MCP server"""
    mcp_server.run(transport="sse")

if __name__ == "__main__":
    main()