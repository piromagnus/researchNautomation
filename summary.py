import os
import json
from pathlib import Path
import ollama
import time
import aisuite as ai
from dotenv import load_dotenv, find_dotenv
from pdf_extract import extract_texts_from_folder,extract_single_pdf
import base64
import subprocess  # added import for subprocess
# from pdf_minerU import parse_md

# def process_md_files(input_folder, output_folder,template_folder,figures_folder,rules,tags,
#  model_name="openai:gpt-4o-2024-11-20"):
#     """
#     Processes Markdown files by sending their content to the Ollama API to extract:
#     - A list of tags
#     - A summary of the paper with the main contributions
#     - A list of new concepts, architectures, and training methods with deep explanations

#     Args:
#         input_folder (str): Path to the folder containing Markdown (.md) files.
#         output_folder (str): Path to the folder where processed results will be saved.
#         model_name (str): Name of the Ollama model to use for processing.
#     """
#     # Ensure the output folder exists
#     os.makedirs(output_folder, exist_ok=True)
#     client = ai.Client()
#     # Iterate over all Markdown files in the input folder
#     for filename in os.listdir(input_folder):
#         if filename.lower().endswith('.md') and not filename.lower().endswith('_ref.md'):
            
#             md_path = os.path.join(input_folder, filename)
#             output_filename = "Paper - " + Path(filename).stem + '.md'
#             output_path = os.path.join(output_folder, output_filename)
#             if os.path.exists(output_path):
#                 # If the output file already exists, skip processing this Markdown file
#                 continue
#             #check if it does
#             with open(md_path, 'r', encoding='utf-8') as file:
#                 content = file.read()
#             with open(template_folder, 'r', encoding='utf-8') as file:
#                 template = file.read()
            
#             #remove all the \n from content

#             content = content.replace('\n', '')
#             # Prepare the prompt for the Ollama API


#             # Prepare the prompt for the Ollama API
#             prompt = (
#                 "You are a specialist of computer vision"
#                 "<template>\n" + template + "<\ template>\n"
#                 "<rules>" + "\n".join(rules) + "</rules>"
#                 "<tags>" + ", ".join(tags) + "<\ tags>"
#                 "Analyze the following academic paper in compute vision and provide the following information in the <format> following the <rules:\n"
#                 "1. A list of relevant tags within <tags>.\n"
#                 "2. A concise summary of the paper, highlighting the main contributions.\n"
#                 "3. A detailed list of new concepts, architectures, and training methods introduced, including deep explanations of each.\n\n"
#                 "Paper Content:\n" + content
#             )

#             # Define the chat messages with system and user roles
#             messages = [
#                 {"role": "system", "content": "You are an assistant that analyzes academic papers. You are a specialist of computer vision."},
#                 {"role": "user", "content": prompt}
#             ]
            
#             # print(prompt)

#             # try:
#             start_time = time.time()

#             response = client.chat.completions.create(
#                 model="openai:gpt-4o-2024-11-20",
#                 messages=messages,
#                 temperature=0.5)
#             analysis = response.choices[0].message.content
#             time_taken = time.time() - start_time
#             prompt_tokens = response.usage.prompt_tokens
#             completion_tokens = response.usage.completion_tokens
#             print(f"Time taken: {time_taken:.2f} seconds")
#             print(f"Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}")


           

#             #add the link in the format [[figures_folder/name]] based on the os.lisdir

#             listdir =    os.listdir(figures_path)
#             for figure in listdir:
#                 analysis = analysis + "\n ![[" + figures_path + "/" + figure + "]] \n"



#             with open(output_path, 'w', encoding='utf-8') as out_file:
#                 out_file.write(analysis)

#             print(f"Processed and saved analysis for {filename}.")

#             # except Exception as e:
#             #     print(f"Failed to process {filename}. Error: {e}")

