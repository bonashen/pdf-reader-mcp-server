# pdf-reader MCP server

An MCP server for reading PDFs

## Components

### Resources

The server provides academic-aware PDF resources with:
- Custom `file://` URI scheme for accessing individual PDFs
- Academic structure detection and key section extraction
- Metadata enriched with document type classification
- Resources optimized for agent understanding

### Academic Prompts

The server provides specialized academic analysis prompts:
- **summarize-academic-paper**: Intelligent academic paper summarization
  - Required "file_path" argument for PDF location
  - Optional "focus" argument (general/methodology/results/implications)
  - Generates prompts with key sections, citations, and metadata
- **analyze-research-methodology**: Deep methodology analysis
  - Required "file_path" argument for PDF location
  - Focuses on research design, data collection, and statistical methods

### Enhanced Tools

**Basic PDF Processing:**
- **load-pdf**: Load and cache a PDF file for processing
- **get-metadata**: Get PDF metadata and document information
- **extract-images**: Extract embedded images with metadata
- **render-page**: Render PDF pages as high-resolution images

**Academic Enhancements:**
- **extract-academic-text**: Text extraction with proper reading order and math formula preservation
- **detect-sections**: Identify academic sections (Abstract, Introduction, Methods, Results, etc.)
- **extract-abstract**: Specifically extract the abstract section
- **extract-key-sections**: Get key sections optimized for agent understanding
- **extract-citations**: Parse in-text citations and reference lists
- **chunk-content**: Break content into agent-friendly semantic chunks
- **analyze-document-structure**: Comprehensive academic document analysis

## Configuration

This PDF reader MCP server provides comprehensive PDF processing capabilities including:
- Full text extraction from any PDF
- High-resolution image extraction 
- Table detection and extraction
- Annotation and comment extraction
- PDF metadata retrieval
- Page rendering to images
- Document structure analysis

## Installation & Setup

### Prerequisites

- Python 3.13 or higher
- `uv` package manager (install with `pip install uv`)

### Install Dependencies

```bash
uv sync
```

### IDE Integration

#### VSCode with MCP Extension

1. Install the [MCP VSCode Extension](https://marketplace.visualstudio.com/items?itemName=modelcontextprotocol.mcp)
2. Open your VSCode settings (`.vscode/settings.json`) and add:

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

```json
{
"mcp.servers": {
    "pdf-reader": {
      "command": "uvx",
      "args": [
        "academic_pdf_reader_mcp"
      ],
      "description": "PDF reader with full extraction capabilities",
      "env": {
        "PDF_READER_TRANSPORT": "stdio"
      }
    }
  }
}
```

#### WindSurf IDE

1. Open WindSurf settings
2. Navigate to Extensions → MCP Servers
3. Add a new server configuration:

```json
{
  "name": "pdf-reader",
  "url": "http://localhost:8000/sse",
  "description": "Comprehensive PDF processing server"
}
```

#### Cursor IDE

1. Open Cursor settings (Cmd/Ctrl + ,)
2. Search for "MCP" or navigate to Extensions → MCP
3. Add server configuration:
`SSE transport`:
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
`stdio transport`:
```json
{
"mcpServers": {
    "pdf-reader": {
      "command": "uvx",
      "args": [
        "academic_pdf_reader_mcp"
      ],
      "description": "PDF reader with full extraction capabilities",
      "env": {
        "PDF_READER_TRANSPORT": "stdio"
      }
    }
  }
}
```

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

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

Before using the PDF reader in any IDE, start the server. The server supports two transport modes:
- **SSE (Server-Sent Events)**: Default mode for connecting with IDEs
- **stdio**: Useful for debugging purposes

You can control the transport mode using the `PDF_READER_TRANSPORT` environment variable.

```bash
# Navigate to the pdf-reader directory
cd /path/to/your/pdf-reader

# Start the server in SSE mode (default)
uv run pdf-reader

# Or start the server in stdio mode for debugging
PDF_READER_TRANSPORT=stdio uv run pdf-reader
```

In SSE mode, the server will start on `http://localhost:8000` with the MCP SSE endpoint available at `/sse` for all IDEs to connect to.

## Usage Examples

Once configured in your IDE, you can use the PDF reader with natural language commands:

### Basic PDF Processing
```
"Load the research paper at /path/to/paper.pdf and extract all the text"
"Get metadata for the PDF document at /documents/report.pdf"
"Extract all images from the PDF on page 3"
```

### Advanced Analysis
```
"Summarize the PDF document in technical style focusing on methodology"
"Analyze the structure of this PDF and tell me about its organization"
"Extract all tables from the document and show me the data"
```

### Visual Processing
```
"Render page 5 of the PDF as a high-resolution image"
"Extract all annotations and comments from this PDF"
"Show me all the images embedded in this document"
```

### Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `load-pdf` | Load and cache PDF | `file_path`, optional `name` |
| `extract-text` | Extract text content | `file_path`, optional `page` |
| `extract-images` | Extract embedded images | `file_path`, optional `page` |
| `get-metadata` | Get document metadata | `file_path` |
| `extract-tables` | Extract table data | `file_path`, optional `page` |
| `extract-annotations` | Extract comments/highlights | `file_path` |
| `render-page` | Render page as image | `file_path`, `page`, optional `dpi` |

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. There are two recommended approaches for debugging:

#### Option 1: Use the stdio transport mode

You can run the server directly in stdio mode for basic debugging:

```bash
PDF_READER_TRANSPORT=stdio uv run pdf-reader
```

#### Option 2: Use the MCP Inspector

For the best debugging experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
npx @modelcontextprotocol/inspector uv --directory /Users/cloudchase/Desktop/AverageJoesLab/mcp-servers/pdf-reader run pdf-reader
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.