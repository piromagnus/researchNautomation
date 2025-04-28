import json
import logging
import traceback
from typing import List, Dict
from datetime import datetime
import os
import matplotlib.pyplot as plt
import numpy as np

import litellm
from dotenv import load_dotenv, find_dotenv
from tqdm import tqdm




# model = "ollama:qwq:latest"
load_dotenv(find_dotenv())
# Adjust model variable loading
# model = os.getenv("SMALL_SUMMARY_MODEL",'ollama:phi4:latest')
# Determine model based on env vars. litellm handles various providers.
# We'll get the specific model string from the .env or .ai.env later.
llm_model = os.getenv("LITELLM_MODEL", 'ollama/phi4') # Default to ollama/phi4 if not set

# add a logger
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def get_llm_response(content, system_prompt, temperature=0.7):
    """Generic LLM response function using litellm"""

    messages = [
        {"role": "system", "content": system_prompt + 
         """ You always reason before outputting the answer whatever the user asks. 
         You reason step by step with a maximum of 6 words per thought and you give your answer after this delimiter ####---####. 
         You must use the delimiter before writing any answer. 
         All outputs must follow the format [reasoning]####---####[answer]"""},
        {"role": "user", "content": content}
    ]
    try:
        # Use litellm.completion instead of client.chat.completions.create
        response = litellm.completion(
            model=llm_model, # Use the model defined above
            messages=messages,
            temperature=temperature,
            timeout=120,
            # Add api_base if needed for local models like Ollama
            api_base=os.getenv("OLLAMA_BASE_URL") if llm_model.startswith("ollama/") else None 
        )
        # Access response content correctly for litellm
        res = response.choices[0].message.content.strip() 
        logger.info(f"LLM response: {res}")
        res_parts = res.split("####---####") # Renamed variable to avoid conflict
        if len(res_parts) > 1 and res_parts[1].strip() != "":
            return res_parts[1].strip()
        else:
            # Retry logic might need adjustment depending on litellm's error handling
            # For simplicity, let's just return the raw response if splitting fails
            logger.warning("LLM response did not contain the expected delimiter. Retrying...")
            return get_llm_response(content, system_prompt, temperature)

            # return res # Return the full response if delimiter not found after reasoning.
            # Original retry logic: get_llm_response(content, system_prompt, temperature) 
        # Return the part after the delimiter
        # return res # This line seems incorrect, should return res_parts[1]
    
    except Exception as e:
        #print the traceback
        print(f"Error in LLM call with litellm: {e}")
        print(traceback.format_exc())
        # Consider more robust error handling if needed
        # Check if it's an API key error specifically
        if "API key" in str(e):
             logger.error("API key error. Please check your environment variables (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)")
        elif "Connection refused" in str(e) and llm_model.startswith("ollama/"):
             logger.error(f"Connection error. Is Ollama running and accessible at {os.getenv('OLLAMA_BASE_URL')}?")
        #add the api error like rate limit error
        elif "Rate limit" in str(e):
             logger.error("Rate limit error. Please wait a few seconds and try again.")
        # Reraise or return None based on desired behavior
        return None 

def get_tasks_tags(paper):
    """Extract the main task from the paper"""
    system_prompt = "You are a helpful assistant that extracts the task from academic papers in computer vision. You will answer only the task in a short sentence or word without anything else."
    content = f"""
        Analyze the research paper and identify the primary task type or research category.
        Examples include: "Image Classification", "3D Monocular Human pose estimation"," "3D Multiview Human pose estimation", "Reinforcement Learning", etc.
        Provide only the task type without any additional explanation or surrounding text.
        Format your answer as a single sentence.
        \n\n{paper}
    """
    return get_llm_response(content, system_prompt)

def get_contributions(paper):
    """Extract the top 3 main contributions from the paper"""
    system_prompt = "You are a helpful assistant that extracts key technical contributions from academic papers. List exactly 3 main technical contributions, each starting with a bullet point."
    content = f"""
        Analyze this research paper and identify the 3 most important technical contributions.
        Be specific, concise and technical.
        Format your answer as bullet points.
        Your answer will contains only the bullet points.
        \n\n{paper}
    """
    return get_llm_response(content, system_prompt)

def get_paper_summary(paper):
    """Generate a concise summary of the paper"""
    system_prompt = "You are a helpful assistant that creates concise summaries of academic papers. Focus only on key innovations and technical aspects."
    content = f"""
        Summarize this research paper in 2-3 short sentences, focusing on:
        - The main technical innovation
        - The key methodology
        - The primary results
        \n\n{paper}
    """
    return get_llm_response(content, system_prompt)

