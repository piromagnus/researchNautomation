Vault Scripts Repository
This repository contains a collection of Python scripts for automating research workflows, paper summaries, and data synchronization.


# Quick Start

## MinerU 
MinerU is a tool designed to automate the processing of a pdf and turn it into markdown. It gets all the layouts, including images, latex formula and tables.  
 See [minerU](https://github.com/opendatalab/MinerU) for more information.
1. Build the docker image:
```bash
docker build -t mineru:latest .
```
2. Modify the ROOT_DIR in the run_minerU.sh to adapt at your architecture containing our pdf. The filepath will be relative to this root dir.
3. Run the docker container:
```bash
  bash run_minerU.sh <filepath> <output_dir>
```

## Install the dependencies
```bash
pip install -r requirements.txt
```


## AiSearch
Based on [GPT-Researcher](https://github.com/assafelovic/gpt-researcher). It get the content of a markdown file and generate a report on it with the help of a LLM and search on Internet with [Tavily](https://tavily.com/).

To run it
```bash
python aisearch.py <dir_path> <markdown_file> <report_type>
```
report_type is
`"research_report" | "resource_report" | "outline_report"|  "custom_report"|  "detailed_report"|  "subtopic_report"`
more details in [GPT-Researcher](https://github.com/assafelovic/gpt-researcher)

It will append the report to the markdown file and generate a log report in the same directory under `report` folder.

it can be using in Obsidian with the plugin python scripter adding a argument for the report type and passing Vault path and active file path.

You must file the ai.env file (using the example file) with the API keys for Gemini (default) and Tavily.
For small query, Ollama is used by default but if you have less memory you can try to use a smaller LLM though it will produce less accurate results.

For gemini you can get free api access on [aistudio](https://aistudio.google.com/).

You can change model in aisearch but take care GPT-Researcher use lanchain-llm models that can be incompatible with aisuite. (eg: google-genai vs genai)

## Summary
The summary.py script is designed to process PDF documents and Markdown files, generating summaries and extracting relevant tags. It can also compile detailed analyses of academic papers.
I use [minerU](https://github.com/opendatalab/MinerU) to extract the pdf and then I use aisuite to generate the summary.

### Setup
1. Ensure you have the required dependencies installed. You can do this by running:
```bash
pip install -r requirements.txt
```
2. Build the Docker image for MinerU:
```bash
docker build -t mineru:latest .
```
3. Modify the .env to add you API Keys for Gemini or any other LLM you want to use.  
   You can use the example file (.env.example) as a starting point:  
```bash
cp .env.example .env
```
4. Modify the utils/summary_path.py to setup the path of your structure. All the paths are relative to the vault_path from the command line.
5. Modify the utils/summary_prompt to adapt the prompt to your needs. By default there is a set of tags, tasks and rules to follow. It is mostly setup of computer vision but you can adapt it to your needs.
6. You need to give a template for the summary. You can use the example file [demo](demo/demo_template.md) as a starting point. The first part, of the file is some metadata in an Obsidian format so you can change it if you need.

### To run

```bash
python summary.py <vault_path> <markdown_path>
```
## Scrap arxiv
The scrapt_arxiv.py script is designed to fetch recent papers from arXiv using specific queries. It performs relevance scoring, GitHub repository detection, and data filtering to ensure the retrieved papers are relevant to your research interests.
### Setup
1. Ensure you have the required dependencies installed. You can do this by running:
```bash
pip install -r requirements.txt
```
2. Modify the .env file to add your API Keys for OpenAI, Anthropic, Tavily, DeepSeek, and Gemini.  
   You can use the example file (.env.example) as a starting point:  
```bash
cp .env.example .env
```
3. Modify the .env also to setup the path of your structure. As the command doesn't ask input everything is setup in the .env. You will also require a query file that will contains the differents settings of each newsletter. see [demo](demo/demo_query.md) for an example. You can add as many queries as you want using a different title as a name. The script will fetch the papers from arxiv and filter them with the queries in the config file.


### Run
```bash
python scrapt_arxiv.py <nb_days>
```
with nb_days is the number of days you want to go back in the past. It will fetch all the papers from arxiv in the last nb_days days and filter them with the queries in the config file.

# Key Files

- aisearch.py  
  Contains functionality to conduct AI research using custom prompt templates and interact with large language models (LLMs) to generate research reports.
- summary.py  
  Processes PDF documents and Markdown files to generate summaries, extract tags, and compile detailed analyses of academic papers.
- md_format.py  
  Provides functions to format Markdown reports including generating ASCII histograms and scatter plots visualizing paper score distributions.
- scrapt_arxiv.py  
  Fetches recent papers from arXiv using queries and performs relevance scoring, GitHub repository detection, and data filtering.


# Environment Setup

There are two environment configuration files:

1. .env  
   Contains API keys and configuration for various services (OpenAI, Anthropic, Tavily, DeepSeek, Gemini).  
   You can use the example file (.env.example) as a starting point:  
   cp .env.example .env  
   **Mostly used for arxiv_scrap.py and summary.py**
2. .ai.env  
   Contains AI API endpoints and model configurations such as OpenAI and Ollama.  
   Similarly, use .ai.env.example as your template:  
   cp .ai.env.example .ai.env 
    **Mostly used for aisearch.py**

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