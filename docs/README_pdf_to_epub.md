# PDF to EPUB Module Documentation

## Overview
The `pdf_to_epub.py` module converts PDF documents to EPUB format using MinerU for extraction and AI-generated summaries. It's designed for academic papers and research documents.

## Architecture

### Core Components
- **PDF Extraction**: Uses MinerU Docker container for PDF to markdown conversion
- **Summary Generation**: Integrates with summary.py for AI-powered analysis
- **EPUB Conversion**: Converts markdown content to EPUB format
- **Path Management**: Handles file organization and naming conventions

### Data Flow
```
PDF → MinerU Extraction → Markdown → AI Summary → EPUB Generation
```

## Function Signatures

### `pdf_to_epub(pdf_path: str, output_path: str = None) -> str`
**Purpose**: Converts PDF to EPUB with AI-generated summary
**Parameters**:
- `pdf_path` (str): Path to the source PDF file
- `output_path` (str, optional): Output EPUB file path (auto-generated if None)

**Returns**: String path to the created EPUB file

## Processing Pipeline

### 1. Path Setup
- Extracts PDF filename and creates working directories
- Defines extraction and output folder structure
- Sets up figures and images paths

### 2. PDF Extraction
- Checks if markdown already exists to avoid re-processing
- Executes MinerU Docker container for PDF conversion
- Extracts text, images, tables, and formatting

### 3. Summary Generation (Planned)
- Integrates with `summary.py` module
- Generates AI-powered paper analysis
- Creates structured academic summary

### 4. EPUB Creation
- Combines full text and summary
- Converts to EPUB format using `markdown_to_epub`
- Maintains formatting and structure

## Configuration

### Environment Variables
- `SUMMARY_MODEL`: LLM model for summary generation (default: "genai:gemini-2.0-flash-exp")

### Folder Structure
```
Knowledge/
├── automation/
│   ├── extract/
│   │   └── {paper_name}/
│   │       └── {paper_name}/
│   │           └── auto/
│   │               ├── {paper_name}.md
│   │               └── images/
│   └── output/
│       └── Paper - {paper_name}.md
```

## Usage Examples

### Command Line Usage
```bash
python pdf_to_epub.py paper.pdf
```

### With Custom Output Path
```bash
python pdf_to_epub.py paper.pdf --output /path/to/output.epub
```

### Programmatic Usage
```python
from pdf_to_epub import pdf_to_epub

epub_path = pdf_to_epub("research_paper.pdf")
print(f"EPUB created at: {epub_path}")
```

## File Organization

### Input Structure
- Source PDF file

### Processing Structure
- Extract folder: `Knowledge/automation/extract/{name}/`
- Auto-generated content: `{name}/auto/`
- Images and figures: `auto/images/`

### Output Structure
- EPUB file: Same directory as source PDF
- Summary file: `Knowledge/automation/output/`

## Dependencies
- `subprocess`: Docker container execution
- `pathlib`: Path manipulation
- `os`: Operating system interface
- Custom utilities:
  - `utils.md_to_epub`: EPUB conversion
  - `summary`: AI summarization (integration planned)

## Integration Points

### MinerU Integration
- Uses Docker container for PDF processing
- Executes via `run_minerU.sh` shell script
- Handles layout preservation and figure extraction

### Summary Module Integration
- Planned integration with `summary.py`
- Will generate AI-powered academic summaries
- Uses configurable LLM models

### EPUB Conversion
- Uses custom `markdown_to_epub` utility
- Preserves formatting and structure
- Handles images and mathematical content

## Error Handling
- **File Existence**: Checks for existing extractions
- **Docker Execution**: Handles container execution errors
- **Path Validation**: Ensures proper directory structure
- **Permission Checks**: Validates write permissions

## Output Format

### EPUB Structure
- **Full Text**: Complete extracted PDF content
- **Summary**: AI-generated academic analysis (planned)
- **Images**: Embedded figures and diagrams
- **Metadata**: Paper information and processing details

### Naming Convention
- Input: `research_paper.pdf`
- Output: `research_paper.epub`
- Extract: `Knowledge/automation/extract/research_paper/`

## Performance Considerations
- **Caching**: Avoids re-extraction of existing files
- **Docker Overhead**: Container startup time for extraction
- **File Size**: EPUB size depends on images and content
- **Processing Time**: Proportional to PDF complexity

## Use Cases
- **Academic Research**: Converting papers for e-readers
- **Document Archival**: Long-term storage in standard format
- **Mobile Reading**: Optimized for tablet/phone reading
- **Accessibility**: Screen reader compatible format
- **Library Management**: Integration with e-book libraries

## Future Enhancements
- **Summary Integration**: Complete AI summary inclusion
- **Metadata Enhancement**: Rich bibliographic information
- **Style Customization**: Configurable EPUB themes
- **Batch Processing**: Multiple PDF conversion support