# Utility Modules Documentation

## Overview
The `utils/` package contains supporting utilities for the research automation system, providing core functionality for I/O operations, prompt management, path configuration, and specialized conversions.

## Module Architecture

### Core Utilities
- **I/O Operations** (`io.py`): File handling and content processing
- **Prompt Management** (`summary_prompts.py`): AI prompt templates and configurations
- **Path Configuration** (`summary_path.py`): Directory structure definitions
- **Markdown to EPUB** (`md_to_epub.py`): Document format conversion
- **Mermaid Diagrams** (`create_mermaid.py`): Diagram generation and validation

## Individual Module Documentation

### utils/io.py

#### `open_obsi_file(file_path: str) -> str`
**Purpose**: Opens and processes Obsidian-style markdown files
**Parameters**:
- `file_path` (str): Path to the markdown file

**Returns**: Content string with frontmatter removed
**Functionality**: 
- Handles Obsidian frontmatter (YAML between `---`)
- Extracts main content for processing
- Supports standard markdown files

### utils/summary_prompts.py

#### Configuration Variables
- **`tasks_tags`**: List of academic task categories
  - TAD, HPE, Tracking, Segmentation, Object-detection, NLP-based, Vision-NLP, Classification
  
- **`tags`**: Paper categorization tags
  - Paper, Transformers, SSM, CNN, Other, Image, Video, Foundation, Fine-Tuning
  
- **`rules`**: Processing guidelines for AI summarization
  - Formatting requirements
  - Tag selection rules
  - Output structure specifications
  
- **`prompt`**: Template for AI paper analysis
  - Structured analysis framework
  - Academic paper summarization guidelines
  - Computer vision specialization

#### Usage
```python
from utils.summary_prompts import rules, tags, prompt

formatted_prompt = prompt.format(template, "\\n".join(rules), ", ".join(tags), filename)
```

### utils/summary_path.py

#### Path Configuration
- **`local_extract_folder`**: "Knowledge/automation/extract"
  - Base directory for PDF extractions
  
- **`local_output_folder`**: "Knowledge/Papers/Diggested_Papers"
  - Output directory for processed summaries
  
- **`template_path`**: "Templates/summary.md"
  - Location of summary template file

#### Usage
All paths are relative to the vault_path provided in command line arguments.

### utils/md_to_epub.py

#### `markdown_to_epub(markdown_path, summary_path, output_path, title=None, author=None) -> None`
**Purpose**: Converts markdown content to EPUB format
**Parameters**:
- `markdown_path` (str): Path to main markdown content
- `summary_path` (str): Path to summary markdown
- `output_path` (str): Output EPUB file path
- `title` (str, optional): Book title
- `author` (str, optional): Book author

**Features**:
- Combines multiple markdown sources
- Preserves formatting and structure
- Handles embedded images
- Creates proper EPUB metadata

### utils/create_mermaid.py

#### `validate_diagram(report: str) -> str | None`
**Purpose**: Generates and validates Mermaid diagrams from text content
**Parameters**:
- `report` (str): Text content to analyze for diagram generation

**Returns**: Valid Mermaid diagram string or None
**Functionality**:
- Analyzes content for diagram opportunities
- Generates Mermaid syntax
- Validates diagram correctness
- Provides fallback handling

### utils/epub_utils.py

#### EPUB Processing Utilities
**Purpose**: Supporting functions for EPUB creation and manipulation
**Features**:
- EPUB structure management
- Metadata handling
- Content formatting
- File organization

### utils/pdf_minerU.py

#### MinerU Integration Utilities
**Purpose**: Interface for MinerU PDF extraction service
**Features**:
- Docker container management
- Extraction parameter configuration
- Output processing
- Error handling

## Integration Patterns

### Common Usage Patterns
```python
# Load configuration
from utils.summary_prompts import rules, tags, prompt
from utils.summary_path import local_extract_folder, local_output_folder

# Process files
from utils.io import open_obsi_file
content = open_obsi_file(file_path)

# Generate output
from utils.md_to_epub import markdown_to_epub
markdown_to_epub(md_path, summary_path, epub_path)
```

### Path Resolution
```python
import os
from utils.summary_path import local_extract_folder

# Resolve relative to vault
extract_folder = os.path.join(vault_path, local_extract_folder)
```

## Configuration Management

### Environment Integration
- Utilities respect environment variables
- Support for multiple deployment scenarios
- Configurable paths and templates

### Template System
- Customizable prompt templates
- Flexible rule systems
- Extensible tag hierarchies

## Error Handling

### File Operations
- Graceful handling of missing files
- Permission validation
- Path existence checking

### Format Conversion
- Input validation
- Fallback mechanisms
- Progress reporting

## Dependencies

### Core Dependencies
- `pathlib`: Path manipulation
- `os`: Operating system interface
- `json`: Configuration file handling

### Format-Specific Dependencies
- `EbookLib`: EPUB creation
- `markdown`: Markdown processing
- `Pillow`: Image handling

## Performance Considerations

### Memory Usage
- Streaming file processing where possible
- Efficient string operations
- Minimal memory footprint

### Processing Speed
- Optimized file I/O
- Caching mechanisms
- Batch processing support

## Extensibility

### Adding New Utilities
1. Create module in `utils/` directory
2. Follow naming conventions
3. Document public interfaces
4. Add integration examples

### Custom Configurations
- Override default paths
- Extend prompt templates
- Add new tag categories
- Customize processing rules