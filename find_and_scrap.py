#!/usr/bin/env python3
import os
import re
import json
import datetime
import time
import arxiv
import argparse
from dotenv import load_dotenv, find_dotenv
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import utils.md_format as mdf
from scrapt_arxiv import detect_github_repos, get_github_repo_stars
import logging
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def parse_markdown_titles(md_file):
    """
    Extract paper titles from a markdown file with the format:
    - PaperTitle1 - PaperTitle2 - etc.
    
    Args:
        md_file: Path to the markdown file
        
    Returns:
        List of paper titles
    """
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for titles in the format specified
        # Assuming each title is on a new line after a dash or hyphen
        titles = []
        
        # First look for the format section
        format_section = re.search(r'<format>(.*?)<\\format>', content, re.DOTALL)
        if format_section:
            format_content = format_section.group(1).strip()
            # Extract titles from the format section
            title_pattern = r'- (.*?)(?= - |$)'
            titles = re.findall(title_pattern, format_content)
        else:
            # If no format section, try to find titles line by line
            lines = content.split('\n')
            for line in lines:
                if line.startswith('- '):
                    title_parts = line[2:].split(' - ')
                    titles.extend([part.strip() for part in title_parts])
        
        # Remove any empty titles
        titles = [title for title in titles if title.strip()]
        
        return titles
    except Exception as e:
        logger.error(f"Error parsing markdown file: {e}")
        return []

def normalize_title(title):
    """Normalize title for better matching with arXiv"""
    # Remove special characters, lowercase, etc.
    title = re.sub(r'[^\w\s]', '', title.lower())
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def find_paper_on_arxiv(title, client, max_results=5):
    """Find paper on arXiv by title"""
    # Prepare search query with the title
    normalized_title = normalize_title(title)
    search_query = f'ti:"{title}"'
    
    # Configure search
    search = arxiv.Search(
        query=search_query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    try:
        # Search for papers
        results = list(client.results(search))
        
        # If direct title search fails, try with normalized titles for comparison
        if not results:
            # Try a more general search
            broader_search = arxiv.Search(
                query=f'all:{title}',
                max_results=10,
                sort_by=arxiv.SortCriterion.Relevance
            )
            broader_results = list(client.results(broader_search))
            
            # Match by comparing titles using semantic similarity with SentenceTransformer
            if broader_results:
                # Initialize sentence transformer model (only once)
                model = SentenceTransformer("dunzhang/stella_en_400M_v5", trust_remote_code=True)
                
                # Encode the query title
                title_embedding = model.encode([normalized_title])[0]
                
                # Encode all result titles and calculate similarities
                result_titles = [normalize_title(result.title) for result in broader_results]
                result_embeddings = model.encode(result_titles)
                
                # Calculate cosine similarity between query and each result
                similarities = cosine_similarity([title_embedding], result_embeddings).flatten()
                
                # Find the result with the highest similarity score
                best_match_idx = np.argmax(similarities)
                best_similarity = similarities[best_match_idx]
                logger.warning(f"Found semantic match for '{title}' with similarity {best_similarity:.2f}")

                # Return the best match if the similarity exceeds threshold
                if best_similarity > 0.75:
                    # logger.warning(f"Found semantic match for '{title}' with similarity {best_similarity:.2f}")
                    return broader_results[best_match_idx]
            else:
                logger.warning(f"No results found for broader search with '{title}'")
        # Return the first result if any found from direct search
        if results:
            return results[0]
            
        # No matching paper found
        return None
    
    except Exception as e:
        logger.error(f"Error searching arXiv for '{title}': {e}")
        return None

def process_paper(title, arxiv_client):
    """Process a single paper: find on arXiv and extract details"""
    logger.info(f"Looking up '{title}' on arXiv...")
    arxiv_paper = find_paper_on_arxiv(title, arxiv_client)
    
    if not arxiv_paper:
        logger.warning(f"No arXiv match found for '{title}'")
        return {
            "title": title,
            "not_found": True,
            "processed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S%z")
        }
    
    # Create paper dictionary with arXiv information
    paper = {
        "title": arxiv_paper.title,
        "abstract": arxiv_paper.summary.replace("\n", " "),
        "authors": [str(author) for author in arxiv_paper.authors],
        "arxiv_categories": arxiv_paper.categories,
        "arxiv_primary_category": arxiv_paper.primary_category,
        "date": arxiv_paper.updated.strftime("%Y-%m-%d %H:%M:%S%z"),
        "link": arxiv_paper.entry_id,
        "pdf_url": arxiv_paper.pdf_url,
        "arxiv_id": arxiv_paper.entry_id.split('/')[-1],
        "processed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S%z"),
        "not_found": False
    }
    
    # Check for GitHub repo in abstract
    if arxiv_paper.comment:
        paper["abstract"] += "\n" + arxiv_paper.comment
        
    github_urls = detect_github_repos(paper["abstract"])
    if github_urls:
        repo_url = github_urls[0]
        try:
            stars = get_github_repo_stars(repo_url, os.getenv("GITHUB_TOKEN"))
            paper['repo'] = repo_url[:-1] if repo_url[-1] == "." else repo_url
            paper['stars'] = stars
        except Exception as e:
            logger.error(f"Failed to get GitHub stars for {repo_url}: {e}")
            paper['repo'] = repo_url[:-1] if repo_url[-1] == "." else repo_url
            paper['stars'] = 0
    else:
        paper['repo'] = "N/A"
        paper['stars'] = 0
    
    return paper

