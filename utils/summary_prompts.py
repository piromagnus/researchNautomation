
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

rules = [
        "NEVER use \n but use instead \\ in the output "
        "Only use tags from the provided list ",
        "Select tags that are directly relevant to the paper's content ",
        "Always add Paper ",
        "Use either Image for image only or Video if it process both images and video",
        "Use either foundation if it a paper on a backbone or fine-tuning if it is a paper that only use pretrained backbone",
        "Use either Transformers, CNN, SSM or Other",
        "Describe the tasks that is done by the paper with at least 1 tags in the ["+ ", ".join(tasks_tags)+"] list "
        "To illustrate the concept, You MUST use the images that are provided in the input with the caption in the format ![[images_path]] \n Figure i : Caption"
        "You will always use the same caption as the one in the input"
        "You will add all the figures with there caption under a # Figures title at the end of the file including images and tables.",
        "You write in Markdown format",
        "You will remove all space or tabulations on the first line after a subtitle",
        "You will use latex with $.$ or $$.$$  for math",
    ]

prompt = """ You are a helpful assistant that summarizes academic papers in computer vision. 
            You are a specialist of computer vision
            
            <template>\n {} <\ template>\n
            <rules> {} </rules>
            <tags> {} <\ tags>
            The paper's filename is {} \n
            Analyze the following academic paper in compute vision and provide the following information in the <format> following the <rules:\n
            1. A list of relevant tags within <tags>.\n
            2. A detailled summary of the paper, highlighting the main contributions, type of input and output data for training and inference, type of learning methods\n
            3. A detailed list of new concepts, architectures, and training methods introduced, including deep explanations of each.\n\n
            4. A detailled explanation of the training stragegy (supervised, weakly-supervised, unsupervised, reinforcement learning or something else), the dataset used, the evaluation metrics and the results\n

            Think step by step, but only keep a minimum draft for each thinking step, with 5 words at most. Return the answer at the end of the response after a separator ####---####.
        
        """