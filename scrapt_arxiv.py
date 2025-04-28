import logging
import requests
import xml.etree.ElementTree as ET
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import time
import re
import arxiv
import datetime

# from dotenv import load_dotenv, find_dotenv
try:
    import utils.md_format as mdf
except ImportError:
    import md_format as mdf # type: ignore


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

def get_recent_arxiv_links_with_arxivpy(query, sort_by_choice="relevance", max_results=50):
    """Fetches recent ArXiv links using the arxiv library."""
    # Map string choice to arxiv library constants
    if sort_by_choice.lower() == "relevance":
        sort_criterion = arxiv.SortCriterion.Relevance
    elif sort_by_choice.lower() == "lastupdateddate":
        sort_criterion = arxiv.SortCriterion.LastUpdatedDate
    else:
        # Default or raise error for invalid choice
        logger.warning(f"Warning: Invalid sort_by_choice '{sort_by_choice}'. Defaulting to relevance.")
        sort_criterion = arxiv.SortCriterion.Relevance

    client = arxiv.Client(page_size=max_results)
    # Consider if 'all:' prefix is always desired or should be part of the input query
    # query = f'all:{query}' 
    start_time = time.time()
    search = arxiv.Search(
        query=query, # Use the query directly
        max_results=max_results,
        sort_by=sort_criterion, # Use the mapped constant
        sort_order=arxiv.SortOrder.Descending
    )
    
    logger.info(f"Fetching from ArXiv API: {client._format_url(search, 0, max_results)}")
    papers = []
    try:
        results = client.results(search)
        for result in results:
            
            # Removed placeholder comment for AI summary generation here
            # create a summary of the abstract in 100 words with aisuite and ollama and llama3.3

            
            # Combine abstract and comments safely
            abstract_content = result.summary.replace("\n", " ")
            comment_content = result.comment.replace("\n", " ") if result.comment else ""
            full_abstract = abstract_content
            if comment_content:
                full_abstract += "\n\n" + comment_content # Add comments with spacing
            
            # Use result attributes directly for clarity
            paper_details = {
                "title": result.title,
                "abstract": full_abstract,
                "acm_classifications": result.categories, # Keep as is, might not be ACM specifically
                "authors": [str(a) for a in result.authors], # Convert Author objects to strings
                "primary_category": result.primary_category,
                "date": result.updated, # Keep as datetime object
                "link": result.entry_id
            }
            papers.append(paper_details)
    except Exception as e:
        logger.error(f"Error during ArXiv search: {e}")
        # Potentially return partial results or raise the exception
        # return papers 

    end_time = time.time()
    logger.info(f"arxiv.py request time: {end_time - start_time:.2f} seconds for {len(papers)} papers.")
    return papers

def get_github_repo_stars(repo_url, token):
    """Fetches GitHub stars for a given repository URL."""
    # Improved regex to handle potential trailing slashes or .git suffixes
    match = re.search(r'github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?$', repo_url)
    if match:
        repo_path = match.group(1)
        api_url = f'https://api.github.com/repos/{repo_path}'
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json" # Best practice header
        }
        try:
            response = requests.get(api_url, headers=headers, timeout=10) # Add timeout
            response.raise_for_status() # Raise HTTPError for bad responses (4XX, 5XX)
            repo_data = response.json()
            return repo_data.get('stargazers_count', 0) # Use .get for safety
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching GitHub stars for {repo_url}: {e}")
            # Handle specific errors like rate limiting if possible
            if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 403:
                if e.response.headers.get("X-RateLimit-Remaining") == "0":
                    reset_time = int(e.response.headers.get("X-RateLimit-Reset", 0))
                    wait_time = max(0, reset_time - int(time.time()))
                    logger.info(f"GitHub rate limit exceeded. Retry after {wait_time} seconds.")
                    # Consider waiting or raising a specific exception
                else:
                    logger.error("GitHub access forbidden. Check token permissions.")
            return 0 # Return 0 on errors
    else:
        logger.error(f"Invalid GitHub URL format: {repo_url}")
        return 0

def detect_github_repos(text): # Renamed parameter for clarity
    """Detects GitHub repository URLs within a given text."""
    # Regex to find standard GitHub repo URLs
    github_urls = re.findall(r'https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', text)
    # Remove potential trailing characters like periods often found in abstracts
    cleaned_urls = [url.rstrip('./') for url in github_urls]
    return list(set(cleaned_urls)) # Return unique URLs

