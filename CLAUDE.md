# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

This is a **template MCP server** created by `uvx create-mcp-server`. Currently implements a note-taking system as a demonstration. The goal is to transform this into an MCP server for reading and processing PDF files.

## Development Commands

### Package Management and Running
- `uv sync` - Sync dependencies and update lockfile
- `uv --directory /Users/cloudchase/Desktop/AverageJoesLab/mcp-servers/pdf-reader run pdf-reader` - Run the MCP server directly
- `uv build` - Build package distributions for publishing
- `uv publish` - Publish to PyPI (requires credentials)

### Debugging
- `npx @modelcontextprotocol/inspector uv --directory /Users/cloudchase/Desktop/AverageJoesLab/mcp-servers/pdf-reader run pdf-reader` - Launch MCP Inspector for debugging over stdio

## Current Template Architecture

### Core Structure
- **Entry Point**: `src/pdf_reader/__init__.py:main()` - Async entry point that delegates to server
- **Main Server**: `src/pdf_reader/server.py` - Contains all MCP protocol handlers and business logic
- **State Management**: In-memory dictionary (`notes: dict[str, str]`) - **NEEDS REPLACEMENT** for PDF functionality

### Current MCP Protocol Implementation (Template)
**Resources**: Custom `note://` URI scheme for accessing individual notes
- Each note exposed as a resource with text/plain mimetype
- **TO CHANGE**: Replace with PDF file resources

**Tools**: Single tool `add-note` for adding new notes
- **TO CHANGE**: Replace with PDF reading tools (e.g., `read-pdf`, `extract-text`, `get-pdf-metadata`)

**Prompts**: `summarize-notes` prompt with optional style argument
- **TO CHANGE**: Replace with PDF-specific prompts (e.g., `summarize-pdf`, `extract-sections`)

### Communication Pattern
- **IMPORTANT**: This project should use **streamable HTTP transport** instead of stdio
- Current template uses stdio transport (`mcp.server.stdio.stdio_server()`) - **NEEDS CHANGE**
- Should be converted to HTTP transport for better PDF file handling and streaming capabilities
- Server runs in async event loop with proper initialization options

## Implementation Plan for PDF Functionality

### Required Changes
1. **Transport Layer**: Convert from stdio to streamable HTTP transport
2. **Dependencies**: Add PDF processing library (PyPDF2, pdfplumber, or pymupdf)
3. **Resource Scheme**: Change from `note://` to `pdf://` or `file://`
4. **State Management**: Replace notes dict with PDF file tracking/caching
5. **Tools**: Implement PDF reading and processing tools
6. **Prompts**: Create PDF-specific prompts for content extraction and analysis

### Configuration Notes
- Requires Python >=3.13
- Dependencies: `mcp>=1.12.3`, `pymupdf>=1.23.0`, `pillow>=10.0.0`, `fastapi>=0.104.0`, `uvicorn>=0.24.0`
- Package entry point: `pdf-reader = "pdf_reader:main"`  
- Uses `uv_build` as build backend

## IDE Integration

### VSCode
Configure in `.vscode/settings.json`:
```json
{
  "mcp.servers": {
    "pdf-reader": {
      "url": "http://localhost:8000/sse",
      "description": "PDF reader with full extraction capabilities"
    }
  }
}
```

### WindSurf
Add to MCP Servers settings:
```json
{
  "name": "pdf-reader", 
  "url": "http://localhost:8000/sse",
  "description": "Comprehensive PDF processing server"
}
```

### Cursor  
Configure in MCP settings:
```json
{
  "mcpServers": {
    "pdf-reader": {
      "url": "http://localhost:8000/sse",
      "description": "PDF reader with text, image, and table extraction"
    }
  }
}
```

### Claude Desktop
Configure in `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "pdf-reader": {
      "url": "http://localhost:8000/sse",
      "description": "PDF reader with comprehensive extraction capabilities"
    }
  }
}
```

### Starting the Server
Before connecting any IDE, start the MCP server:
```bash
uv run pdf-reader
```
Server will be available at `http://localhost:8000` with MCP SSE endpoint at `/sse`