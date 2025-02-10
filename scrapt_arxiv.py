import requests
import xml.etree.ElementTree as ET
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import time
import re
import arxiv
import json
import datetime
import os
from dotenv import load_dotenv, find_dotenv

def get_recent_arxiv_links_with_arxivpy(query,sort_by_choice="relevance", max_results=50):
    choice = arxiv.SortCriterion.Relevance if sort_by_choice == "relevance" else arxiv.SortCriterion.LastUpdatedDate
    client = arxiv.Client(page_size = max_results)
    query = f'all:{query}'
    start_time = time.time()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=choice,
        sort_order=arxiv.SortOrder.Descending
    )
    
    print(client._format_url(search,0,max_results))
    papers = []
    for result in client.results(search):
        
        # create a summary of the abstract in 100 words with aisuite and ollama and llama3.3

        
        abstract = result.summary.replace("\n"," ") + "\n"+ (result.comment if result.comment is not None else "")
        # Create a chat completion to summarize the abstract
        

        paper_details = {
            "title": result.title,
            "abstract": abstract,
            "acm_classifications": result.categories,
            "authors" : result.authors,
            "primary_category": result.primary_category,
            "date": result.updated,
            "link": result.entry_id
        }
        papers.append(paper_details)
    end_time = time.time()
    print(f"arxiv.py request time: {end_time - start_time} seconds")
    return papers

def get_recent_arxiv_links(query, max_results=50):
    base_url = 'http://export.arxiv.org/api/query'
    query_words = query.split()
    and_query = '+AND+'.join([f'abs:{word}' for word in query_words])
    print(and_query)
    params = {
        'search_query': f'all:{query}',# and_query,##+AND+cat:cs.CV', use "" for exact matching
        'start': 0,
        'max_results': max_results,
        'sortBy': 'lastUpdatedDate',
        'sortOrder': 'descending'
    }
    response = requests.get(base_url, params=params)
    #plot the full request
    print(response.url)
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        namespace = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        papers = []
        for entry in root.findall('atom:entry', namespace):
            title = entry.find('atom:title', namespace).text.strip().replace('\n', ' ')
            link = entry.find('atom:id', namespace).text.strip()
            abstract = entry.find('atom:summary', namespace).text.strip().replace('\n', ' ')
            date = entry.find('atom:updated', namespace).text.strip()
            # Extract ACM Classification if available
            acm_classifications = []
            for category in entry.findall('atom:category', namespace):
                term = category.attrib.get('term')
                if term and term.startswith('cs.'):
                    acm_classifications.append(term)
            primary_category_elem = entry.find('arxiv:primary_category', namespace)
            primary_category = primary_category_elem.attrib.get('term') if primary_category_elem is not None else 'N/A'
            comments = entry.find('arxiv:comment', namespace)
            comments = comments.text.strip() if comments is not None else ''




            paper_details = {
                "title": title,
                "abstract": abstract+"\n"+comments,
                "acm_classifications": acm_classifications,
                "primary_category": primary_category,
                "date": date,
                "link": link
            }
            papers.append(paper_details)
        return papers
    else:
        print(f'Error: {response.status_code}')
        return []



# def get_relevant_papers(query, papers, k=5):
#     client = ai.Client()
#     model = "ollama:your-ollama-model"
#     # model = SentenceTransformer("dunzhang/stella_en_400M_v5", trust_remote_code=True)

#     # Embed the query
#     query_embedding = client.embed(query, model=model)

#     # Embed the papers' titles and abstracts
#     paper_embeddings = []
#     for paper in papers:
#         combined_text = paper['title'] + " " + paper['abstract']
#         embedding = client.embed(combined_text, model=model)
#         paper_embeddings.append(embedding)

#     # Calculate cosine similarity
#     similarities = cosine_similarity([query_embedding], paper_embeddings).flatten()