def get_relevant_papers(query, papers, embedding_model_name="mixedbread-ai/mxbai-embed-large-v1"):
    """Calculates relevance scores for papers based on a query using sentence transformers."""
    try:
        # Load the model dynamically
        model = SentenceTransformer(embedding_model_name, trust_remote_code=True)
    except Exception as e:
        logger.error(f"Error loading sentence transformer model '{embedding_model_name}': {e}. Using default.")
        # Fallback to a default model if loading fails
        try:
            default_model = "all-MiniLM-L6-v2"
            model = SentenceTransformer(default_model)
            embedding_model_name = default_model # Update name if fallback is used
        except Exception as fallback_e:
             logger.error(f"Error loading default sentence transformer model: {fallback_e}")
             return [] # Return empty list if models cannot be loaded

    logger.info(f"Using embedding model: {embedding_model_name}")
    
    # Embed the query
    query_embedding = model.encode([query])[0]

    # Embed the papers' titles and abstracts
    paper_embeddings = []
    texts_to_embed = []
    for paper in papers:
        # Ensure abstract exists and is a string
        abstract = paper.get('abstract', '') 
        if not isinstance(abstract, str):
             abstract = str(abstract) # Attempt conversion if not string
        # Combine title and abstract for embedding
        combined_text = paper.get('title', '') + " " + abstract 
        texts_to_embed.append(combined_text)

    if not texts_to_embed:
        return [] # No valid text found in papers

    # Encode all paper texts in a batch for efficiency
    paper_embeddings = model.encode(texts_to_embed)

    # Calculate cosine similarity
    similarities = cosine_similarity([query_embedding], paper_embeddings).flatten()

    # Add the score to the paper dict and sort
    scored_papers = []
    for i, paper in enumerate(papers):
        paper_copy = paper.copy() # Avoid modifying original dicts
        paper_copy['score'] = float(similarities[i]) # Ensure score is float
        scored_papers.append(paper_copy)

    # Sort by score descending
    sorted_papers = sorted(scored_papers, key=lambda x: x['score'], reverse=True)

    return sorted_papers

def filter_papers_by_date_and_category(papers, category, days=8):
    """
    Filter papers published within the last `days` days and matching the specified primary category.
    
    Args:
        papers (list): List of paper dictionaries.
        category (str): The primary category to filter by (e.g., 'cs.CV').
        days (int): Number of past days to include. Defaults to 8.
    
    Returns:
        list: Filtered list of papers.
    """
    filtered_papers = []
    # Ensure today is timezone-aware (UTC)
    today = datetime.datetime.now(datetime.timezone.utc)
    # Set time to end of day for comparison
    today = today.replace(hour=23, minute=59, second=59, microsecond=999999) 
    cutoff_date = today - datetime.timedelta(days=days)
    
    logger.info(f"Filtering papers from {cutoff_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')} in category '{category}'")

    for paper in papers:
        pub_date = paper.get('date') # Get date from paper dict
        primary_cat = paper.get('primary_category')

        # Validate date type (should be datetime object from arxiv.py)
        if not isinstance(pub_date, datetime.datetime):
            # Attempt to parse if it's a string (fallback, though unlikely with arxiv.py)
            if isinstance(pub_date, str):
                try:
                    pub_date = datetime.datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
                except ValueError:
                    logger.warning(f"Invalid date format '{pub_date}' for paper: {paper.get('title', 'N/A')}")
                    continue # Skip paper if date is invalid
            else:
                logger.warning(f"Invalid date type ({type(pub_date)}) for paper: {paper.get('title', 'N/A')}")
                continue # Skip paper if date is invalid

        # Ensure pub_date is timezone-aware for comparison
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=datetime.timezone.utc) # Assume UTC if no timezone
        
        # Check if the paper is within the date range and matches the category
        if cutoff_date <= pub_date <= today and primary_cat == category:
            filtered_papers.append(paper)
    
    logger.info(f"Found {len(filtered_papers)} papers matching date and category criteria.")
    return filtered_papers

