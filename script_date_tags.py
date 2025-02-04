

import os
import requests
import aisuite as ai
from dotenv import load_dotenv, find_dotenv
import time
import json
from tqdm import *



def list_pdf_files(directory):
    pdf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files


def get_paper_details(query, semantic_scholar_api_key=None):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "fields": "title,authors,citationCount,year,paperId,abstract",
        "limit": 1
    }
    headers = {"x-api-key": semantic_scholar_api_key} if semantic_scholar_api_key else {}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json().get("data", [])
        return data[0] if data else -1
    else:
        print(f"Semantic Scholar API request failed: {response.status_code} {response.text}")
        return None


def generate_tags(abstract, existing_tags,rules,verbose=False,prompt=None,system=None):
    # Initialize the aisuite client
    client = ai.Client()
    if system is None:
        system = "You are a specialist in computer vision. You will reason step by step to find the best tags relevant to the abstract you will be given."
    if prompt is None:
        prompt = f"""
                Given the following abstract and existing tags, generate additional relevant tags for the paper.
                You will write only the output in the expected format and not anything else.
                Follow these rules:
                {rules}

                Abstract:
                {abstract}

                Existing Tags:
                {', '.join(existing_tags)}

                Format (json):
                [type_tag, archi_tag, task_tag]

                Generate tags : 
                """


    messages=[
        {"role": "system",
         "content": system },
        {"role": "user",
          "content": prompt}
    ]
    # print(messages)

    start_time = time.time()

    response = client.chat.completions.create(
            model="openai:gpt-4o-2024-11-20",
            messages=messages,
            temperature=0.5,
            # response_format=list,
        )
    
    final_tags_json = response.choices[0].message.content
    if verbose:
        time_taken = time.time() - start_time
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        print(f"Time taken: {time_taken:.2f} seconds")
        print(f"Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}")
   
    final_tags = json.loads("["+final_tags_json.split("[")[1].split("]")[0]+"]")
   
    return list(final_tags)


def process_pdf(path,rules,tags):
    print(f"Processing {path}...")
    paper_name = os.path.basename(path)[:-4].replace("_"," ")
    paper_details = get_paper_details(paper_name)

    #get info from semantic scholar

    if paper_details is None:
        while paper_details is None:
            print("Waiting semantic scholar api")
            time.sleep(3)
            paper_details=get_paper_details(paper_name)
    if paper_details ==-1:
        paper_details = {
            "title": paper_name,
            "authors": "",
            "citationCount": 0,
            "year": 0,
            "paperId": "",
            "abstract": ""
        }
        return {
            "title" : paper_name,
            "authors": "Unknown",
            "citation_count": "Unknown",
            "year": "Unknown",
            "paper_id": "Unknown",
            "tags": [],
            "source" :path
        }
    # print(paper_details)
    # get the tags based on the abstract
    detected_tags = generate_tags(paper_details['abstract'], tags,rules)

    final_dict = {
        "title" : paper_details['title'],
        "authors": ", ".join(author['name'] for author in paper_details['authors']),
        "citation_count": paper_details['citationCount'],
        "year": paper_details['year'],
        "paper_id": paper_details['paperId'],
        "tags": detected_tags,
        "source" : path
    }
    # print(final_dict)
    return final_dict




#format to markdown with a process of double.
def filter_papers(output_listy):
    """
    Filters papers into a list without duplicates and a list of removed duplicates based on 'paper_id'.
    Provides metrics on the number of unique and duplicate papers.

    Args:
        output_listy (list): List of paper dictionaries.

    Returns:
        tuple: (filtered_papers, removed_duplicates, metrics)
    """
    paper_id_seen = {}
    filtered_papers = []
    removed_duplicates = []

    for paper in output_listy:
        paper_id = paper.get('paper_id')
        if paper_id:
            if paper_id not in paper_id_seen:
                paper_id_seen[paper_id] = True
                filtered_papers.append(paper)
            else:
                removed_duplicates.append(paper)
        else:
            filtered_papers.append(paper)  # Include papers without a paper_id

    num_unique = len(filtered_papers)
    num_duplicates = len(removed_duplicates)

    metrics = {
        "unique_papers": num_unique,
        "duplicate_papers": num_duplicates
    }

    return filtered_papers, removed_duplicates, metrics


