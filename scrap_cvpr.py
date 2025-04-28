import requests
from bs4 import BeautifulSoup
import json
import datetime
import os
import time
import arxiv
from dotenv import load_dotenv, find_dotenv
from scrapt_arxiv import detect_github_repos, get_github_repo_stars
import utils.md_format as mdf
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import re




not_found=0

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def create_retry_session(retries=3):
    """Create a requests session with retry capability"""
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def scrape_cvpr_titles():
    """Scrape paper titles and basic info from CVPR website"""
    url = 'https://cvpr.thecvf.com/Conferences/2025/AcceptedPapers'
    session = create_retry_session()
    papers = []
    
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch CVPR papers: {e}")
        return papers

    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('tr')
    
    if not rows:
        logger.warning("No paper entries found. The page structure might have changed.")
        return papers

    total_papers = len([r for r in rows if r.find('strong')])
    processed = 0

    for row in rows:
        try:
            title_tag = row.find('strong')
            if not title_tag:
                continue
            
            processed += 1
            logger.info(f"Processing paper title {processed}/{total_papers}")
            
            title = title_tag.get_text(strip=True)
            authors_tag = row.find('div', class_='indented')
            authors = authors_tag.get_text(" ", strip=True) if authors_tag else ""
            
            # Only keep title and authors from web scraping
            # We'll get abstracts and other details from arXiv
            paper_details = {
                "title": title,
                "authors": authors.split(", "),
                "cvpr_scraped_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S%z")
            }
            papers.append(paper_details)
            
        except Exception as e:
            logger.error(f"Failed to process paper title: {e}")
            continue

    return papers

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
                query=f'all:"{title}"',
                max_results=10,
                sort_by=arxiv.SortCriterion.Relevance
            )
            broader_results = list(client.results(broader_search))
            
            # Match by comparing normalized titles
            for result in broader_results:
                result_normalized = normalize_title(result.title)
                # Check if titles are similar (80% match or more)
                if len(result_normalized) > 0 and len(normalized_title) > 0:
                    # Simple character-level similarity
                    similarity = sum(c1 == c2 for c1, c2 in zip(result_normalized, normalized_title)) / max(len(result_normalized), len(normalized_title))
                    if similarity > 0.8:
                        return result
        
        # Return the first result if any found from direct search
        if results:
            return results[0]
            
        # No matching paper found
        return None
    
    except Exception as e:
        logger.error(f"Error searching arXiv for '{title}': {e}")
        return None

def enhance_paper_with_arxiv(paper, arxiv_client):
    """Enhance paper details with information from arXiv"""
    title = paper['title']
    logger.info(f"Looking up '{title}' on arXiv...")
    
    # Find paper on arXiv
    arxiv_paper = find_paper_on_arxiv(title, arxiv_client)
    
    if not arxiv_paper:
        logger.warning(f"No arXiv match found for '{title}'")
        global not_found
        not_found += 1
        return paper
    
    # Enhance paper with arXiv information
    abstract = arxiv_paper.summary.replace("\n", " ")
    if arxiv_paper.comment is not None:
        abstract += "\n" + arxiv_paper.comment
    
    paper.update({
        "abstract": abstract,
        "arxiv_categories": arxiv_paper.categories,
        "arxiv_primary_category": arxiv_paper.primary_category,
        "arxiv_date": arxiv_paper.updated,
        "arxiv_link": arxiv_paper.entry_id,
        "pdf_url": arxiv_paper.pdf_url,
        "arxiv_id": arxiv_paper.entry_id.split('/')[-1]
    })
    
    # Keep original CVPR authors but add arXiv authors as reference
    paper["arxiv_authors"] = [str(author) for author in arxiv_paper.authors]
    
    return paper

