from datasets import load_dataset

import evaluate
from transformers import pipeline
from tqdm import tqdm

dataset = load_dataset("HuggingFaceH4/MATH-500",trust_remote_code=True)  # or load from local files if you cloned the repo

def cosd_prompt(problem):
    return f"Problem: {problem}\n Think step by step, but only keep a minimum draft for each thinking step, with 5 words at most. You will describe all your process to find the relevant element. You will start with the overall plan and then you will developp each step with at least 5 steps. Return the answer and only the latex answer at the end of the response after a separator ####---####."


generator = pipeline("text-generation", model="Qwen/Qwen2.5-7B-Instruct",trust_remote_code=True,device="cuda:1")

results = []
max = 10
i=0
for ex in tqdm(dataset["test"]):
    
    prompt = cosd_prompt(ex["problem"])
    generated = generator(prompt, max_length=1024)[0]["generated_text"]
    print(len(generated))
    print(generated)
    generated = generated.split("####---####")
    while len(generated) <= 1:
        print("Retry")
        generated = generator(prompt, max_length=1024)[0]["generated_text"].split("####---####")
    generated = generated[1].strip()
    results.append({
        "problem": ex["problem"],
        "ground_truth": ex["answer"],
        "model_output": generated,
    })
    print("Problem:", ex["problem"])
    print("Ground truth:", ex["answer"])
    print("Model output:", generated)
    i+=1
    if i>=max:
        break
    
# accuracy_metric = evaluate.load("accuracy")
# # (Assume you have a function that extracts the final answer from generated text)
# pred_answers = [r["model_output"] for r in results]
# gt_answers = [r["ground_truth"] for r in results]
# accuracy = accuracy_metric.compute(predictions=pred_answers, references=gt_answers)
# print("Accuracy:", accuracy)
# print("Results:", results[0])