def create_markdown(output_listy):
    """

        1. Separate papers into two groups: known and unknown years.
        2. Sort known papers by year in descending order and citation_count in descending order.
        3. Group known papers by year.
        4. Generate markdown for known papers, grouping them by year and sorting them by citation_count.
        5. Generate markdown for unknown papers if any.
        6. Combine the markdown for known and unknown papers.
    
    """

    from collections import defaultdict

    # Separate papers with known and unknown years
    known_papers = []
    unknown_papers = []

    for paper in output_listy:
        year = paper.get('year')
        if isinstance(year, int):
            known_papers.append(paper)
        else:
            unknown_papers.append(paper)

    # Sort known papers by year descending and citation_count descending
    sorted_known = sorted(known_papers, key=lambda x: (-x['year'], -x['citation_count']))

    # Group known papers by year
    grouped_papers = defaultdict(list)
    for paper in sorted_known:
        grouped_papers[paper['year']].append(paper)

    # Generate markdown for known papers
    markdown_lines = []
    for year in sorted(grouped_papers.keys(), reverse=True):
        markdown_lines.append(f"# {year}")
        for paper in grouped_papers[year]:
            tags_formatted = ' '.join(f"#{tag}" for tag in paper['tags'])
            markdown_lines.append(f"- [ ] [[{paper['source']}|{paper['title']}]] : {paper['citation_count']} citations, {paper['year']}, {tags_formatted}")
        markdown_lines.append("")  # Add empty line after each year

    # Generate markdown for unknown papers if any
    if unknown_papers:
        markdown_lines.append("# Unknown")
        for paper in unknown_papers:
            tags_formatted = ' '.join(f"#{tag}" for tag in paper['tags'])
            markdown_lines.append(f"- [ ] [[{paper['source']}|{paper['title']}]] : {paper['citation_count']} citations, Unknown, {tags_formatted}")
        markdown_lines.append("")  # Add empty line after Unknown section

    return '\n'.join(markdown_lines)

def process_pdfs(root_folder,directory, rules, tags,output_list=[]):

    # load existing dic

    processed_files = set(entry['source'] for entry in output_list)
    pdf_files = list_pdf_files(directory)

    for pdf_path in tqdm(pdf_files):
        pdf_path = pdf_path.replace(root_folder,"")

        if pdf_path not in processed_files:
        # get the paper details and tags
            try:
                paper_info = process_pdf(pdf_path, rules, tags)
                output_list.append(paper_info)
                if paper_info["tags"] ==[]:
                    if paper_info["citation_count"] == "Unknown":
                        print("Paper not found")
                    else:
                        print("Paper found but wrong tags")
                else:
                    print(f"Successfully processed: {paper_info['title']}")
                processed_files.add(pdf_path)
            except Exception as e:
                print(f"Error processing {pdf_path}: {str(e)}")
            # quit()
            time.sleep(5)        
    return output_list

if __name__ == "__main__":
    # Example usage


    root_folder = "../Knowledge/"
    papers_folder = os.path.join(root_folder,"Papers")
    json_path = os.path.join(root_folder,"papers_info.json")
    print(json_path)
    rules = "You will always provide only one list of 3 element following the format" \
            "The type_tag will be either :\n -  'Image' : if the paper deals only with image\n - 'Video_Mono' : if it deals with video and possibly images from a unique monocular or In the wild pov\n - 'Video_Multi' : if it deals with several video of the same scene with differents POV\n\n" \
            "the archi_tag will describe the architecture of the paper either CNN, ViT or SSM (like Vision mamba) " \
            "the task_tag will describe if it is either a video_classification (as well as TAD, TAL),"\
            "image_classification " \
            " Human pose estimation (HPE)" \
            "tracking" \
            "Segmentation" \
            "or NLP_related vision tasks"

    tags = [
        "image",
        "Video_Mono",
        "Video_Multi",
        "CNN",
        "ViT",
        "SSM",
        "video_classification",
        "image_classification",
        "HPE",
        "Tracking",
        "Segmentation",
        "NLP-vision",
        "Others"

    ]


    load_dotenv(find_dotenv())
    
    with open(json_path, 'r') as f:
        output_list = json.load(f)
    output_list = process_pdfs(root_folder,papers_folder, rules, tags,output_list=output_list)

    unique, duplicates, stats = filter_papers(output_list)
    print(f"Unique Papers: {stats['unique_papers']}")
    print(f"Duplicate Papers: {stats['duplicate_papers']}")

    # print(unique)
    # print(duplicates)

    md = create_markdown(unique)
    with open(os.path.join(root_folder,'Tasks papers_list.md'), 'w') as f:
        f.write(md)

    with open(json_path, 'w') as f:
        json.dump(output_list, f, indent=4, default=str)

    # write duplicates 
    with open(os.path.join(root_folder,'Duplicates_papers_list.json'), 'w') as f:
        json.dump(duplicates, f, indent=4, default=str)

    print("Processing complete. Markdown file 'papers_list.md' has been generated.")