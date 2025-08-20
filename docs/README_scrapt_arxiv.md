# ArXiv Scraper Module Documentation

## Overview
The `scrapt_arxiv.py` module fetches recent papers from ArXiv, performs relevance scoring using semantic similarity, detects GitHub repositories, and generates formatted reports for research newsletters.

## Architecture

### Core Components
- **ArXiv API Integration**: Fetches papers using the arxiv Python library
- **Semantic Scoring**: Uses SentenceTransformers for relevance evaluation
- **GitHub Detection**: Identifies associated code repositories
- **Report Generation**: Creates markdown-formatted newsletters
- **Data Filtering**: Applies configurable filters and thresholds

### Data Flow
```
ArXiv Query → Paper Fetching → Relevance Scoring → GitHub Detection → Newsletter Generation
```

## Function Signatures

### `get_recent_arxiv_links_with_arxivpy(query, sort_by_choice="relevance", max_results=50) -> list`
**Purpose**: Fetches recent ArXiv papers using the arxiv library
**Parameters**:
- `query` (str): Search query for ArXiv
- `sort_by_choice` (str): Sort criterion ("relevance" or "lastupdateddate")
- `max_results` (int): Maximum number of results to fetch

**Returns**: List of paper objects with metadata

### `score_papers_with_transformers(papers, query_text, threshold=0.7) -> list`
**Purpose**: Scores papers for relevance using semantic similarity
**Parameters**:
- `papers` (list): List of paper objects to score
- `query_text` (str): Reference text for similarity comparison
- `threshold` (float): Minimum similarity threshold

**Returns**: List of scored papers above threshold

### `detect_github_in_papers(papers) -> list`
**Purpose**: Detects GitHub repository links in paper abstracts
**Parameters**:
- `papers` (list): List of paper objects to analyze

**Returns**: List of papers with GitHub repository information

### `generate_newsletter_content(papers, title, date) -> str`
**Purpose**: Generates formatted newsletter content
**Parameters**:
- `papers` (list): List of papers to include
- `title` (str): Newsletter title
- `date` (str): Publication date

**Returns**: Markdown-formatted newsletter content

## Configuration

### Environment Variables (.env)
- `ARXIV_QUERY_FILE`: Path to query configuration file
- `NEWSLETTER_OUTPUT_PATH`: Output directory for newsletters
- `EMBEDDING_MODEL`: Model for semantic similarity (default: sentence-transformers)

### Query Configuration File
JSON format with newsletter configurations:
```json
{
  "newsletter_name": {
    "query": "computer vision transformers",
    "threshold": 0.7,
    "max_results": 50,
    "sort_by": "relevance"
  }
}
```

## Data Processing Pipeline

### 1. Paper Fetching
- Connects to ArXiv API
- Applies search queries
- Handles rate limiting and errors
- Extracts paper metadata

### 2. Relevance Scoring
- Embeds paper abstracts using SentenceTransformers
- Computes cosine similarity with query
- Filters papers by threshold
- Ranks by relevance score

### 3. GitHub Detection
- Scans abstracts for GitHub URLs
- Validates repository links
- Extracts repository metadata
- Associates code with papers

### 4. Newsletter Generation
- Formats papers in markdown
- Groups by relevance score
- Includes metadata and links
- Generates publication date

## Scoring System

### Relevance Metrics
- **Cosine Similarity**: Primary relevance measure
- **Threshold Filtering**: Configurable minimum scores
- **Ranking**: Ordered by descending relevance

### GitHub Integration
- **Repository Detection**: Pattern matching for GitHub URLs
- **Link Validation**: Checks repository accessibility
- **Metadata Extraction**: Repository stars, forks, description

## Output Format

### Newsletter Structure
```markdown
# Newsletter Title - Date

## High Relevance Papers (Score > 0.8)
- [Paper Title](arxiv_link) - Score: 0.85
  - GitHub: [repo_name](github_link)
  - Abstract: Brief summary...

## Medium Relevance Papers (Score > 0.7)
...
```

### Paper Information Includes
- Title and ArXiv link
- Relevance score
- GitHub repository (if detected)
- Abstract excerpt
- Publication date
- Author information

## Usage Examples

### Command Line Usage
```bash
python scrapt_arxiv.py --config queries.json --output newsletters/
```

### Query Configuration Example
```json
{
  "computer_vision": {
    "query": "computer vision deep learning",
    "threshold": 0.75,
    "max_results": 30,
    "sort_by": "relevance"
  },
  "nlp_transformers": {
    "query": "natural language processing transformers",
    "threshold": 0.8,
    "max_results": 25,
    "sort_by": "lastupdateddate"
  }
}
```

## Dependencies
- `arxiv`: Official ArXiv API client
- `sentence-transformers`: Semantic similarity models
- `scikit-learn`: Cosine similarity computation
- `requests`: HTTP requests for GitHub validation
- `numpy`: Numerical operations

## Performance Considerations

### Optimization Features
- **Batch Processing**: Multiple papers processed together
- **Caching**: Embeddings cached for repeated queries
- **Rate Limiting**: Respects ArXiv API limits
- **Parallel Processing**: Concurrent GitHub repository checks

### Resource Usage
- **Memory**: Proportional to batch size and model size
- **Network**: ArXiv API and GitHub validation requests
- **Processing**: Transformer model inference time

## Error Handling
- **API Failures**: Graceful degradation for ArXiv/GitHub errors
- **Invalid Papers**: Skips malformed entries
- **Network Issues**: Retry logic with exponential backoff
- **Model Loading**: Fallback to simpler similarity measures

## Integration Points
- **ArXiv API**: Official paper database
- **GitHub API**: Repository metadata
- **SentenceTransformers**: Semantic models
- **Newsletter Systems**: Markdown output compatibility