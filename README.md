# pdf-reader MCP server

An MCP server for reading PDFs

## Components

### Resources

The server provides PDF file resources with:
- Custom `file://` URI scheme for accessing individual PDFs
- Each PDF resource exposes metadata, page count, and content preview
- Resources updated when PDFs are loaded via the `load-pdf` tool

### Prompts

The server provides intelligent PDF analysis prompts:
- **summarize-pdf**: Creates comprehensive summaries of PDF documents
  - Required "file_path" argument for PDF location
  - Optional "style" argument (brief/detailed/technical)
  - Generates prompts with full document text and metadata
- **analyze-pdf-structure**: Analyzes document structure and layout
  - Required "file_path" argument for PDF location
  - Provides insights on organization, content types, and formatting

### Tools

The server implements comprehensive PDF processing tools:
- **load-pdf**: Load and cache a PDF file for processing
- **extract-text**: Extract text content from PDF (all pages or specific page)
- **extract-images**: Extract all embedded images with metadata
- **get-metadata**: Get PDF metadata (title, author, pages, creation date, etc.)
- **extract-tables**: Extract structured table data from PDF
- **extract-annotations**: Extract comments, highlights, and annotations
- **render-page**: Render PDF pages as high-resolution images

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

Before using the PDF reader in any IDE, start the HTTP server:

```bash
# Navigate to the pdf-reader directory
cd /path/to/your/pdf-reader

# Start the server
uv run pdf-reader
```

The server will start on `http://localhost:8000` with the MCP SSE endpoint available at `/sse` for all IDEs to connect to.

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

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).


You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /Users/cloudchase/Desktop/AverageJoesLab/mcp-servers/pdf-reader run pdf-reader
```


Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.