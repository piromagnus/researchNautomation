#!/usr/bin/env python3
import os
import argparse
import subprocess
from utils.md_to_epub import markdown_to_epub
from summary import process_single_md
from utils.summary_prompts import rules, tags, prompt
from pathlib import Path

model_name = os.getenv("SUMMARY_MODEL",'genai:gemini-2.0-flash-exp')

def pdf_to_epub(pdf_path: str, output_path: str = None) -> str:
    """Convert PDF to EPUB using MinerU extraction and markdown conversion"""
    
    # Setup paths
    scripts_folder = os.path.dirname(os.path.realpath(__file__))
    pdf_name = os.path.basename(pdf_path)
    name_without_suffix = Path(pdf_name).stem
    
    # Define extraction folders
    extract_folder = f"Knowledge/automation/extract/{name_without_suffix}"
    full_extract_path = os.path.join(extract_folder, name_without_suffix)
    figures_path = os.path.join(full_extract_path, "auto/images")
    
    # Extract PDF to markdown using MinerU
    if not os.path.exists(os.path.join(full_extract_path, "auto", f"{name_without_suffix}.md")):
        subprocess.run(["bash", f"{scripts_folder}/run_minerU.sh", pdf_path, full_extract_path], check=True)
    
    
    # process_single_md(filepath,vault_path,figures_path,output,template_model,client,tags,model_name=model_name,prompt=prompt,rules=rules)


    # Prepare paths for epub conversion
    full_text_path = os.path.join(full_extract_path, "auto", f"{name_without_suffix}.md")
    summary_path = os.path.join("Knowledge/automation/output", f"Paper - {name_without_suffix}.md")
    
    if output_path is None:
        output_path = os.path.join(os.path.dirname(pdf_path), f"{name_without_suffix}.epub")
    
    # Convert to EPUB
    markdown_to_epub(full_text_path, summary_path, output_path,None,None)
    
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert PDF to EPUB with AI-generated summary')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--output', '-o', help='Output EPUB file path (optional)')
    args = parser.parse_args()
    
    epub_path = pdf_to_epub(args.pdf_path, args.output)
    print(f"EPUB created at: {epub_path}")