def scrape_arxiv_papers_pipeline(query, category, sort_by_choice="lastUpdatedDate", max_results=50, days=8):
    """Pipeline for scraping and filtering papers from ArXiv."""
    logger.info(f"\n--- Starting Scrape Pipeline for category '{category}' ---")
    logger.info(f"Query: '{query}', Sort: '{sort_by_choice}', Max Results: {max_results}, Days: {days}")
    start_time = time.time()
    # Use the refined function name
    papers = get_recent_arxiv_links_with_arxivpy(query, sort_by_choice, max_results=max_results)
    filtered_papers = filter_papers_by_date_and_category(papers, category, days=days)
    end_time = time.time()
    logger.info(f"--- Scrape Pipeline finished in {end_time - start_time:.2f} seconds ---")
    return filtered_papers

def analyze_papers_pipeline(papers, filter_query, negative_query, score_threshold=0.6, embedding_model_name="mixedbread-ai/mxbai-embed-large-v1", github_token=None):
    """Pipeline for analyzing, scoring, and enriching papers."""
    logger.info(f"\n--- Starting Analysis Pipeline ---")
    logger.info(f"Positive Query: '{filter_query}', Negative Query: '{negative_query}', Threshold: {score_threshold}")
    start_time = time.time()

    if not papers:
        logger.warning("No papers provided for analysis. Skipping.")
        return []
        
    # Get relevance scores based on the positive filter query
    relevant_papers = get_relevant_papers(filter_query, papers, embedding_model_name)
    logger.info(f"Calculated positive scores for {len(relevant_papers)} papers.")
    
    # Filter by positive score threshold first
    relevant_papers = [paper for paper in relevant_papers if paper.get('score', 0) >= score_threshold]
    logger.info(f"{len(relevant_papers)} papers remaining after positive score threshold ({score_threshold}).")

    if not relevant_papers:
        logger.info("No papers met the positive score threshold. Analysis stopped.")
        return []

    # Rename positive score and add GitHub info
    processed_papers = []
    if github_token is None:
         logger.warning("Warning: GITHUB_TOKEN not provided. Cannot fetch star counts.")
    for paper in relevant_papers:
        paper['positive_score'] = paper.pop('score') # Rename score to positive_score
        github_urls = detect_github_repos(paper.get('abstract', ''))
        paper['repo'] = "N/A"
        paper['stars'] = 0
        if github_urls:
            # Usually, the first detected repo is the most relevant
            repo_url = github_urls[0]
            paper['repo'] = repo_url 
            if github_token:
                 stars = get_github_repo_stars(repo_url, github_token)
                 paper['stars'] = stars
            else:
                 paper['stars'] = -1 # Indicate stars couldn't be fetched
        processed_papers.append(paper)
        
    logger.info(f"Added GitHub info (stars require GITHUB_TOKEN).")

    # Calculate negative scores for the filtered papers
    # We pass processed_papers which now have 'positive_score' but no 'score' key
    # get_relevant_papers calculates 'score' based on the negative_query
    negative_scored_papers = get_relevant_papers(negative_query, processed_papers, embedding_model_name)
    logger.info(f"Calculated negative scores for {len(negative_scored_papers)} papers.")

    # Process scores and calculate general score
    final_papers = []
    for paper in negative_scored_papers:
        # The 'score' key now holds the similarity to the *negative* query
        neg_similarity = paper.pop('score') 
        paper['negative_score'] = 1.0 - neg_similarity # Lower similarity to negative is better
        
        # Ensure positive_score exists before calculation
        positive_score = paper.get('positive_score', score_threshold) # Default to threshold if missing?
        negative_score = paper.get('negative_score', 0) # Default to 0 if missing
        
        # Simple average for general score (alternative normalizations commented out)
        paper['general_score'] = (positive_score + negative_score) / 2
        final_papers.append(paper)
        
    logger.info(f"Calculated general scores.")
    
    # Sort by general score
    final_papers.sort(key=lambda x: x.get('general_score', 0), reverse=True)
    
    end_time = time.time()
    logger.info(f"--- Analysis Pipeline finished in {end_time - start_time:.2f} seconds ---")
    return final_papers

