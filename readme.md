Vault Scripts Repository
This repository contains a collection of Python scripts for automating research workflows, paper summaries, and data synchronization.

# Key Files

- aisearch.py  
  Contains functionality to conduct AI research using custom prompt templates and interact with large language models (LLMs) to generate research reports.
- summary.py  
  Processes PDF documents and Markdown files to generate summaries, extract tags, and compile detailed analyses of academic papers.
- md_format.py  
  Provides functions to format Markdown reports including generating ASCII histograms and scatter plots visualizing paper score distributions.
- scrapt_arxiv.py  
  Fetches recent papers from arXiv using queries and performs relevance scoring, GitHub repository detection, and data filtering.
- pdf-extract.py  
  Contains functions to extract text and images from PDF files using pdfminer.

# Environment Setup

There are two environment configuration files:

1. .env  
   Contains API keys and configuration for various services (OpenAI, Anthropic, Tavily, DeepSeek, Gemini).  
   You can use the example file (.env.example) as a starting point:  
   cp .env.example .env  
2. .ai.env  
   Contains AI API endpoints and model configurations such as OpenAI and Ollama.  
   Similarly, use .ai.env.example as your template:  
   cp .ai.env.example .ai.env  

   ## .ai.env Information
   - OPENAI_API_KEY, OPENAI_API_BASE: API key and base URL for OpenAI services.
   - OLLAMA_BASE_URL: Base URL for accessing Ollama API endpoints.
   - GOOGLE_API_KEY, GEMINI_API_KEY: API keys for Google services and Gemini.
   - FAST_LLM, SMART_LLM, STRATEGIC_LLM: Identifiers for fast, smart, and strategic LLM models.
   - EMBEDDING: Model identifier for embedding services.
   - TAVILY_API_KEY: API key for Tavily services.

   Ensure that both .env and .ai.env are updated with the correct keys and endpoints for your environment.

# Quickstart

- Clone the repository.
- Install the dependencies listed in requirements.txt.
- Install the aisuite fork with ```cd packages/aisuite && pip install .```
<!-- - Install Ollama for Local LLM. -->
- Update the .env and .ai.env files with your credentials.
- Run the desired script (e.g., aisearch.py, summary.py) as needed.


# Additional Notes

- Each script contains its own error handling and logging.
- You may adjust query parameters, API endpoints, or file paths depending on your use case.