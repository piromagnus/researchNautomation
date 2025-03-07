from gpt_researcher import GPTResearcher
import aisuite as ai
import asyncio
from dotenv import load_dotenv, find_dotenv
import requests
import bs4
from utils.io import open_obsi_file
from utils.create_mermaid import validate_diagram





async def get_report(query: str, report_type: str):
    researcher = GPTResearcher(query, report_type,max_subtopics=3)
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    
    # Get additional information
    research_context = researcher.get_research_context()
    research_costs = researcher.get_costs()
    research_images = researcher.get_research_images()
    research_sources = researcher.get_research_sources()
    
    return report, research_context, research_costs, research_images, research_sources



def get_md_query(prompt:str,file_path: str) -> str:
    query = open_obsi_file(file_path)

    filename = os.path.basename(file_path).replace(".md","")
    client = ai.Client()
    messages = [
            {"role": "system", "content": "You are a helpful assistant that creates concises query for agentic search. Your objectives it to create a reasearch query based on the informations provided. You will only give the query and nothing before nor any explaination of what it is. You will be concise without long sentences. You will use short group of words"},
            {"role": "user", "content": f"Please write a query for this concept {filename} using this context:\n\n{query}"}
            ]
            
    response = client.chat.completions.create(
        model=os.getenv("QUERY_LLM"),
        messages=messages,
        temperature=0.7
    )

    query = response.choices[0].message.content
    #get the basename
    


    return prompt+ query

def get_report_filepath(original_filepath: str) -> str:
    """ Get the filepath to write the report"""
    """ Replace Concepts by repport in the folder"""
    return original_filepath.replace("Concepts", "report")

def write_report_to_file(filepath: str, report: str, context: str, costs: dict, 
                        images: list, sources: list) -> None:
    """Write the report and additional information to a file"""
    with open(filepath, 'w') as file:
        file.write("Context:\n")
        file.write(context + "\n\n")
        file.write("Report:\n")
        file.write(report + "\n\n")
        file.write("Research Costs:\n")
        file.write(str(costs) + "\n\n")
        file.write("Number of Research Images:\n")
        file.write(str(len(images)) + "\n\n")
        file.write("Number of Research Sources:\n")
        file.write(str(len(sources)) + "\n\n")

def scrape_pages(urls: list[str]) -> list[str]:
    # Corrected function to scrape pages from a list of URLs
    pages = []
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = bs4.BeautifulSoup(response.text, "html.parser")
            paragraphs = soup.find_all("p")
            text = "\n\n".join(p.get_text() for p in paragraphs)
            pages.append(text)
        except Exception as e:
            print(f"Error scraping {url}: {e}")
    return pages

if __name__ == "__main__":

    #TODO add a query in the concepts vault to get more information about the topic

    import time

    load_dotenv(".ai.env")
    import argparse
    import os

    start = time.time()
    # Parse the arguments
    parser = argparse.ArgumentParser(description="Conduct AI research")
    parser.add_argument("vault", type=str, help="the folder where the research data is stored", default="/home/pmarrec/vault")
    parser.add_argument("file_name", type=str, help="the file path to the research data")
    parser.add_argument("report_type", type=str, help="the type of report to generate", default="research_report")
    args = parser.parse_args()
    

    prompt= "You have to write a really detailled answer to the following topic for a PhD level: \n"


    # Load the research data
    vault_path= args.vault if args.vault!="." else "/home/pmarrec/vault"
    file_name=args.file_name if args.file_name!="." else None
    if file_name is not None and not file_name.endswith(".md"):
        print("Please provide a markdown file")
        exit(0)

    file_path = os.path.join(vault_path, file_name)
    query = get_md_query(prompt,file_path)
    print(f"Query: {query}")
    


    report, context, costs, images, sources = asyncio.run(get_report(query, args.report_type))
    
    #replace \( by $ and \) by $
    report = report.replace(r"\( ", "$").replace(r" \)", "$")
    report = report.replace(r"\(", "$").replace(r"\)", "$")

    #replace \[ by $$ and \] by $$
    report = report.replace(r"\[ ", "$$").replace(r" \]", "$$")
    report = report.replace(r"\[", "$$").replace(r"\]", "$$")

    client = ai.Client()
    messages = [
            {"role": "system", "content": "You are a helpful assistant that creates concises summary of large text to be read fast. You are an expert in machine learning, computer science and Computer vision."},
            {"role": "user", "content": f"Please summarize the following in a PhD level manner grasping the most important part in less than 200 words:\n\n{report}"}
            ]
            
    response = client.chat.completions.create(
        model="genai:gemini-2.0-flash-thinking-exp-01-21",
        messages=messages,
        temperature=0.7
    )
    summary = response.choices[0].message.content
    # ask the model to provide a mermaid diagram of the concepts
    diagram =  validate_diagram(report)
    if diagram is None:
        print("Diagram generation failed")
        diagram = "No diagram generated"
    else:
        diagram = "```mermaid\n"+diagram +"```"


    report = summary + "\n\n" + diagram + "\n\n" + report

    report_filepath = get_report_filepath(file_path)
    write_report_to_file(report_filepath, report, context, costs, images, sources)
    print(f"Report written to {report_filepath}")

    # add the report to the file
    with open(file_path, "a") as file:
        file.write(f"\n\n---\n\n{report} \n time taken: {time.time()-start} seconds\n\n")

## .env for Ollama environment
# OPENAI_API_KEY="123"
# OPENAI_API_BASE="http://127.0.0.1:11434/v1"
# OLLAMA_BASE_URL="http://127.0.0.1:11434/"
# FAST_LLM="ollama:qwen2:1.5b"
# SMART_LLM="ollama:qwen2:1.5b"
# EMBEDDING="ollama:all-minilm:22m"

