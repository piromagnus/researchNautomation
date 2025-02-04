import os
import argparse
import requests
from bs4 import BeautifulSoup
import aisuite as ai
from dotenv import load_dotenv
from prompts import *


def get_md_query(prompt:str,file_path: str) -> str:
    with open(file_path, "r") as file:
        content = file.read()
    
    # Split by --- and get the content after frontmatter
    parts = content.split("---")
    if len(parts) >= 3:
        # Take everything after the second '---'
        query = "---".join(parts[2:]).strip()
    else:
        # If no proper frontmatter, return the whole content
        query = content.strip()
    filename = os.path.basename(file_path).replace(".md","")
    client = ai.Client()
    messages = [
            {"role": "system", "content": "You are a helpful assistant that creates concise Wikipedia search queries based on provided text. YOU ONLY GIVE THE QUERY AND NOTHING ELSE. You will be concise without long sentences. You will use short groups of words."},
            {"role": "user", "content": f"Generate a short search query for Wikipedia for the concept {filename} using this context:\n\n{query}"}
            ]
            
    response = client.chat.completions.create(
        model="ollama:llama3.1:8b",
        messages=messages,
        temperature=0.7
    )

    query = response.choices[0].message.content
    
    return query


def search_wikipedia(query: str) -> str:
    # Use Wikipedia's API to search for the most similar page and return its title.
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json"
    }
    response = requests.get("https://en.wikipedia.org/w/api.php", params=params)
    data = response.json()
    results = data.get("query", {}).get("search", [])
    if not results:
        return None
    return results[0]["title"]

def scrape_wikipedia_page(title: str) -> str:
    # Scrape the Wikipedia page using BeautifulSoup.
    url = "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")
    response = requests.get(url)
    if response.status_code != 200:
        return "Failed to retrieve Wikipedia page."
    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all("p")
    text = "\n\n".join(p.get_text() for p in paragraphs)
    return text

def generate_summary(text: str) -> str:
    # New function to generate a summary using aisuite
    client = ai.Client()
    messages = [
        {"role": "system", "content": quick_search_summary},
        {"role": "user", "content": f"Summarize the following Wikipedia content to explain the concept at a PhD level in details:\n\n{text}"}
    ]
    response = client.chat.completions.create(
        model="ggenai:gemini-2.0-flash-exp",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def main():
    parser = argparse.ArgumentParser(description="Search and scrape Wikipedia based on file content")
    parser.add_argument("vault", type=str, help="Path to the input file")
    parser.add_argument("file_name", type=str, help="Path to the input file")
    args = parser.parse_args()

    prompt= "You have to write a really detailled answer to the following topic for a PhD level: \n"

    # Read file content
    load_dotenv(".ai.env")
    # Generate a concise search query using aisuite
    search_query = get_md_query(prompt, os.path.join(args.vault, args.file_name))
    print(f"Generated Wikipedia Query: {search_query}")

    # Search Wikipedia for a similar page
    page_title = search_wikipedia(search_query)
    while not page_title:
        print("No relevant Wikipedia page found. Trying again.")
        search_query = get_md_query(prompt, os.path.join(args.vault, args.file_name))
        page_title = search_wikipedia(search_query)
    print(f"Wikipedia Page Title: {page_title}")

    # Scrape and display the page content
    page_content = scrape_wikipedia_page(page_title)
    print("\n--- Scraped Wikipedia Page Content ---\n")
    print(page_content)

    # New: Generate and display a summary of the scraped content
    summary = generate_summary(page_content)
    print("\n--- Summary of the Concept ---\n")
    print(summary)

if __name__ == "__main__":
    main()
