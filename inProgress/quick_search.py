import os
import argparse

import aisuite as ai
from dotenv import load_dotenv
from scripts.inProgress.prompts import *
import wikipedia
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from duckduckgo_search import DDGS
import re
import bs4
import requests
import time
from tqdm import tqdm



class Pages:
    def __init__(self, url: str, text: str):
        self.url = url
        self.text = text

    def __str__(self):
        return f"URL: {self.url}\nText: {self.text}"


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
    print(query)
    if query == "":
        return get_title_from_query(file_path)
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

def get_title_from_query(file_path: str) -> str:
    filename = os.path.basename(file_path).replace(".md","")
    return filename


def search_wiki_duck_duck_go(query: str) -> str:
    results = DDGS().text(query + "  wikipedia", max_results=5)
    # print(results)
    titles = []
    for i in results:
        if "wikipedia" in i['href']:
            #get the title of the url with regex
            title = re.search(r'(?:wikipedia.org/wiki/)([^&]+)', i['href'])
            if title:
                titles.append(title.group(1))
            #     return title.group(1).replace("_"," ")
    return titles

def search_duck_duck_go(query: str) -> str:
    results = DDGS().text(query, max_results=5)
    # print(results)
    urls = []
    for i in results:
        urls.append(i['href'])
    return urls

def search_wikipedia(query: str,results = 3) -> list[str]:
    # Use Wikipedia's API to search for the most similar page and return its title.
    list = wikipedia.search(query, results=results)
    print(list)
    if len(list) == 0:
        return None
    return list 

def scrape_pages(urls: list[str]) -> list[str]:
    # scrape pages with BeautifulSoup and return their text contents
    pages = []
    full_sum=""
    max_size = 64000
    for url in urls:
        response = requests.get(url)
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        text=soup.get_text()
        for i in range(0,len(text),max_size):
            chuck = text[i:i+max_size]


            client = ai.Client()
            messages = [
                {"role": "system", "content": summary_sources},
                {"role": "user", "content": f"Summarize the following content:\n\n{chuck}"}
            ]
            response = client.chat.completions.create(
                model="ggenai:gemini-2.0-flash-exp",
                messages=messages,
                temperature=0.7,
            )
            sum_text= response.choices[0].message.content
            full_sum+=sum_text
        pages.append(Pages(url,full_sum))
    return pages

def scrape_wikipedia_page(titles: list[str],query) -> str:
    # Scrape the Wikipedia page using BeautifulSoup.
    pages = []
    score = []
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = model.encode(query)
    for t in titles:
        # print(t)
        try:
            page = wikipedia.page(t)
        except : 
            continue
        url = page.url
        pages.append(page)
        page_embedding = model.encode(page.content)
        score.append(cosine_similarity([query_embedding], [page_embedding])[0][0])
    max_score_id = score.index(max(score))
    print(score)
    page = pages[max_score_id]
    # Use SentenceTransformer to get the most similar page to the query
    return page

