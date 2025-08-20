# Summary Module Documentation

## Overview
The `summary.py` module processes PDF documents by converting them to markdown using MinerU and then generating AI-powered summaries. It's specifically designed for academic papers in computer vision and related fields.

## Architecture

### Core Components
- **PDF Extraction**: Uses MinerU Docker container to extract PDF content
- **Markdown Processing**: Analyzes extracted markdown files
- **AI Summarization**: Uses LLMs to generate structured summaries
- **Template System**: Configurable output templates
- **Figure Management**: Handles images and tables from PDFs

### Data Flow
```
PDF → MinerU Extraction → Markdown → AI Analysis → Structured Summary
```

## Function Signatures

### `process_single_md(file_path, vault_path, loc_figures_path, output_folder, template_folder, tags=None, model_name="openai/gpt-4o-2024-11-20", prompt="", rules=None) -> None`
**Purpose**: Processes a single markdown file and generates analysis
**Parameters**:
- `file_path` (str): Path to the markdown file to process
- `vault_path` (str): Base vault directory path
- `loc_figures_path` (str): Path to figures/images directory
- `output_folder` (str): Directory for output files
- `template_folder` (str): Path to template file
- `tags` (list, optional): List of tags to apply
- `model_name` (str): LLM model identifier (litellm format)
- `prompt` (str): Custom prompt template
- `rules` (list, optional): List of processing rules

**Returns**: None (writes to file)

### Main Script Arguments
When run as a script, accepts:
- `vault_path` (str): Path to the vault folder
- `file_name` (str): Name of the PDF file to process

## Configuration

### Environment Variables (.env)
- `SUMMARY_MODEL`: LLM model for summarization (default: "gemini/gemini-2.0-flash")

### Path Configuration (utils/summary_path.py)
- `local_extract_folder`: "Knowledge/automation/extract"
- `local_output_folder`: "Knowledge/Papers/Diggested_Papers"
- `template_path`: "Templates/summary.md"

### Prompt Configuration (utils/summary_prompts.py)
- **Tags**: Predefined list for categorization (Paper, Transformers, SSM, CNN, etc.)
- **Task Tags**: Specific task categories (TAD, HPE, Tracking, Segmentation, etc.)
- **Rules**: Processing guidelines and formatting requirements
- **Prompt Template**: Structured prompt for AI analysis

## Template System

### Summary Template Structure
The template file should contain:
1. Obsidian-style metadata (optional)
2. Structured sections for paper analysis
3. Placeholders for AI-generated content

### Supported Formats
- Markdown with Obsidian extensions
- LaTeX math notation ($.$ and $$.$$)
- Image references (![[path]] format)
- Table preservation

## Usage Examples

### Command Line Usage
```bash
python summary.py <vault_path> <pdf_file>
```

### Example with Real Paths
```bash
python summary.py /home/user/vault paper.pdf
```

### Docker Integration
The module automatically calls MinerU via Docker:
```bash
bash run_minerU.sh <pdf_path> <output_folder>
```

## Processing Pipeline

### 1. PDF Extraction
- Checks if markdown already exists
- Runs MinerU Docker container if needed
- Extracts text, images, and tables

### 2. Content Analysis
- Reads extracted markdown
- Processes images and figures
- Applies content formatting rules

### 3. AI Summarization
- Uses configured LLM model
- Applies prompt template and rules
- Generates structured summary

### 4. Output Generation
- Creates formatted summary file
- Preserves figure references
- Maintains academic structure

## Output Format

### Generated Summary Contains
1. **Metadata**: Tags and categorization
2. **Summary**: Main contributions and methods
3. **Concepts**: New architectures and techniques
4. **Training Strategy**: Learning approach and datasets
5. **Task Definition**: Specific problem being solved
6. **Figures**: All images and tables with captions

### File Naming Convention
- Input: `paper.pdf`
- Output: `Paper - paper.md`

## Dependencies
- `litellm`: LLM abstraction layer
- `python-dotenv`: Environment configuration
- `subprocess`: Docker container execution
- Custom utilities from `utils/` package

## Error Handling
- Checks for existing extracted files
- Validates file paths and permissions
- Handles Docker execution errors
- Graceful LLM API failure handling

## Integration Points
- **MinerU**: PDF to markdown conversion
- **Docker**: Containerized extraction
- **Obsidian**: Compatible markdown format
- **Various LLMs**: Through litellm interface