def add_ascii_histogram(scores, md_file):
    bins = np.arange(0, 1.1, 0.1)
    hist, _ = np.histogram(scores, bins=bins)
    max_height = 20  # Maximum height
    scale = max_height / max(hist) if max(hist) > 0 else 1
    
    md_file.write("\n## Score Distribution\n```\n")
    
    # Create vertical bars
    for height in range(max_height, -1, -1):
        line = ""
        for count in hist:
            bar_height = int(count * scale)
            line += "   |" if bar_height > height else "    "
        md_file.write(line + "\n")
    
    # Add bin markers below
    bin_markers = ""
    for bin_edge in bins[:-1]:
        bin_markers += f"{bin_edge:.1f}-"
    bin_markers+="1"
    md_file.write("-" * (len(hist) * 4) + "\n")
    md_file.write(bin_markers + "\n")
    md_file.write("```\n")

def add_scatter_plot(papers, md_file, output_file):
    positives = [float(p.get('positive_score', 0)) for p in papers]
    negatives = [float(p.get('negative_score', 0)) for p in papers]
    scores = [float(p.get('general_score', 0)) for p in papers]
    
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(negatives, positives, c=scores, cmap='viridis', alpha=0.7)
    plt.colorbar(scatter, label='General Score')
    plt.xlabel('Negative Score')
    plt.ylabel('Positive Score')
    plt.title('Paper Scores Distribution')
    
    # Save the image in the same folder as output_file with similar name + _stats.png
    output_dir = os.path.dirname(output_file)
    output_filename = os.path.splitext(os.path.basename(output_file))[0] + '_stats.png'
    output_image_path = os.path.join(output_dir, output_filename)
    
    plt.savefig(output_image_path, format='png', dpi=200, bbox_inches='tight')
    plt.close()

    
    md_file.write(f"\n## Score Scatter Plot\n")
    md_file.write(f"![[{output_filename}]]\n\n")

