import os
from pathlib import Path
import time
# import aisuite as ai
import litellm
from dotenv import load_dotenv, find_dotenv
import base64
import subprocess  # added import for subprocess
from utils.summary_prompts import rules, tags, prompt
from utils.summary_path import local_extract_folder, local_output_folder,template_path

def process_single_md(
    file_path: str,
    vault_path: str,
    loc_figures_path: str,
    output_folder: str,
    template_folder : str,
    # client: ai.Client, # Removed aisuite client
    tags: list = None,
    model_name: str = "openai/gpt-4o-2024-11-20", # Use litellm model format
    prompt: str = "",
    rules: list = None,
    ) -> None:
        """Process a single markdown file and generate analysis."""

        input_folder = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        # provider = model_name.split(":")[0] # No longer needed with litellm standard format
        output_filename = "Paper - " + Path(filename).stem + '.md'
        output_path = os.path.join(output_folder, output_filename)

        full_figures_path = os.path.join(vault_path,loc_figures_path)
        os.makedirs(full_figures_path, exist_ok=True)
        img_listdir = os.listdir(full_figures_path)
        img_listdir.sort()
        #sort
        # if provider == "genai": # Provider-specific logic might need adjustment based on litellm setup or removed if not needed

        #     for img in img_listdir:
        #         full_img_path = os.path.join(full_figures_path,img)
        #         client.upload.upload_file(full_img_path, provider_key=provider) # Removed aisuite specific upload

        if os.path.exists(output_path):
            # If the output file already exists, skip processing this Markdown file
            print("Already processed:", filename)
            return
        with open(template_folder, 'r', encoding='utf-8') as file:
            template = file.read()
        
        prompt=prompt.format(template,"\n".join(rules), ", ".join(tags),  filename.replace(".md",".pdf"))
        # Prepare the prompt for the Ollama API
        # print(prompt)
        md_path = os.path.join(input_folder, filename)
        
        #check if it does
        with open(md_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        #remove all the \n from content

        content = content.replace('\n', '')
        prompt += "Paper Content:\n" + content
        #format images with a ./before each image_full_path
        images_full_path = []
        for img in img_listdir:
            images_full_path.append("./" + os.path.join(full_figures_path,img))

        # Define the chat messages with system and user roles
        messages = [
            {"role": "system", "content": "You are an assistant that analyzes academic papers. You are a specialist of computer vision."},
            {"role": "user", "content":   prompt} # Removed provider check, as format is standard
        ]
        
        # print(prompt)
        api_base = None
        if model_name.startswith("ollama/"):
            api_base = os.getenv("OLLAMA_BASE_URL") # Get Ollama base URL if using Ollama

        # try:
        start_time = time.time()
        
        # Set timeout and custom headers if needed, passed directly to completion
        timeout = 180 # Example timeout
        custom_headers = None
        if model_name.startswith("anthropic/"): # Example for Anthropic headers
             custom_headers = {"anthropic-beta": "pdfs-2024-09-25"}

        response = litellm.completion(
            model=model_name,
            messages=messages,
            # max_tokens=40000, # litellm might use different parameter names or defaults
            temperature=0.5,
            api_base=api_base, # Pass API base if needed (e.g., for Ollama)
            timeout=timeout, # Pass timeout
            headers=custom_headers # Pass custom headers if needed
            )
        analysis = response.choices[0].message.content.replace("```markdown\\n","").replace("```","")
        
        # remove the ####---#### at the end
        try:
            print(analysis.split("####---####")[0])
            analysis = analysis.split("####---####")[1]
            
        except:
            print("No separator found in {}".format(analysis))
        ## remove the first lines if they are empty but not after
        
        analysis = analysis.split("\n")
        # remove the first lines if they are empty but not after
        while len(analysis)>0 and analysis[0].strip() == "":
            analysis = analysis[1:]
        analysis = "\n".join(analysis)


        
        time_taken = time.time() - start_time
        try:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            print(f"Time taken: {time_taken:.2f} seconds")
            print(f"Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}")
        except AttributeError: # Handle cases where usage info might not be present
            print(f"Time taken: {time_taken:.2f} seconds")
            print("Token usage information not available in response.")

        analysis = analysis + "\n# Figures\n"
        for figure in img_listdir:
            analysis = analysis + "\n ![[" + loc_figures_path + "/" + figure + "]] \n"

        with open(output_path, 'w', encoding='utf-8') as out_file:
            out_file.write(analysis)

        print(f"Processed and saved analysis for {filename}.")







# Example usage
if __name__ == "__main__":
    import argparse

    # vault_path first arg
    parser = argparse.ArgumentParser(description='Process markdown files using Ollama API')
    parser.add_argument('vault_path', type=str, help='Path to the vault folder')
    parser.add_argument('file_name', type=str, help='Name of the file to process')
    args = parser.parse_args()


    vault_path= args.vault_path if args.vault_path!="." else "/home/pmarrec/vault"
    file_name=args.file_name if args.file_name!="." else None
    if file_name is not None and not file_name.endswith(".pdf"):
        print("Please provide a pdf file")
        exit(0)

    load_dotenv(find_dotenv())

    
    
    extract_folder = os.path.join(vault_path,local_extract_folder)
    output = os.path.join(vault_path,local_output_folder)  # path to the figures relative to the vault_path
    base_filename = os.path.basename(file_name)
    no_suff_filename = base_filename.split(".")[0]
    current_local_extract_folder = os.path.join(local_extract_folder,no_suff_filename,no_suff_filename,"auto")
    folder_extracted=os.path.join(vault_path,current_local_extract_folder)
    figures_path = os.path.join(current_local_extract_folder,"images")
    template_model = os.path.join(vault_path,template_path)
    os.makedirs(output, exist_ok=True)
    os.makedirs(extract_folder, exist_ok=True)
    os.makedirs(os.path.join(extract_folder,"images"), exist_ok=True)
    os.makedirs(folder_extracted, exist_ok=True)



    
    
    #with opena
    # model_name = "athene-v2" #"qwen2.5:32b" #"llama3.1:latest" #
    # model_name = "openai:gpt-4o-2024-11-20"
    # model_name = "anthropic:claude-3-5-sonnet-20241022"    
    # model_name = "deepseek:deepseek-reasoner"
    # model_name = "deepseek:deepseek-chat"
    # model_name = "genai:gemini-2.0-pro-exp-02-05"
    model_name = os.getenv("SUMMARY_MODEL",'gemini/gemini-2.0-flash') # Use litellm format
    print("Model name:",model_name)


    




    # Removed aisuite client initialization
    # client = ai.Client(
    #     provider_configs={
    #     "ollama": {"timeout": 180},
    #     "anthropic" : {"default_headers" : {
    #                         "anthropic-beta": "pdfs-2024-09-25"}
    #                         }})

   
    

    
    if file_name:
        # filepath=os.path.join(vault_path,file_name)
        # extract_single_pdf(filepath,figures_folder=figures_path,output_folder=extract_folder,table_dir=args.tab)
        scripts_folder = os.path.dirname(os.path.realpath(__file__))
        output_folder = os.path.join(local_extract_folder,os.path.basename(file_name).replace(".pdf",""))
        full_filename = os.path.join(folder_extracted,no_suff_filename+".md")
        print("full_filename",full_filename)
        if os.path.exists(full_filename):
            print("Already extracted")
        else:  
            subprocess.run(["bash",f"{scripts_folder}/run_minerU.sh", file_name, output_folder], check=True)

    if file_name:
        
        filepath = os.path.join(folder_extracted,no_suff_filename+".md")
        # process_single_md(filepath,vault_path,figures_path,output,template_model,client,tags,model_name=model_name,prompt=prompt,rules=rules) # Removed client argument
        process_single_md(filepath,vault_path,figures_path,output,template_model,tags=tags,model_name=model_name,prompt=prompt,rules=rules)

    else:
        print("Error: No file provided")
        # process_md_files(extract_folder, output,template_model,figures_path,rules,tags,model_name)

    print("Processed - done")