def generate_summary_wiki(text: str) -> str:
    # New function to generate a summary using aisuite
    client = ai.Client()
    messages = [
        {"role": "system", "content": quick_search_summary_wiki},
        {"role": "user", "content": f"Summarize the following Wikipedia content to explain the concept at a PhD level in details:\n\n{text}"}
    ]
    response = client.chat.completions.create(
        model="ggenai:gemini-2.0-flash-exp",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()


def generate_summary_several_sources(pages: list[str]) -> str:
    # New function to generate a summary using aisuite
    format_pages = "# Sources: \n"
    for page in pages:
        format_pages += f"*url* : {page.url} \ncontent : {page.text}\n\n"


    client = ai.Client()
    messages = [
        {"role": "system", "content": quick_search_summary},
        {"role": "user", "content": f"Summarize the following sources to explain the concept at a PhD level in details:\n\n{format_pages}"}
    ]
    response = client.chat.completions.create(
        model="ggenai:gemini-2.0-pro-exp-02-05",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def create_research_plan(query: str) -> dict:
    client = ai.Client()
    messages = [
        {"role": "system", "content": phd_plan_prompt},
        {"role": "user", "content": f"Create a research plan for: {query}"}
    ]
    response = client.chat.completions.create(
        model="ggenai:gemini-2.0-pro-exp-02-05",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

def generate_search_queries(research_plan: str,max_queries=5) -> list[str]:
    client = ai.Client()
    messages = [
        {"role": "system", "content": search_query_generation},
        {"role": "user", "content": f"Generate {max_queries} and only that number of search queries based on this research plan:\n{research_plan}"}
    ]
    response = client.chat.completions.create(
        model="ggenai:gemini-2.0-pro-exp-02-05",
        messages=messages,
        temperature=0.7
    )
    # Split the response into individual queries
    queries = [q.strip() for q in response.choices[0].message.content.split('\n') if q.strip()]
    return queries[:max_queries]

def process_chunk(chunk: str) -> str:
    client = ai.Client()
    messages = [
        {"role": "system", "content": chunk_summary_prompt},
        {"role": "user", "content": f"Summarize this academic text chunk:\n{chunk}"}
    ]
    response = client.chat.completions.create(
        model="ollama:llama3.1:8b",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

def generate_final_report(summaries: list[str], sources: list[str]) -> str:
    formatted_content = "# Summaries:\n\n"
    for i, summary in enumerate(summaries, 1):
        formatted_content += f"## Summary {i}:\n{summary}\n\n"
    
    formatted_content += "# Sources:\n"
    for source in sources:
        formatted_content += f"- {source}\n"

    client = ai.Client()
    messages = [
        {"role": "system", "content": final_report_prompt},
        {"role": "user", "content": f"Generate a comprehensive PhD report based on:\n\n{formatted_content}"}
    ]
    response = client.chat.completions.create(
        model="ggenai:gemini-2.0-pro-exp-02-05",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

def gather_initial_context(query: str) -> str:
    # Do a quick initial search to gather context
    urls = search_duck_duck_go(query)[:2]  # Limit to first 2 results for speed
    initial_summaries = []
    max_size = 8000  # Smaller chunk size for initial context

    for url in urls:
        try:
            response = requests.get(url)
            soup = bs4.BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
            
            # Take just the first chunk for quick context
            chunk = text[:max_size]
            summary = process_chunk(chunk)
            initial_summaries.append(summary)
            
        except Exception as e:
            print(f"Error in initial context gathering for {url}: {str(e)}")
    print(initial_summaries)
    # Analyze the initial context
    client = ai.Client()
    messages = [
        {"role": "system", "content": initial_context_prompt},
        {"role": "user", "content": f"Analyze these preliminary findings:\n\n{''.join(initial_summaries)}"}
    ]
    response = client.chat.completions.create(
        model="ggenai:gemini-2.0-pro-exp-02-05",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

def main():
    parser = argparse.ArgumentParser(description="Generate PhD level report based on research topic")
    parser.add_argument("vault", type=str, help="Path to the vault")
    parser.add_argument("file_name", type=str, help="Path to the input file")
    args = parser.parse_args()

    start = time.time()

    load_dotenv(".ai.env")
    search_query = get_md_query("", os.path.join(args.vault, args.file_name))
    print(f"Initial Query: {search_query}")

    # Gather initial context first
    print("Gathering initial context...")
    initial_context = gather_initial_context(search_query)
    print("Initial context gathered")

    # Create research plan with context
    research_plan = create_research_plan(f"Topic: {search_query}\n\nInitial Context:\n{initial_context}")
    print("Research plan created")

    # Generate search queries from plan
    search_queries = generate_search_queries(research_plan,max_queries=5)
    print(f"Generated {len(search_queries)} search queries")
    print(search_queries)
    all_summaries = []
    all_sources = []
    max_size = 16000  # Chunk size for processing



    # Process each search query
    for query in tqdm(search_queries):
        urls = search_duck_duck_go(query)
        print(urls)
        for url in urls:
            try:
                response = requests.get(url)
                soup = bs4.BeautifulSoup(response.text, "html.parser")
                text = soup.get_text()
                print(len(text))
                # Process text in chunks
                chunks = [text[i:i+max_size] for i in range(0, len(text), max_size)]
                chunk_summaries = []
                
                for chunk in chunks:
                    summary = process_chunk(chunk)
                    chunk_summaries.append(summary)
                
                combined_summary = "\n".join(chunk_summaries)
                all_summaries.append(combined_summary)
                all_sources.append(url)
                
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")

    # Generate final report
    final_report = generate_final_report(all_summaries, all_sources)

    # Save the results
    with open(os.path.join(args.vault, args.file_name), "a") as file:
        file.write("\n\n# Initial Research Context\n")
        file.write(initial_context)
        file.write("\n\n# Research Plan\n")
        file.write(research_plan)
        file.write("\n\n# Final Report\n")
        file.write(final_report)
        file.write("\n\n## Sources\n")
        for i,source in enumerate(all_sources):
            file.write(f"- {source}\n")
            file.write(f"## Summary {i+1}\n")
            file.write(all_summaries[i])

        file.write("\n\n")
        file.write("Time taken: {:.2f} seconds".format(time.time() - start))

if __name__ == "__main__":
    main()
