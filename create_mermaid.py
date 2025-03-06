from dotenv import load_dotenv
from utils import open_obsi_file
import aisuite as ai
from pathlib import Path
import os

request_prompt = """
"<report>\n{}\n<report>\n 
Please create a mermaid diagram to explain the concept described within the report.
You will avoid using "(" and ")" in the diagram.
You will focus on the main topic of this note.
You will first select the subject of the note and then you will create a diagram to explain the concept within the <main_topic> <main_topic> tag.
You will then extract the main concepts related to this subject with <concept> <concept> tag and then you will do the diagram.
Then you will think about how to create the diagram what to keep, 
        what to remove and how to construct a diagram that explains the links between the concepts and how it is working. You will do think in <think> <think> tag
You will keep the diagram simple and easy to understand.
You will avoid many links starting from the same node.
You will reason step by step to provide the clearest explanation possible. Let's start with the first step 
<main_topic>

"""
### 2. Python Script Using mermaid-py
import re
import mermaid  # Ensure you have installed mermaid-py via pip

def extract_mermaid_content(diagram: str) -> str:
    """
    Extracts the mermaid diagram content from markdown code fences.
    """
    pattern = r"```mermaid\s*([\s\S]+?)\s*```"
    match = re.search(pattern, diagram)
    if match:
        return match.group(1).strip()
    return ""

def create_graph(content: str, title: str = "diagram") -> mermaid.Graph:
    """
    Creates a mermaid Graph object from diagram content.
    """
    return mermaid.Graph(
        title=title,
        script=content
    )

def run_mermaid(graph: mermaid.Graph, output_path: str = "./output") -> str:
    """
    Tries to generate and save an SVG from the mermaid Graph object.
    Returns "Okay" if successful, otherwise returns error message.
    """
    try:
        # Save mermaid file
        # os.makedirs(output_path, exist_ok=True)
        # mmd_path = Path(output_path) / f"{graph.title}.mmd"
        # svg_path = Path(output_path) / f"{graph.title}.svg"
        
        # Save mermaid file
        # graph.save(mmd_path)
        
        # Generate SVG
        start = time.time()
        m = mermaid.Mermaid(graph)
        # print(f"Time to generate SVG: {time.time()-start}")
        # m.to_svg(svg_path)
        print(f"SVG generated in {time.time()-start} seconds")
        
        # Save SVG
        # print(f"SVG Output saved to {svg_path}")
        return "Okay"
    except Exception as e:
        print(f"Error generating diagram: {e}")
        return f"{e}"

def request_correction(error: str, diagram: str, content: str) -> str:
    """
    Requests a correction from the LLM based on the error message.
    """
    client = ai.Client()
    messages = [
        {"role": "system", "content": "You are a helpful assistant that fixes mermaid diagrams. You only respond with the corrected diagram within the ```mermaid``` tags."},
        {"role": "user", "content": f"""
The following mermaid diagram has an error: {error}

Original diagram:
{diagram}

Context content:
{content}

Please provide a corrected version of the mermaid diagram that fixes this error. Only respond with the corrected diagram in markdown code fences."""}
    ]
    
    response = client.chat.completions.create(
        model="genai:gemini-2.0-flash-thinking-exp-01-21",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

def generate_diagram(content: str) -> str:
    client = ai.Client()
    messages = [
            {"role": "system", "content": "You are a helpful assistant that creates mermaid diagram of concepts. You will focus on the main topic and use sub concept of the main topic explain it visually. You are an expert in machine learning, computer science and Computer vision. You will use the format ```mermaid``` tag. for diagram"},
            {"role": "user", "content": request_prompt.format(content)}
            ]
    
    response = client.chat.completions.create(
        model="genai:gemini-2.0-flash-thinking-exp-01-21",
        messages=messages,
        temperature=0.7
    )
    diagram = response.choices[0].message.content
    return diagram

def validate_diagram(content: str, max_attempts: int = 3) -> str:
    """
    Validates and corrects the mermaid diagram until it's valid or max attempts reached.
    """
    attempt = 0
    diagram = generate_diagram(content)
    print(f"Initial diagram generated:\n{diagram}")
    
    while attempt < max_attempts:
        diagram_content = extract_mermaid_content(diagram)
        if not diagram_content:
            print(f"Attempt {attempt + 1}: No valid mermaid code block found")
            return None
            
        print(f"Attempt {attempt + 1}: Validating diagram content:\n{diagram_content}")
        
        # Create graph object
        graph = create_graph(diagram_content, f"diagram_attempt_{attempt}")
        # print(graph.script)
        result = run_mermaid(graph)
        
        if result == "Okay":
            print(f"Valid diagram generated after {attempt + 1} attempts")
            return diagram_content
            
        print(f"Attempt {attempt + 1}: Diagram invalid. Error: {result}")
        diagram = request_correction(result, diagram_content, content)
        attempt += 1
    
    print(f"Failed to generate valid diagram after {max_attempts} attempts")
    return None

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
    args = parser.parse_args()
    

    # Load the research data
    vault_path= args.vault if args.vault!="." else "/home/pmarrec/vault"
    file_name=args.file_name if args.file_name!="." else None
    if file_name is not None and not file_name.endswith(".md"):
        print("Please provide a markdown file")
        exit(0)

    file_path = os.path.join(vault_path, file_name)
    content = open_obsi_file(file_path)

    # Generate and validate diagram
    final_diagram = validate_diagram(content)
    if final_diagram:
        print("Final diagram:")
        print(final_diagram)
    else:
        print("Failed to generate a valid diagram")