def enhance_papers_with_arxiv_data(papers, batch_size=5):
    """Enhance multiple papers with arXiv data in batches"""
    arxiv_client = arxiv.Client(page_size=batch_size)
    enhanced_papers = []
    
    logger.info(f"Enhancing {len(papers)} papers with arXiv data...")
    
    for i in tqdm(range(0, len(papers), batch_size), desc="Fetching arXiv data"):
        batch = papers[i:i + batch_size]
        batch_enhanced = []
        
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = []
            for paper in batch:
                futures.append(executor.submit(
                    enhance_paper_with_arxiv, paper, arxiv_client
                ))
            
            for future in futures:
                result = future.result()
                if result:
                    batch_enhanced.append(result)
        
        enhanced_papers.extend(batch_enhanced)
        
        # Respect arXiv API rate limits
        if i + batch_size < len(papers):
            time.sleep(3)
    
    # Check how many papers were successfully enhanced
    enhanced_count = sum(1 for paper in enhanced_papers if paper.get('abstract'))
    logger.info(f"Successfully enhanced {enhanced_count}/{len(papers)} papers with arXiv data")
    
    return enhanced_papers

def scrape_cvpr_papers_pipeline():
    """Pipeline for scraping papers from CVPR and enhancing with arXiv"""
    # First get paper titles from CVPR website
    cvpr_papers = scrape_cvpr_titles()
    
    if not cvpr_papers:
        return []
    
    # Then enhance with arXiv data
    enhanced_papers = enhance_papers_with_arxiv_data(cvpr_papers)
    
    return enhanced_papers

def process_paper_analysis(paper):
    """Process analysis for a single paper"""
    try:
        # Check if paper has an abstract (from arXiv)
        if not paper.get('abstract'):
            logger.warning(f"Paper '{paper.get('title')}' has no abstract, using title only for analysis")
            text_for_processing = f"Title: {paper['title']}\n"
        else:
            text_for_processing = f"Title: {paper['title']}\nAbstract: {paper['abstract']}\n"
        
        # Retry LLM calls up to 3 times with exponential backoff
        retries = 3
        for attempt in range(retries):
            try:
                main_task = mdf.get_tasks_tags(text_for_processing)
                contributions = mdf.get_contributions(text_for_processing)
                summary = mdf.get_paper_summary(text_for_processing)
                break
            except Exception as e:
                if attempt == retries - 1:  # Last attempt
                    logger.error(f"Failed to get LLM analysis after {retries} attempts: {e}")
                    main_task = "Analysis failed"
                    contributions = "Analysis failed"
                    summary = "Analysis failed"
                time.sleep(2 ** attempt)  # Exponential backoff
        
        # Look for GitHub repos in the abstract if available
        if paper.get('abstract'):
            github_urls = detect_github_repos(paper['abstract'])
            if github_urls:
                repo_url = github_urls[0]
                try:
                    stars = get_github_repo_stars(repo_url, os.getenv("GITHUB_TOKEN"))
                    paper['repo'] = repo_url[:-1] if repo_url[-1] == "." else repo_url
                except Exception as e:
                    logger.error(f"Failed to get GitHub stars for {repo_url}: {e}")
                    stars = 0
                    paper['repo'] = "N/A"
            else:
                stars = 0
                paper['repo'] = "N/A"
        else:
            stars = 0
            paper['repo'] = "N/A"
        
        paper.update({
            "main_task": main_task,
            "contributions": contributions,
            "summary": summary,
            "stars": stars,
            "analyzed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S%z")
        })
        
        return paper
    except Exception as e:
        logger.error(f"Failed to analyze paper '{paper.get('title', 'Unknown')}': {e}")
        return None

def load_existing_analyzed_papers(output_file):
    """Load existing analyzed papers from JSON file if it exists"""
    try:
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                existing_papers = json.load(f)
            logger.info(f"Loaded {len(existing_papers)} existing analyzed papers")
            return {paper['title']: paper for paper in existing_papers}
        return {}
    except Exception as e:
        logger.error(f"Error loading existing papers: {e}")
        return {}

def filter_unanalyzed_papers(papers, existing_papers):
    """Filter out papers that have already been analyzed"""
    unanalyzed = []
    for paper in papers:
        if paper['title'] not in existing_papers:
            unanalyzed.append(paper)
    logger.info(f"Found {len(unanalyzed)} papers that need analysis")
    return unanalyzed