#     # Get top K most relevant papers
#     top_k_indices = np.argsort(similarities)[-k:][::-1]
#     top_k_papers = [papers[i] for i in top_k_indices]
def get_github_repo_stars(repo_url,token):
    repo_path = re.search(r'github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)', repo_url)
    if repo_path:
        repo_path = repo_path.group(1)
        api_url = f'https://api.github.com/repos/{repo_path}'
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(api_url,headers=headers)
        if response.status_code == 200:
            repo_data = response.json()
            return repo_data['stargazers_count']
        elif response.status_code == 403:
            if response.headers.get("X-RateLimit-Remaining") == "0":
                reset_time = int(response.headers.get("X-RateLimit-Reset"))
                wait_time = max(0, reset_time - int(time.time()))
                print(f"Rate limit exceeded. Retry after {wait_time} seconds.")
                quit()
            else:
                print("Access forbidden. Check your token permissions.")
    else:
        print(f"Failed to retrieve data: {response.status_code} - {response.text}")
    return 0

def detect_github_repos(abstract):
    github_urls = re.findall(r'https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', abstract)
    return github_urls

def get_relevant_papers(query, papers):
    # model = SentenceTransformer("all-MiniLM-L6-v2")
    model = SentenceTransformer("dunzhang/stella_en_400M_v5", trust_remote_code=True)
    
    # Embed the query
    query_embedding = model.encode([query])[0]

    # Embed the papers' titles and abstracts
    paper_embeddings = []
    for paper in papers:
        combined_text = paper['title'] + " " + paper['abstract']
        embedding = model.encode([combined_text])[0]
        paper_embeddings.append(embedding)

    # Calculate cosine similarity
    similarities = cosine_similarity([query_embedding], paper_embeddings).flatten()

    # Get top K most relevant papers
    sorted_indices = np.argsort(similarities)[::-1]
    # add the score to the paper dict
    sorted_papers = [{**papers[id], 'score': similarities[id]} for id in sorted_indices]

    return sorted_papers

def filter_papers_by_date_and_category(papers, category, days=8):
    """
    Filter papers published within the last `days` days and matching the specified category.
    
    Args:
        papers (list): List of paper dictionaries.
        category (str): The primary category to filter by (e.g., 'cs.CV').
        days (int): Number of past days to include. Defaults to 7.
    
    Returns:
        list: Filtered list of papers.
    """
    filtered_papers = []
    today = datetime.datetime.now(datetime.timezone.utc)
    #put time to midnight
    today = today.replace(hour=23, minute=59, second=0, microsecond=0) 
    last_week = today - datetime.timedelta(days=days)
    
    for paper in papers:
        # Parse the publication date
        # try:
        #     pub_date = datetime.datetime.strptime(paper['date'], "%Y-%m-%dT%H:%M:%SZ")
        # except ValueError:
        #     print(f"Invalid date format for paper: {paper['title']}")
        #     continue
        if not isinstance(paper['date'], datetime.datetime):
            print(f"Invalid date type for paper: {paper['title']}")
            continue
        
        pub_date = paper['date']
        # Check if the paper is within the last week and matches the category
        if last_week <= pub_date <= today and paper['primary_category'] == category:
            filtered_papers.append(paper)
    
    return filtered_papers

