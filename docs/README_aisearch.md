# AiSearch Module Documentation

## Overview
The `aisearch.py` module provides AI-powered research automation capabilities using GPT-Researcher and web scraping. It can analyze markdown files, generate research queries, and produce comprehensive reports with internet research.

## Architecture

### Core Components
- **GPTResearcher Integration**: Uses the GPT-Researcher library for automated research
- **Query Generation**: Transforms markdown content into research queries
- **Web Scraping**: Fetches and processes web content
- **Report Generation**: Creates structured reports with summaries and diagrams
- **LLM Integration**: Uses litellm for flexible model support

### Data Flow
```
Markdown File → Query Generation → Internet Research → Report Generation → Enhanced Markdown
```

## Function Signatures

### `async get_report(query: str, report_type: str) -> tuple`
**Purpose**: Conducts automated research and generates a report
**Parameters**:
- `query` (str): The research query to investigate
- `report_type` (str): Type of report to generate (research_report, resource_report, outline_report, custom_report, detailed_report, subtopic_report)

**Returns**: `(report, research_context, research_costs, research_images, research_sources)`

### `get_md_query(prompt: str, file_path: str) -> str`
**Purpose**: Generates a research query from markdown file content
**Parameters**:
- `prompt` (str): Base prompt template
- `file_path` (str): Path to the markdown file to analyze

**Returns**: Combined prompt and generated query string

### `scrape_pages(urls: list[str]) -> list[str]`
**Purpose**: Scrapes text content from a list of URLs
**Parameters**:
- `urls` (list[str]): List of URLs to scrape

**Returns**: List of extracted text content from each URL

### `validate_diagram(report: str) -> str | None`
**Purpose**: Validates and generates Mermaid diagrams from report content
**Parameters**:
- `report` (str): The report content to analyze

**Returns**: Valid Mermaid diagram string or None if generation fails

## Configuration

### Environment Variables (.ai.env)
- `SMART_LLM`: Primary LLM model for research (e.g., "google_genai:gemini-2.0-flash")
- `QUERY_LLM`: LLM model for query generation
- `TAVILY_API_KEY`: API key for Tavily web search service
- `GOOGLE_API_KEY`: API key for Google/Gemini services

### Model Transformation
The module automatically transforms model names for litellm compatibility:
- `google_genai:model-name` → `gemini/model-name`

## Usage Examples

### Command Line Usage
```bash
python aisearch.py <dir_path> <markdown_file> <report_type>
```

### Report Types
- `research_report`: Comprehensive research analysis
- `resource_report`: Resource compilation and analysis
- `outline_report`: Structured outline format
- `custom_report`: Customizable report format
- `detailed_report`: In-depth analysis
- `subtopic_report`: Focused subtopic analysis

### Integration with Obsidian
The module can be integrated with Obsidian using the Python Scripter plugin by passing:
- Vault path
- Active file path
- Report type as arguments

## Dependencies
- `gpt_researcher`: Core research automation
- `litellm`: LLM abstraction layer
- `requests`: HTTP requests for web scraping
- `beautifulsoup4`: HTML parsing
- `python-dotenv`: Environment variable management

## Output
- Appends generated report to the original markdown file
- Creates a separate report file in the `report` folder
- Includes Mermaid diagrams when possible
- Provides research context, costs, and sources

## Error Handling
- Graceful handling of web scraping failures
- Fallback behavior for diagram generation failures
- Model transformation error handling for unsupported formats