def save_analyzed_batch(analyzed_batch, output_file, existing_papers):
    """Save the current batch of analyzed papers"""
    try:
        # Update existing papers with new batch
        for paper in analyzed_batch:
            existing_papers[paper['title']] = paper
        
        # Convert to list for JSON serialization
        papers_list = list(existing_papers.values())
        
        # Save atomically using temporary file
        temp_file = output_file + '.tmp'
        with open(temp_file, 'w') as f:
            json.dump(papers_list, f, indent=4, default=str)
        os.replace(temp_file, output_file)
        
        logger.info(f"Saved {len(analyzed_batch)} papers, total: {len(existing_papers)}")
    except Exception as e:
        logger.error(f"Error saving analyzed batch: {e}")

def analyze_papers_pipeline(papers, output_file, batch_size=10):
    """Pipeline for analyzing papers with LLM and adding metadata"""
    # Load existing analyzed papers
    existing_papers = load_existing_analyzed_papers(output_file)
    
    # Filter out already analyzed papers
    unanalyzed_papers = filter_unanalyzed_papers(papers, existing_papers)
    if not unanalyzed_papers:
        logger.info("No new papers to analyze")
        return list(existing_papers.values())
    
    total_batches = (len(unanalyzed_papers) + batch_size - 1) // batch_size
    analyzed_papers = []
    
    for i in tqdm(range(0, len(unanalyzed_papers), batch_size), total=total_batches, desc="Analyzing papers"):
        batch = unanalyzed_papers[i:i + batch_size]
        batch_results = []
        
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = []
            for paper in batch:
                futures.append(executor.submit(process_paper_analysis, paper))
            
            for future in futures:
                result = future.result()
                if result:
                    batch_results.append(result)
        
        # Save batch results immediately
        if batch_results:
            save_analyzed_batch(batch_results, output_file, existing_papers)
            analyzed_papers.extend(batch_results)
    
    return list(existing_papers.values())

if __name__ == "__main__":
    try:
        load_dotenv(find_dotenv())
        
        if not os.getenv("ROOT_FOLDER"):
            raise ValueError("ROOT_FOLDER environment variable is not set")
        if not os.getenv("GITHUB_TOKEN"):
            logger.warning("GITHUB_TOKEN not set - GitHub star counts will not be available")
        
        root_folder = os.getenv("ROOT_FOLDER")
        output_folder = os.path.join(root_folder, "cvpr_papers")
        raw_folder = os.path.join(output_folder, "raw")
        os.makedirs(output_folder, exist_ok=True)
        os.makedirs(raw_folder, exist_ok=True)
        
        today = datetime.datetime.now().strftime("%Y%m%d")
        raw_file = os.path.join(raw_folder, f"cvpr_papers_{today}_raw.json")
        output_file = os.path.join(output_folder, f"cvpr_papers_{today}.json")
        md_file = os.path.join(output_folder, f"cvpr_papers_{today}.md")
        
        # Phase 1: Scraping and Enhancing with arXiv
        if not os.path.exists(raw_file):
            logger.info("Starting CVPR papers scraping...")
            papers = scrape_cvpr_papers_pipeline()
            if not papers:
                logger.error("No papers were successfully scraped")
                exit(1)
            
            with open(raw_file, 'w') as f:
                json.dump(papers, f, indent=4, default=str)
            logger.info(f"Scraped and enhanced {len(papers)} papers")
        
        # Phase 2: Analysis
        logger.info("Starting papers analysis...")
        with open(raw_file, 'r') as f:
            papers = json.load(f)
        
        analyzed_papers = analyze_papers_pipeline(papers, output_file)
        if not analyzed_papers:
            logger.error("No papers were successfully analyzed")
            exit(1)
        
        # Generate markdown only if needed
        if not os.path.exists(md_file):
            mdf.list_to_markdown(analyzed_papers, md_file, ai_summary=True)
            logger.info(f"Generated markdown at {md_file}")
        
        logger.info("Not found papers: {}".format(not_found))
        logger.info("Total papers: {}".format(len(analyzed_papers)))
        logger.info("Script finished successfully")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        exit(1)