def parse_markdown_to_queries(markdown_file):
    """
    Parse a markdown file to extract query configurations.
    Expects sections starting with # ID, containing key = "value" pairs.
    
    Args:
        markdown_file (str): Path to the markdown file.
    
    Returns:
        list: List of dictionaries containing the extracted information.
             Returns empty list if file not found or parsing error.
    """
    queries = []
    current_query = None # Use None to indicate no active query section
    
    try:
        with open(markdown_file, 'r', encoding='utf-8') as file: # Specify encoding
            lines = file.readlines()
    except FileNotFoundError:
        logger.error(f"Error: Queries file not found at '{markdown_file}'")
        return []
    except Exception as e:
         logger.error(f"Error reading queries file '{markdown_file}': {e}")
         return []

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('//') or line.startswith('/*'): # Skip empty lines and comments
             continue

        if line.startswith("# "):
            if current_query: # Save the previous query block if exists
                queries.append(current_query)
            current_query = {"id": line[2:].strip()} # Start a new query block
        elif current_query is not None and '=' in line:
            # Split only on the first equals sign
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"') # Remove leading/trailing quotes/spaces
            
            # Basic type conversion (can be extended)
            if key in ["score_th"]:
                try:
                    current_query[key] = float(value)
                except ValueError:
                     logger.warning(f"Warning: Invalid float value '{value}' for key '{key}' in query '{current_query.get('id', 'Unknown')}' at line {line_num}. Skipping.")
            elif key in ["max_results", "days"]:
                 try:
                     current_query[key] = int(value)
                 except ValueError:
                     logger.warning(f"Warning: Invalid integer value '{value}' for key '{key}' in query '{current_query.get('id', 'Unknown')}' at line {line_num}. Skipping.")
            else:
                current_query[key] = value # Store as string otherwise
        elif line and current_query is None:
             logger.warning(f"Warning: Found content outside a query block at line {line_num}: '{line}'")

    if current_query: # Add the last query block
        queries.append(current_query)
    
    logger.info(f"Parsed {len(queries)} query configurations from '{markdown_file}'.")
    return queries