def analyze_paper(paper):
    """Use LLM to analyze a paper's content"""
    if paper.get('not_found', True):
        return paper
    
    try:
        text_for_processing = f"Title: {paper['title']}\nAbstract: {paper['abstract']}\n"
        
        # Add LLM-based analysis
        paper['main_task'] = mdf.get_tasks_tags(text_for_processing)
        paper['contributions'] = mdf.get_contributions(text_for_processing)
        paper['summary'] = mdf.get_paper_summary(text_for_processing)
        paper['analyzed_at'] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S%z")
        
        return paper
    except Exception as e:
        logger.error(f"Failed to analyze paper '{paper.get('title', 'Unknown')}': {e}")
        paper['analysis_error'] = str(e)
        return paper

def process_papers_in_batches(titles, batch_size=5):
    """Process papers in batches to respect API rate limits"""
    arxiv_client = arxiv.Client(page_size=batch_size)
    processed_papers = []
    not_found_count = 0
    
    logger.info(f"Processing {len(titles)} paper titles in batches of {batch_size}...")
    
    for i in tqdm(range(0, len(titles), batch_size), desc="Fetching papers from arXiv"):
        batch = titles[i:i + batch_size]
        batch_results = []
        
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = []
            for title in batch:
                futures.append(executor.submit(
                    process_paper, title, arxiv_client
                ))
            
            for future in futures:
                result = future.result()
                if result:
                    batch_results.append(result)
        
        processed_papers.extend(batch_results)
        not_found_count += sum(1 for paper in batch_results if paper.get('not_found', True))
        
        # Respect arXiv API rate limits
        if i + batch_size < len(titles):
            time.sleep(3)
    
    logger.info(f"Found {len(processed_papers) - not_found_count} papers out of {len(titles)}")
    
    # Now analyze found papers
    analyzed_papers = []
    
    for i in tqdm(range(0, len(processed_papers), batch_size), desc="Analyzing papers"):
        batch = processed_papers[i:i + batch_size]
        
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = []
            for paper in batch:
                futures.append(executor.submit(analyze_paper, paper))
            
            for future in futures:
                result = future.result()
                if result:
                    analyzed_papers.append(result)
                    
        # Give the LLM API a short break between batches
        if i + batch_size < len(processed_papers):
            time.sleep(1)
    
    return analyzed_papers

def main():
    parser = argparse.ArgumentParser(description='Process paper titles from a markdown file.')
    parser.add_argument('md_file', help='Path to the markdown file with paper titles')
    parser.add_argument('--output', '-o', help='Output path (default: [input_filename]_analyzed.json)')
    parser.add_argument('--batch-size', '-b', type=int, default=5, help='Batch size for processing papers')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv(find_dotenv())
    
    # Check for GitHub token (optional but recommended)
    if not os.getenv("GITHUB_TOKEN"):
        logger.warning("GITHUB_TOKEN not set - GitHub star counts will not be accurate")
    
    md_file = args.md_file
    if not os.path.exists(md_file):
        logger.error(f"Markdown file not found: {md_file}")
        exit(1)
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        base_name = os.path.splitext(os.path.basename(md_file))[0]
        output_path = f"{base_name}_analyzed"
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else "."
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse titles from markdown
    paper_titles = parse_markdown_titles(md_file)
    if not paper_titles:
        logger.error("No paper titles found in the markdown file")
        exit(1)
    
    logger.info(f"Found {len(paper_titles)} paper titles to process")
    
    # Process papers
    papers = process_papers_in_batches(paper_titles, args.batch_size)
    
    # Save results to JSON
    json_output = f"{output_path}.json"
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=4, default=str)
    logger.info(f"Saved paper data to {json_output}")
    
    # Generate markdown from processed papers
    md_output = f"{output_path}.md"
    mdf.list_to_markdown(papers, md_output, ai_summary=True)
    logger.info(f"Generated markdown at {md_output}")
    
    # Print summary
    found_papers = sum(1 for paper in papers if not paper.get('not_found', True))
    logger.warning(f"Summary: Successfully processed {found_papers} out of {len(paper_titles)} papers")
    
if __name__ == "__main__":
    main()