def list_to_markdown(papers: List[Dict], output_file: str, ai_summary=True):
    """
    Converts a list of paper dictionaries to a Markdown file with detailed information.

    Each paper includes its title, abstract, links to arXiv and GitHub repository,
    score, date, and the number of GitHub stars.

    Args:
        papers (List[Dict]): List of papers with keys like 'title', 'abstract', 'link', 
                             'repo', 'score', 'stars', and 'date'.
        output_file (str): Path to the output Markdown file.
        ai_summary (bool): Whether to generate AI summaries for papers. Defaults to True.
    """
    with open(output_file, 'w', encoding='utf-8') as md:
        n_papers = len(papers)
        if n_papers == 0:
             md.write("# No papers found for this query.\n")
             return

        dates = [paper.get('date', '').split()[0] for paper in papers if paper.get('date')] # Extract only the day part
        unique_dates = sorted(list(set(dates)), reverse=True) # Sort dates reverse chronologically
        subset_dates = unique_dates[:min(5,len(unique_dates))]  # Example: limit to the first 5 unique dates
        
        # Ensure scores are floats before calculation
        general_scores = [float(p.get('general_score', 0)) for p in papers]
        negative_scores = [float(p.get('negative_score', 0)) for p in papers]
        positive_scores = [float(p.get('positive_score', 0)) for p in papers]
        
        avg_score = sum(general_scores) / n_papers
        avg_negative = sum(negative_scores) / n_papers
        avg_positive = sum(positive_scores) / n_papers
        
        total_stars = sum(int(paper.get('stars', 0)) for paper in papers)
        # Avoid division by zero if no papers have stars info
        papers_with_stars = [p for p in papers if 'stars' in p] 
        
        md.write(f"# Stats\n")
        md.write(f"Number of papers: {n_papers}\n")
        str_dates='\n - '.join(subset_dates)
        md.write(f"Recent Dates:\n - {str_dates}\n") # Clarified heading

        md.write(f"Average score: {avg_score:.2f}\n")

        md.write(f"Average negative score: {avg_negative:.2f}\n")
        md.write(f"Average positive score: {avg_positive:.2f}\n")

        # Use general_scores directly
        add_ascii_histogram(general_scores, md) 
        add_scatter_plot(papers, md,output_file)
        # Removed redundant client instantiation
        # client_llm = ai.Client()

        md.write(f"Total stars: {total_stars}\n\n")

        for paper in tqdm(papers, desc="Processing papers"):
            title = paper.get('title', 'No Title')
            # Handle potential list of authors objects or strings
            authors_data = paper.get('authors', ['No Authors']) 
            if authors_data and isinstance(authors_data[0], str):
                 authors = authors_data # Assume list of strings
            elif authors_data and hasattr(authors_data[0], 'name'): # Check for arxiv.Result.Author objects
                 authors = [str(a) for a in authors_data]
            else:
                 authors = ['No Authors'] # Default case

            abstract = paper.get('abstract', 'No Abstract')
            arxiv_link = paper.get('link', '#')
            repo_link = paper.get('repo', None)
            # print(abstract)
            # Format scores consistently
            negative_score = paper.get('negative_score') 
            positive_score = paper.get('positive_score')
            general_score = paper.get('general_score')
            stars = paper.get('stars', 0)
            date_str = paper.get('date', '')

            if ai_summary and abstract and abstract != "No Abstract" and abstract.strip() != "": # Check if abstract is not empty
                try: # Add error handling for LLM calls
                    task = get_tasks_tags(abstract)
                    summary = get_paper_summary(abstract)
                    contributions = get_contributions(abstract)
                except Exception as e:
                     logger.error(f"Failed to generate AI summary for '{title}': {e}")
                     task = "Error generating task"
                     summary = "Error generating summary"
                     contributions = "Error generating contributions"
            else:
                task = None
                summary = None
                contributions = None

            # Extract only the date part robustly
            try:
                 # Handle both datetime objects and string formats
                 if isinstance(date_str, datetime):
                      date = date_str.strftime("%Y-%m-%d")
                 elif isinstance(date_str, str):
                      # Attempt parsing common formats
                      parsed_date = None
                      for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d"):
                           try:
                                parsed_date = datetime.strptime(date_str.split('T')[0], fmt.split('T')[0]) # Try parsing only date part
                                break
                           except ValueError:
                                continue
                      date = parsed_date.strftime("%Y-%m-%d") if parsed_date else "Invalid Date Format"
                 else:
                      date = "Invalid Date Type"
            except Exception: # Catch broader errors during date processing
                date = "Invalid Date"
            

            
            #md.write(f"Average stars: {avg_stars:.2f}")

            repo_str=  f"[Repo]({repo_link})\n" if (repo_link and repo_link != "N/A") else "No Repo\n" # Simplified check
            # Format authors correctly
            try:
                authors_abv = [author.split(" ")[-1] + ", " + author.split(" ")[0][0] + "." for author in authors if " " in author]
                authors_str = ", ".join(authors_abv) if authors_abv else ", ".join(authors) # Fallback if no space
            except:
                authors_str = ", ".join(map(str, authors)) # Handle unexpected author format

            md.write(f"# {title}\n")
            if task is not None:
                md.write(f"**Task:** {task}\n")
            if contributions is not None:
                md.write(f"**Key Contributions:**\n{contributions}\n")
            md.write(f"**Authors:** {authors_str}\n")
            md.write(f"**Links:** [arXiv]({arxiv_link}) | " + repo_str)
            # Format scores or show N/A
            score_line = "**Score:** N/A"
            if general_score is not None:
                 score_line = f"**Score:** {float(general_score):.3f} | ⭐ : {stars}" # Using 3 decimal places
            md.write(f"{score_line}\n")
            
            score_details = []
            if positive_score is not None:
                 score_details.append(f"**Score positive:** {float(positive_score):.3f}")
            if negative_score is not None:
                 score_details.append(f"**Score negative:** {float(negative_score):.3f}")
            if score_details:
                 md.write(" | ".join(score_details) + "\n")

            md.write(f"**Date:** {date}\n")
            if summary:
                md.write(f"**Summary:** {summary}\n")
            # Use markdown blockquote for abstract
            md.write(f"**Abstract:** \n> {abstract}\n\n") 

if __name__ == "__main__":
    load_dotenv(find_dotenv())
    root_folder=os.getenv("ROOT_FOLDER")
    
    input_folder = os.path.join(root_folder,os.getenv("JSON_FOLDER"))
    output_folder = os.path.join(root_folder,os.getenv("MD_FOLDER"))

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # get the folders only inside input_folder
    folders = [f for f in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, f))]

    for folder in folders:
        input_folder_path = os.path.join(input_folder, folder)
        output_folder_path = os.path.join(output_folder, folder)

        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)

        input_files = os.listdir(input_folder_path)
        ##remove the one finishing by _config.json
        input_files = [f for f in input_files if not f.endswith('_config.json')]

        output_files = os.listdir(output_folder_path)
        print(output_files)

        for input_file in input_files:
            if input_file.endswith('.json'):
                json_file_path = os.path.join(input_folder_path, input_file)
                output_file_name = f"{input_file.replace('.json', '.md')}"
                output_file_path = os.path.join(output_folder_path, output_file_name)

                if output_file_name not in output_files:
                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        papers = json.load(f)
                    list_to_markdown(papers, output_file_path)
                    print(f"Processed {input_file} into {output_file_name}")
                else:
                    print(f"Skipping {input_file} as {output_file_name} already exists")
            else:
                print(f"Skipping {input_file} as it's not a JSON file")
