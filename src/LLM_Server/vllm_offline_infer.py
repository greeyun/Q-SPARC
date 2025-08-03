from vllm import LLM, SamplingParams
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# give some qustions
prompts = [
    "Who are you？",
    "Where is the capital of New Zealand",
]


# init
sampling_params = SamplingParams(temperature=0.8, top_p=0.95, max_tokens=100)

# loading model
llm = LLM(model="/hpc/fxu244/Documents/Code/LLMs/Qwen3-0.6B", trust_remote_code=True, max_model_len=4096, gpu_memory_utilization=0.1) # gpu_memory_utilization 这个参数提前说明要占用多少比例的GPU，默认是90%

# output
outputs = llm.generate(prompts, sampling_params)

# print
for output in outputs:
    prompt = output.prompt
    generated_text = output.outputs[0].text
    print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")