def process_arxiv_papers(query, category, filter_query,negative_query,sort_by_choice, max_results=2000, days=8, score_threshold=0.6):
    """Processes a list of ArXiv papers based on the given query, category, and filter query. Filters the papers by date and category, selects the most relevant papers, and optionally filters them by a score threshold.
    
    Args:
        query (str): The search query to use for fetching the ArXiv papers.
        category (str): The primary category to filter the papers by (e.g., 'cs.CV').
        filter_query (str): An additional query to use for filtering the papers.
        max_results (int, optional): The maximum number of papers to fetch. Defaults to 2000.
        days (int, optional): The number of past days to include. Defaults to 8.
        score_threshold (float, optional): The minimum score threshold for including a paper. Defaults to 0.6.
    
    Returns:
        list: A list of relevant paper dictionaries, each containing the paper's metadata and a 'score' field indicating the relevance score.
    """
    start = time.time()
    papers = get_recent_arxiv_links_with_arxivpy(query,sort_by_choice, max_results=max_results)
    
    print("Request time : ", time.time() - start)
    print(f"Total papers fetched: {len(papers)}")
    filtered_papers = filter_papers_by_date_and_category(papers, category, days=days)
    print(f"Papers after filtering by date and category: {len(filtered_papers)}")
    
    relevant_papers = get_relevant_papers(filter_query, filtered_papers)
    print(f"Relevant papers selected: {len(relevant_papers)}")
    print("All :", time.time() - start)
    
    for paper in relevant_papers:
        github_urls = detect_github_repos(paper['abstract'])
        if github_urls:
            stars = get_github_repo_stars(github_urls[0],os.getenv("GITHUB_TOKEN"))
            if github_urls[0][-1]==".":
                paper['repo'] = github_urls[0][:-1]
            else:
                paper['repo'] = github_urls[0]
        else:
            stars = 0
            paper['repo'] = "N/A"
        paper['stars'] = stars
    
    relevant_papers = [paper for paper in relevant_papers if paper['score'] >= score_threshold]
    #remane score to score_arxiv
    for paper in relevant_papers:
        paper['positive_score'] = paper['score']
        del paper['score']
    print(f"Papers after filtering by score: {len(relevant_papers)}")

    negative_papers = get_relevant_papers(negative_query, relevant_papers)
    print("All time ", time.time() - start)
    #replace score to 1-score
    for paper in negative_papers:
        paper['negative_score'] = 1 - paper['score']
        del paper['score']

    #create a general score with normalisation with the max and min scores by addition of the 2 score

    # max_positive_score = max(paper['positive_score'] for paper in negative_papers)
    # min_positive_score = min(paper['positive_score'] for paper in negative_papers)
    # max_negative_score = max(paper['negative_score'] for paper in negative_papers)
    # min_negative_score = min(paper['negative_score'] for paper in negative_papers)

    for paper in negative_papers:
        normalized_positive = (paper['positive_score'] - score_threshold) / (1 - score_threshold)
        # normalized_negative = (paper['negative_score'] - min_negative_score) / (max_negative_score - min_negative_score) if max_negative_score != min_negative_score else 0
        paper['general_score'] = (normalized_positive + paper['negative_score'])/2





    #sort by positive_score
    negative_papers.sort(key=lambda x: x['general_score'], reverse=True)
    end = time.time()
    print("Total time :", end - start)
    return negative_papers


