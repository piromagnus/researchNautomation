import json
from typing import List, Dict
from datetime import datetime
import os
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import aisuite as ai
from dotenv import load_dotenv, find_dotenv



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



def list_to_markdown(papers: List[Dict], output_file: str,ai_summary=True):
    """
    Converts a list of paper dictionaries to a Markdown file with detailed information.

    Each paper includes its title, abstract, links to arXiv and GitHub repository,
    score, date, and the number of GitHub stars.

    Args:
        papers (List[Dict]): List of papers with keys like 'title', 'abstract', 'link', 
                             'repo', 'score', 'stars', and 'date'.
        output_file (str): Path to the output Markdown file.
    """
    with open(output_file, 'w', encoding='utf-8') as md:
        n_papers = len(papers)
        dates = [paper.get('date', '').split(" ")[0] for paper in papers]
        unique_dates = list(set(dates))
        subset_dates = unique_dates[:min(5,len(unique_dates))]  # Example: limit to the first 5 unique dates
        avg_score = sum(float(paper.get('general_score', 0)) for paper in papers) / n_papers
        avg_negative = sum(float(paper.get('negative_score', 0)) for paper in papers) / n_papers
        avg_positive = sum(float(paper.get('positive_score', 0)) for paper in papers) / n_papers
        total_stars = sum(int(paper.get('stars', 0)) for paper in papers)
        avg_stars = total_stars / n_papers
        md.write(f"# Stats\n")
        md.write(f"Number of papers: {n_papers}\n")
        str_dates='\n - '.join(subset_dates)
        md.write(f"Number of unique dates:\n - {str_dates}\n")

        md.write(f"Average score: {avg_score:.2f}\n")

        md.write(f"Average negative score: {avg_negative:.2f}\n")
        md.write(f"Average positive score: {avg_positive:.2f}\n")

        scores = [float(paper.get('general_score', 0)) for paper in papers]
        add_ascii_histogram(scores, md)
        add_scatter_plot(papers, md,output_file)
        client_llm = ai.Client()
        model = "ollama:phi4:latest"
        md.write(f"Total stars: {total_stars}\n\n")
        for paper in papers:
            title = paper.get('title', 'No Title')
            authors = paper.get('authors', ['No Authors'])
            abstract = paper.get('abstract', 'No Abstract')
            arxiv_link = paper.get('link', '#')
            repo_link = paper.get('repo', None)
            
            negative_score = paper.get('negative_score', 'N/A')
            positive_score = paper.get('positive_score', 'N/A')
            general_score = paper.get('general_score', 'N/A')
            stars = paper.get('stars', 0)
            date_str = paper.get('date', '')
            
            messages = [
            {"role": "system", "content": "You are a helpful assistant that creates concise summaries of academic papers in computer vision. You will only give the summary and nothing before nor any explaination of what it is. You will be concise without long sentences. You will use short group of words"},
            {"role": "user", "content": f"Please summarize the following abstract in 50 words:\n\n{abstract}"}
            ]
            if ai_summary:
                response = client_llm.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7
                )
                
                summary = response.choices[0].message.content
            else:
                summary = None

            # Extract only the date part
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S%z").strftime("%Y-%m-%d")
            except ValueError:
                date = "Invalid Date"
            
        
            
            #md.write(f"Average stars: {avg_stars:.2f}")

            repo_str=  f"[Repo]({repo_link})\n" if (repo_link!="N/A" and repo_link is not None) else "No Repo\n"
            authors_abv = [ author.split(" ")[-1] + ", " +        author.split(" ")[0][0]+"." for author in authors]
            authors_str = ", ".join(authors_abv)

            md.write(f"# {title}\n")
            md.write(f"**Authors:** {authors_str}\n")
            md.write(f"**Links:** [arXiv]({arxiv_link}) | " + repo_str)
            md.write(f"**Score:** {general_score} | ⭐ : {stars}\n")
            md.write(f"**Score positive:** {positive_score} |**Score negative:** {negative_score}\n")
            md.write(f"**Date:** {date}\n")
            if summary:
                md.write(f"**Summary:** {summary}\n")
            md.write(f"**Abstract:** {abstract}\n\n")
    

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
            