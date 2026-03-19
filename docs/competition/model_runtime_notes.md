# Model Runtime Notes

Primary competition model target:

- `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16`

Current working assumptions from the linked model references:

- Transformers path uses `AutoTokenizer` and `AutoModelForCausalLM` with `trust_remote_code=True`.
- Recommended load settings include `torch_dtype=torch.bfloat16` and `device_map="auto"`.
- Reasoning is enabled by default in the chat template.
- Reasoning-off mode should be expressed as `enable_thinking=False` in the chat template when the serving stack supports it.
- NVIDIA's published examples recommend `temperature=1.0` and `top_p=1.0` for reasoning tasks.
- Budget control is model-specific and may require either chat-template-aware serving or a dedicated two-step client flow depending on the runtime.

Implications for this repo:

- Local experimentation can still use OpenAI-compatible endpoints, but the request shape should stay compatible with Nemotron-specific chat-template flags where possible.
- Kaggle submission runtime should target the actual model package and published code path, not a generic hosted API assumption, until the competition rules prove otherwise.