def parse_markdown_to_queries(markdown_file):
    """
    Parse a markdown file to extract queries, categories, filter queries, and score thresholds.
    
    Args:
        markdown_file (str): Path to the markdown file.
    
    Returns:
        list: List of dictionaries containing the extracted information.
    """
    queries = []
    with open(markdown_file, 'r') as file:
        lines = file.readlines()
    
    current_query = {}
    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            if current_query:
                queries.append(current_query)
            current_query = {"id": line[2:]}
        elif line.startswith("query ="):
            current_query["query"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("category ="):
            current_query["category"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("filter_query ="):
            current_query["filter_query"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("score_th ="):
            current_query["score_th"] = float(line.split("=", 1)[1].strip())
        elif line.startswith("negative_query ="):
            current_query["negative_query"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("sortBy ="):
            current_query["sort_by_choice"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("max_results ="):
            current_query["max_results"] = line.split("=", 1)[1].strip().strip('"')
    if current_query:
        queries.append(current_query)
    
    return queries

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Process ArXiv papers based on queries from a markdown file.')
    # add the number of days as arguments
    parser.add_argument("days",type=int, default=8, help='Number of days to consider for paper filtering.')
    args = parser.parse_args()
    days = args.days+1
    max_results= 1000
    sort_by_choice = "lastUdpated"#"relevance"
    
    load_dotenv(find_dotenv())

    root_folder=os.getenv("ROOT_FOLDER")
    queries_file= os.path.join(root_folder,os.getenv("QUERIES_FILE"))
    json_folder = os.path.join(root_folder,os.getenv("JSON_FOLDER"))
    md_folder = os.path.join(root_folder,os.getenv("MD_FOLDER"))

    ai_summary = os.getenv("AI_SUMMARY", "false").lower() == "true"


    os.makedirs(json_folder, exist_ok=True)
    os.makedirs(md_folder, exist_ok=True)


    queries = parse_markdown_to_queries(queries_file)
    print(queries)
    
    for scrap in queries:
        id = scrap['id']
        query = scrap['query']
        category = scrap['category']
        filter_query = scrap['filter_query']
        score_th = scrap['score_th']
        negative_query = scrap['negative_query']       

        if "max_results" not in scrap:
            scrap["max_results"] = max_results
        else:
            max_results = int(scrap["max_results"])
        if "sortBy" not in scrap:
            scrap["sortBy"]=sort_by_choice
        else:
            sort_by_choice = scrap["sortBy"]

        query_folder = os.path.join(json_folder,f"{id}/")
        os.makedirs(query_folder, exist_ok=True)

        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

        output_file = f'{query_folder}/{today}-{days}.json'
        print(os.path.exists(output_file))
        cfg_file = f'{query_folder}/{today}-{days}_config.json'

        if os.path.exists(cfg_file):
            with open(cfg_file, 'r') as f:
                cfg = json.load(f)
                print("cfg : ",cfg)
            if 'max_results' not in cfg:
                cfg['max_results'] = max_results
            if 'sortBy' not in cfg:
                cfg['sortBy'] = sort_by_choice

            if (cfg['query'] == query and cfg['category'] == category 
                and cfg['filter_query'] == filter_query 
                and cfg['score_th'] == score_th 
                and os.path.exists(output_file)
                and cfg['max_results'] == max_results
                and cfg['sortBy'] == sort_by_choice
                ):
                print(f"Skipping {id} as it has already been scraped today.")
            else: # create a new instance
                with open(cfg_file.replace(".json","_new.json"), 'w') as f:
                    json.dump(scrap, f, indent=4)
                out_dict = process_arxiv_papers(query, category, filter_query,sort_by_choice=sort_by_choice,negative_query=negative_query,score_threshold=score_th,max_results = max_results,days=days)
                with open(output_file.replace("_config.json","_new_config.json"), 'w') as f:
                    json.dump(out_dict, f, indent=4, default=str)
        else:
            out_dict = process_arxiv_papers(query, category, filter_query,sort_by_choice=sort_by_choice,negative_query=negative_query,score_threshold=score_th,max_results = max_results,days=days)
            with open(output_file, 'w') as f:
                json.dump(out_dict, f, indent=4, default=str)
            with  open(cfg_file, 'w') as f:
                json.dump(scrap, f, indent=4,  default=str)
        
        # Format in Markdown
        import md_format as mdf
        md_file_path = f'{md_folder}/{id}/{today}-{days}.md'
        with open(output_file, 'r') as f:
            out_dict = json.load(f)
        if os.path.exists(md_file_path):
            print(f"Skipping {id} as it has already been formatted today.")
        else:
            mdf.list_to_markdown(out_dict, md_file_path, ai_summary=ai_summary)
        

        


        

       

    # query = "human pose estimation"
    # category = "cs.CV"
    # filter_query = "human pose estimation keypoints body wholebody skeleton heatmap regression"
    # score_th= 0.6
    # out_dict = process_arxiv_papers(query, category, filter_query,score_th=score_th)
    # output_folder = "automation/weekly_arxiv_json"
    # if not os.path.exists(output_folder):
    #     os.makedirs(output_folde


       

    # query = "human pose estimation"
    # category = "cs.CV"
    # filter_query = "human pose estimation keypoints body wholebody skeleton heatmap regression"
    # score_th= 0.6
    # out_dict = process_arxiv_papers(query, category, filter_query,score_th=score_th)
    # output_folder = "automation/weekly_arxiv_json"
    # if not os.path.exists(output_folder):
    #     os.makedirs(output_folder)
    # today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    # with open(f'{output_folder}/{today}.json', 'w') as f:
    #     json.dump(out_dict, f, indent=4, default=str)