def process_single_md(
    file_path: str,
    vault_path: str,
    loc_figures_path: str,
    output_folder: str,
    template_folder : str,
    client: ai.Client,
    tags: list = None,
    model_name: str = "openai:gpt-4o-2024-11-20",
    pdf_file: str = None,
    ) -> None:
        """Process a single markdown file and generate analysis."""

        input_folder = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        # figures_path = os.path.join(figures_path,filename.split(".")[0])
        # print("figures_path",figures_path)
        # quit()
        output_filename = "Paper - " + Path(filename).stem + '.md'
        output_path = os.path.join(output_folder, output_filename)

        full_figures_path = os.path.join(vault_path,loc_figures_path)
        os.makedirs(full_figures_path, exist_ok=True)
        img_listdir = os.listdir(full_figures_path)
        #sort
        img_listdir.sort()
        for img in img_listdir:
            full_img_path = os.path.join(full_figures_path,img)
            client.upload.upload_file(full_img_path,model_name.split(":")[0])

        if os.path.exists(output_path):
            # If the output file already exists, skip processing this Markdown file
            print("Already processed:", filename)
            return
        with open(template_folder, 'r', encoding='utf-8') as file:
            template = file.read()
        prompt = (
            "You are a specialist of computer vision"
            "You write in Markdown format using "
            "You will remove all space or tabulations on the first line after a subtitle"
            "You will use latex with $.$ or $$.$$  for math"
            "<template>\n" + template + "<\ template>\n"
            "<rules>" + "\n".join(rules) + "</rules>"
            "<tags>" + ", ".join(tags) + "<\ tags>"
            "The paper's filename is " + filename.replace(".md",".pdf") + "\n"
            "Analyze the following academic paper in compute vision and provide the following information in the <format> following the <rules:\n"
            "1. A list of relevant tags within <tags>.\n"
            "2. A detailled summary of the paper, highlighting the main contributions, type of input and output data for training and inference, type of learning methods\n"
            "3. A detailed list of new concepts, architectures, and training methods introduced, including deep explanations of each.\n\n"
            "4. A detailled explanation of the training stragegy (supervised, weakly-supervised, unsupervised, reinforcement learning or something else), the dataset used, the evaluation metrics and the results\n"
        )
        # Prepare the prompt for the Ollama API
        if pdf_file:
            with open(file_name, "rb") as pdf_file:
                binary_data = pdf_file.read()
                base64_encoded_data = base64.standard_b64encode(binary_data)
                base64_string = base64_encoded_data.decode("utf-8") 
            prompt = [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": base64_string}},
                {"type": "text", "text": prompt} 
            ]
        else:
            md_path = os.path.join(input_folder, filename)
           
            #check if it does
            with open(md_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            
            #remove all the \n from content

            content = content.replace('\n', '')
            prompt += "Paper Content:\n" + content
        
        # Define the chat messages with system and user roles
        messages = [
            {"role": "system", "content": "You are an assistant that analyzes academic papers. You are a specialist of computer vision."},
            {"role": "user", "content":   prompt}
        ]
        
        # print(prompt)

        # try:
        start_time = time.time()

        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            # max_tokens=40000,
            temperature=0.5)
        analysis = response.choices[0].message.content.replace("```markdown\n","").replace("```","")
        time_taken = time.time() - start_time
        try:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            print(f"Time taken: {time_taken:.2f} seconds")
            print(f"Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}")
        except:
            print(f"Time taken: {time_taken:.2f} seconds")


        

        #add the link in the format [[figures_folder/name]] based on the os.lisdir
        # figures_path = os.path.join(figures_path,filename.split(".")[0])
        
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
    parser.add_argument('tab', type=str, help='Direction of the tab (Up or Down)')
    parser.add_argument('--direct', action='store_true', help='Process a single file')
    args = parser.parse_args()


    if args.tab not in ["up","down"]:
        print("Please provide a valid tab direction")
        exit(0)

    vault_path= args.vault_path if args.vault_path!="." else "/home/pmarrec/vault"
    file_name=args.file_name if args.file_name!="." else None
    if file_name is not None and not file_name.endswith(".pdf"):
        print("Please provide a pdf file")
        exit(0)
    local_extract_folder ="Knowledge/automation/extract"

    root_folder=os.path.join(vault_path,"Knowledge/automation")
    
    pdf_folder = os.path.join(root_folder,"PDF_inbox")
    
    
    extract_folder = os.path.join(vault_path,local_extract_folder)
    
    output = os.path.join(root_folder,"Processed_pdf")
    
    os.makedirs(root_folder, exist_ok=True)
    os.makedirs(output, exist_ok=True)
    os.makedirs(extract_folder, exist_ok=True)
    os.makedirs(pdf_folder, exist_ok=True)

    figures_path = os.path.join(extract_folder,"images") # path to the figures relative to the vault_path
    os.makedirs(figures_path, exist_ok=True)
    # model_name = "athene-v2" #"qwen2.5:32b" #"llama3.1:latest" #
    template_model = os.path.join(vault_path,"Templates/summary.md")
    #with opena
    # model_name = "openai:gpt-4o-2024-11-20"
    # model_name = "anthropic:claude-3-5-sonnet-20241022"    
    # model_name = "deepseek:deepseek-reasoner"
    # model_name = "deepseek:deepseek-chat"
    # model_name = "ggenai:gemini-2.0-pro-exp-02-05"
    model_name = "genai:gemini-2.0-flash-exp"



    print("Model name:",model_name)
    load_dotenv(find_dotenv())
    client = ai.Client(
        provider_configs={
        "anthropic" : {"default_headers" : {
                            "anthropic-beta": "pdfs-2024-09-25"}
                            }})


    tasks_tags = [
        "TAD",
        "HPE",
        "Tracking",
        "Segmentation",
        "Object-detection",
        "NLP-based",
        "Vision-NLP",
        "Classification"
    ]

    rules = [
        "NEVER use \n but use instead \\ in the output"
        "Only use tags from the provided list",
        "Select tags that are directly relevant to the paper's content",
        "Always add Paper",
        "Use either Image for image only or Video if it process both images and video",
        "Use either foundation if it a paper on a backbone or fine-tuning if it is a paper that only use pretrained backbone",
        "Use either Transformers, CNN, SSM or Other",
        "Describe the tasks that is done by the paper with at least 1 tags in the ["+ ", ".join(tasks_tags)+"] list "
        "To illustrate the concept, You MUST use the images that are provided in the input with the caption in the format ![[images_path]] \n Figure i : Caption"
        "You will always use the same caption as the one in the input"
        "You will add all the figures with there caption under a # Figures title at the end of the file including images and tables."
    ]

    tags = [
            "Paper",
            "Transformers",
            "SSM",
            "CNN",
            "Other",
            "Image",
            "Video",
            "Fondation",
            "Fine-Tuning",
        ]
   
    base_filename = os.path.basename(file_name)
    no_suff_filename = base_filename.split(".")[0]
    current_local_extract_folder = os.path.join(local_extract_folder,no_suff_filename,no_suff_filename,"auto")
    folder_extracted=os.path.join(vault_path,current_local_extract_folder)
    figures_path = os.path.join(current_local_extract_folder,"images")
    os.makedirs(figures_path, exist_ok=True)
    os.makedirs(folder_extracted, exist_ok=True)
    # print( ", ".join(tags))
    if args.direct and model_name.split(":")[0] == "anthropic":
        filepath=os.path.join(extract_folder,base_filename).replace(".pdf",".md")
        pdf_path = os.path.join(vault_path,file_name)
        process_single_md(filepath,vault_path,figures_path,output,template_model,client,tags,model_name,pdf_file=pdf_path)
        print("Processed - done")
        quit()
    
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
    else:
        extract_texts_from_folder(pdf_folder, extract_folder)

    if file_name:
        
        filepath = os.path.join(folder_extracted,no_suff_filename+".md")
        os.makedirs(figures_path, exist_ok=True)

        process_single_md(filepath,vault_path,figures_path,output,template_model,client,tags,model_name)

    else:
        print("Error: No file provided")
        # process_md_files(extract_folder, output,template_model,figures_path,rules,tags,model_name)

    print("Processed - done")