if __name__ == "__main__":
    import argparse
        # Load .env variables first
    from dotenv import load_dotenv, find_dotenv
    import os
    import json
    parser = argparse.ArgumentParser(description='Scrape and analyze ArXiv papers based on queries from a markdown file.')
    # Make days argument optional with a default
    parser.add_argument("--days", type=int, default=8, help='Number of past days to fetch papers from (default: 8).')
    # Add arguments for file paths, allowing overrides via command line
    parser.add_argument("--queries_file", type=str, default=None, help="Path to the markdown queries file.")
    parser.add_argument("--root_folder", type=str, default=None, help="Root directory for data and output.")
    parser.add_argument("--json_folder", type=str, default="automation/weekly_arxiv_json", help="Subdirectory for JSON outputs relative to root folder.")
    parser.add_argument("--md_folder", type=str, default="Weekly Letter", help="Subdirectory for Markdown outputs relative to root folder.")
    parser.add_argument("--raw_subfolder", type=str, default="raw", help="Subdirectory within json_folder for raw scraped data.")
    parser.add_argument("--ai_summary", type=str, default="true", help="Generate AI summary for papers (true/false).")
    parser.add_argument("--embedding_model", type=str, default=None, help="Name of the sentence-transformer model for embeddings.")

    args = parser.parse_args()
    

    load_dotenv(find_dotenv())
    

    # Determine configuration values: Command line > Environment variable > Default
    days_to_fetch = args.days
    ai_summary_enabled = args.ai_summary.lower() == "true"
    
    root_folder = args.root_folder or os.getenv("ROOT_FOLDER")
    if not root_folder:
         logger.error("Error: ROOT_FOLDER is not set via command line (--root_folder) or .env file. Exiting.")
         exit(1)
         
    queries_file_path = args.queries_file or os.path.join(root_folder, os.getenv("QUERIES_FILE", "queries.md")) # Default filename if env var missing
    json_folder_path = os.path.join(root_folder, args.json_folder or os.getenv("JSON_FOLDER", "automation/weekly_arxiv_json"))
    md_folder_path = os.path.join(root_folder, args.md_folder or os.getenv("MD_FOLDER", "Weekly Letter"))
    raw_folder_path = os.path.join(json_folder_path, args.raw_subfolder or "raw")
    embedding_model = args.embedding_model or os.getenv("EMBEDDING_MODEL", "mixedbread-ai/mxbai-embed-large-v1") # Get model from env or default
    github_token = os.getenv("GITHUB_TOKEN") # Needed for star fetching

    logger.info("--- Configuration ---")
    logger.info(f"Days to fetch: {days_to_fetch}")
    logger.info(f"AI Summary Generation: {ai_summary_enabled}")
    logger.info(f"Root Folder: {root_folder}")
    logger.info(f"Queries File: {queries_file_path}")
    logger.info(f"JSON Output Folder: {json_folder_path}")
    logger.info(f"Markdown Output Folder: {md_folder_path}")
    logger.info(f"Raw Data Folder: {raw_folder_path}")
    logger.info(f"Embedding Model: {embedding_model}")
    logger.info(f"GitHub Token Loaded: {'Yes' if github_token else 'No'}")
    logger.info("---------------------")

    # Create necessary directories
    os.makedirs(json_folder_path, exist_ok=True)
    os.makedirs(md_folder_path, exist_ok=True)
    os.makedirs(raw_folder_path, exist_ok=True)
    
    # Parse queries from the specified file
    query_configs = parse_markdown_to_queries(queries_file_path)
    if not query_configs:
         logger.error("No valid query configurations found. Exiting.")
         exit(1)
         
    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    date_tag = f"{today_str}-D{days_to_fetch}" # Use a more descriptive tag including days
    
    # --- Phase 1: Scraping --- 
    logger.info("\n=== Starting Phase 1: Scraping ArXiv ===")
    for config in query_configs:
        query_id = config.get('id')
        if not query_id:
             logger.warning("Warning: Found query block without an ID. Skipping.")
             continue
        
        logger.info(f"\nProcessing query ID: {query_id}")
        query = config.get('query')
        category = config.get('category')
        if not query or not category:
            logger.warning(f"Warning: Query '{query_id}' is missing 'query' or 'category'. Skipping scrape.")
            continue
            
        max_r = config.get("max_results", 1000) # Use parsed int or default
        sort_by = config.get("sort_by_choice", "lastUpdatedDate") # Use parsed string or default
        
        # Define paths for this query
        query_raw_folder = os.path.join(raw_folder_path, query_id)
        os.makedirs(query_raw_folder, exist_ok=True)
        raw_output_file = os.path.join(query_raw_folder, f'{date_tag}_raw.json')
        
        if not os.path.exists(raw_output_file):
            logger.info(f"Raw data file not found for {query_id} ({date_tag}). Scraping...")
            try:
                # Pass parameters correctly
                scraped_papers = scrape_arxiv_papers_pipeline(
                    query=query,
                    category=category,
                    sort_by_choice=sort_by,
                    max_results=max_r,
                    days=days_to_fetch
                )
                # Save raw data
                with open(raw_output_file, 'w', encoding='utf-8') as f:
                    # Use default=str for datetime objects
                    json.dump(scraped_papers, f, indent=4, default=str) 
                logger.info(f"Scraped and saved {len(scraped_papers)} papers for '{query_id}' to {raw_output_file}")
            except Exception as e:
                logger.error(f"Error scraping papers for '{query_id}': {e}")
                continue # Continue to next query on error
        else:
             logger.info(f"Raw data file already exists for {query_id} ({date_tag}). Skipping scrape.")
    
    # --- Phase 2: Analysis --- 
    logger.info("\n=== Starting Phase 2: Analyzing Papers ===")
    for config in query_configs:
        query_id = config.get('id')
        if not query_id:
             continue # Skip blocks without ID

        logger.info(f"\nProcessing analysis for query ID: {query_id}")
        filter_q = config.get('filter_query')
        negative_q = config.get('negative_query')
        score_t = config.get('score_th', 0.6) # Use parsed float or default
        
        if not filter_q or not negative_q:
             logger.warning(f"Warning: Query '{query_id}' is missing 'filter_query' or 'negative_query'. Skipping analysis.")
             continue

        # Define paths for this query
        query_raw_folder = os.path.join(raw_folder_path, query_id)
        query_json_folder = os.path.join(json_folder_path, query_id)
        query_md_folder = os.path.join(md_folder_path, query_id)
        os.makedirs(query_json_folder, exist_ok=True)
        os.makedirs(query_md_folder, exist_ok=True)
        
        raw_input_file = os.path.join(query_raw_folder, f'{date_tag}_raw.json')
        analyzed_output_file = os.path.join(query_json_folder, f'{date_tag}_analyzed.json') # Changed filename
        config_output_file = os.path.join(query_json_folder, f'{date_tag}_config.json') # Changed filename
        md_output_file = os.path.join(query_md_folder, f'{date_tag}.md')
        
        # Check if raw input exists and analyzed output doesn't
        if os.path.exists(raw_input_file) and not os.path.exists(analyzed_output_file):
            logger.info(f"Analyzed file not found for {query_id} ({date_tag}). Analyzing raw data...")
            try:
                # Load raw papers
                with open(raw_input_file, 'r', encoding='utf-8') as f:
                    raw_papers = json.load(f)
                
                # Convert date strings back to datetime objects if needed for analysis 
                # (filter_papers_by_date needs datetime objects)
                # This assumes dates were saved as strings. If saved differently, adjust.
                for paper in raw_papers:
                     if isinstance(paper.get('date'), str):
                          try:
                               # Try parsing common formats, assuming UTC
                               # Add the format seen in the logs: YYYY-MM-DD HH:MM:SS+TZ
                               paper['date'] = datetime.datetime.strptime(paper['date'], "%Y-%m-%d %H:%M:%S%z")
                          except ValueError:
                               try:
                                    paper['date'] = datetime.datetime.strptime(paper['date'], "%Y-%m-%dT%H:%M:%S.%f%z")
                               except ValueError:
                                    try:
                                         paper['date'] = datetime.datetime.strptime(paper['date'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
                                    except ValueError:
                                         logger.warning(f"Warning: Could not parse date string '{paper.get('date')}' back to datetime for {paper.get('title')}")
                                         paper['date'] = None # Or handle as error
                                    
                # Filter out papers with invalid dates before analysis
                papers_to_analyze = [p for p in raw_papers if isinstance(p.get('date'), datetime.datetime)]
                if len(papers_to_analyze) < len(raw_papers):
                    logger.warning(f"Warning: Skipped {len(raw_papers) - len(papers_to_analyze)} papers due to invalid date format during analysis loading.")

                if not papers_to_analyze:
                     logger.warning(f"No valid papers to analyze for {query_id} after date parsing.")
                     continue
                     
                # Call the analysis pipeline
                analyzed_papers = analyze_papers_pipeline(
                    papers=papers_to_analyze,
                    filter_query=filter_q,
                    negative_query=negative_q,
                    score_threshold=score_t,
                    embedding_model_name=embedding_model, # Pass the model name
                    github_token=github_token # Pass the token
                )
                
                # Save analyzed data
                with open(analyzed_output_file, 'w', encoding='utf-8') as f:
                    json.dump(analyzed_papers, f, indent=4, default=str) # Save with dates as strings
                # Save the config used for this analysis run
                with open(config_output_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, default=str)
                logger.info(f"Analyzed {len(analyzed_papers)} papers for '{query_id}' and saved to {analyzed_output_file}")
                
            except Exception as e:
                logger.error(f"Error analyzing papers for '{query_id}': {e}")

                continue # Continue to next query on error
        elif not os.path.exists(raw_input_file):
             logger.info(f"Raw input file {raw_input_file} not found. Skipping analysis for {query_id}.")
        else: # Analyzed file already exists
             logger.info(f"Analyzed file already exists for {query_id} ({date_tag}). Skipping analysis.")
             
        # --- Generate Markdown (if analysis was successful or already existed) --- 
        if os.path.exists(analyzed_output_file) and not os.path.exists(md_output_file):
             logger.info(f"Generating Markdown report for {query_id} ({date_tag})...")
             try:
                 with open(analyzed_output_file, 'r', encoding='utf-8') as f:
                     papers_for_md = json.load(f)
                 # Call markdown generation function from md_format module
                 mdf.list_to_markdown(papers_for_md, md_output_file, ai_summary=ai_summary_enabled)
                 logger.info(f"Markdown report generated: {md_output_file}")
             except Exception as e:
                  logger.error(f"Error generating Markdown for '{query_id}': {e}")

        elif not os.path.exists(analyzed_output_file):
             logger.info(f"Analyzed file {analyzed_output_file} not found. Cannot generate Markdown for {query_id}.")
        else:
             logger.info(f"Markdown file already exists for {query_id} ({date_tag}). Skipping generation.")

    logger.info("\n=== Script finished ===")

