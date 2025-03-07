import os
import json
import re
from typing import List, Dict
import utils.md_format as mdf

def extract_titles_from_markdown(markdown_path: str) -> List[str]:
    """Extract all titles from markdown file."""
    titles = []
    with open(markdown_path, 'r', encoding='utf-8') as file:
        content = file.read()
        # Match lines starting with single # followed by text
        title_matches = re.finditer(r'^# (.+)$', content, re.MULTILINE)
        titles = [match.group(1).strip() for match in title_matches]
    return titles

def update_json_from_markdown(json_path: str, markdown_path: str, output_json_path: str) -> Dict:
    """Update JSON file based on markdown titles."""
    try:
        # Read existing JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Get markdown titles
        markdown_titles = extract_titles_from_markdown(markdown_path)
        
        # Filter JSON data
        filtered_data = [
            paper for paper in json_data 
            if paper.get('title') in markdown_titles
        ]
        
        # Write updated JSON
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=4, ensure_ascii=False)
        
        metrics = {
            "original_papers": len(json_data),
            "remaining_papers": len(filtered_data),
            "removed_papers": len(json_data) - len(filtered_data)
        }
        
        return metrics
        
    except Exception as e:
        print(f"Error processing files: {str(e)}")
        return None

def sync_markdown_json(root_folder: str):
    """Synchronize JSON files with markdown content."""
    input_folder = os.path.join(root_folder, "automation/weekly_arxiv_json")
    markdown_folder = os.path.join(root_folder, "Weekly Letter")
    
    # Process each folder
    folders = [f for f in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, f))]
    
    for folder in folders:
        #get the file that are in folder and doesn't end with config.json or clean.json

        files = [f for f in os.listdir(os.path.join(input_folder, folder)) if f.endswith('.json') and not f.endswith('_config.json') and not f.endswith('_clean.json')]

        if len(files) == 0:
            print(f"No JSON files found in {folder}")
            continue

        for file in files:
            json_path = os.path.join(input_folder, folder, file)
            json_archive = os.path.join(input_folder,"archive", file)
            markdown_path = os.path.join(markdown_folder, folder, file.replace('.json', ' clean.md'))
            output_json_path = os.path.join(input_folder, folder, file.replace('.json', '_clean.json'))
        
            if os.path.exists(json_path) and os.path.exists(markdown_path):
                metrics = update_json_from_markdown(json_path, markdown_path, output_json_path)
                if metrics:
                    print(f"\nProcessed {file}:")
                    print(f"Original papers: {metrics['original_papers']}")
                    print(f"Remaining papers: {metrics['remaining_papers']}")
                    print(f"Removed papers: {metrics['removed_papers']}")
                    # Move JSON file to archive
                    try:
                        os.replace(json_path, json_archive)
                        print(f"Moved {file} to archive")
                    except Exception as e:
                        print(f"Error moving file to archive: {str(e)}")
                    with open(output_json_path, 'r', encoding='utf-8') as f:
                        papers = json.load(f)
                    mdf.list_to_markdown(papers, markdown_path.replace(' clean.md', '_clean.md'))
            else:
                if not os.path.exists(json_path):
                    print(f"JSON file not found: {json_path}")
                if not os.path.exists(markdown_path):
                    print(f"Markdown file not found: {markdown_path}")
            
# Add to main execution
if __name__ == "__main__":
    root_folder = "../Knowledge"
    sync_markdown_json(root_folder)