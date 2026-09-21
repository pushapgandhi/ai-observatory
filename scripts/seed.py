"""Source-checked historical selection. Dates are the linked publication's date."""
import json
from pathlib import Path

ROWS = [
('2022-03-29','Research','DeepMind','Chinchilla revisits compute-optimal model training','Studies how model size and training-token counts should scale together under a fixed compute budget.','https://arxiv.org/abs/2203.15556'),
('2022-10-20','Research','Google Research','FLAN scales instruction tuning','Investigates how task diversity, model scale, and chain-of-thought data affect the generalization of instruction-tuned language models.','https://arxiv.org/abs/2210.11416'),
('2023-02-27','Research','Meta','LLaMA releases efficient foundation models for research','Introduces models trained on publicly available datasets, examining the capabilities of smaller models trained on more tokens.','https://arxiv.org/abs/2302.13971'),
('2023-03-15','Research','OpenAI','GPT-4 technical report documents multimodal capabilities','Reports a model that accepts images and text, along with evaluations, training-scaling observations, and limitations.','https://arxiv.org/abs/2303.08774'),
('2023-05-23','Research','University of Washington','QLoRA reduces the memory cost of fine-tuning','Combines frozen four-bit model weights with low-rank adapters to make large-model fine-tuning more accessible.','https://arxiv.org/abs/2305.14314'),
('2023-07-18','Research','Meta','Llama 2 shares pretrained and chat models','Details the training and evaluation of pretrained and dialogue-tuned language models, with released weights under a community license.','https://arxiv.org/abs/2307.09288'),
('2023-12-19','Research','Google DeepMind','Gemini technical report describes a multimodal model family','Describes a model family designed to work across text, images, audio, and video, with technical evaluations and limitations.','https://arxiv.org/abs/2312.11805'),
('2024-07-31','Research','Meta','The Llama 3 report documents an expanded model family','Presents the training, post-training, and evaluation of Llama 3 models, including larger-scale and multilingual capabilities.','https://arxiv.org/abs/2407.21783'),
('2021-02-26','Research','OpenAI','CLIP: learning vision from natural language','Pairs images with text to learn visual representations that transfer to new tasks without task-specific training.','https://arxiv.org/abs/2103.00020'),
('2021-06-17','Research','Microsoft','LoRA makes large-model adaptation more efficient','Freezes original model weights and trains small low-rank updates, reducing the cost of adapting large language models.','https://arxiv.org/abs/2106.09685'),
('2021-07-15','Research','DeepMind · Nature','AlphaFold predicts protein structures with high accuracy','A neural network approach demonstrates highly accurate protein structure prediction, expanding the role of AI in structural biology.','https://www.nature.com/articles/s41586-021-03819-2'),
('2021-12-20','Research','LMU Munich · Heidelberg','Latent diffusion brings high-resolution synthesis within reach','Runs diffusion in a compressed representation to reduce computation while supporting flexible image generation.','https://arxiv.org/abs/2112.10752'),
('2022-01-28','Research','Google Research','Chain-of-thought prompting improves reasoning','Worked reasoning examples help large language models solve arithmetic, symbolic, and commonsense reasoning tasks.','https://arxiv.org/abs/2201.11903'),
('2022-03-04','Research','OpenAI','InstructGPT learns from human feedback','Human demonstrations and preference rankings help align language-model responses with the intent of a user request.','https://arxiv.org/abs/2203.02155'),
('2022-05-27','Research','Stanford','FlashAttention makes exact attention more efficient','An IO-aware attention algorithm reduces transfers between GPU memory layers, improving speed and memory use for long sequences.','https://arxiv.org/abs/2205.14135'),
('2022-11-30','Models','OpenAI','ChatGPT opens conversational AI to the public','A public research preview introduces a dialogue interface for follow-up questions, instruction following, and iterative assistance.','https://openai.com/index/chatgpt/'),
('2023-04-05','Research','Meta','Segment Anything introduces promptable image segmentation','A model and large mask dataset enable flexible object segmentation, with zero-shot transfer to new image distributions.','https://arxiv.org/abs/2304.02643'),
('2023-05-29','Research','Stanford','Direct Preference Optimization simplifies alignment','Learns from preference pairs using a classification-style objective, avoiding a separate reward model and reinforcement-learning training loop.','https://arxiv.org/abs/2305.18290'),
('2024-02-15','Models','Google DeepMind','Gemini 1.5 expands long-context understanding','Google introduces a new model generation with substantially longer context, designed to work across text, video, audio, and code.','https://blog.google/innovation-and-ai/products/google-gemini-next-generation-model-february-2024/'),
('2024-05-13','Models','OpenAI','GPT-4o brings text, vision, and audio together','A multimodal model processes text, images, and audio in a single architecture, with faster spoken interaction and broader ChatGPT access.','https://openai.com/index/hello-gpt-4o/'),
('2025-01-22','Research','DeepSeek','DeepSeek-R1 explores reasoning through reinforcement learning','Reports reasoning models trained with reinforcement learning and releases model weights alongside smaller distilled models.','https://arxiv.org/abs/2501.12948'),
('2025-03-25','Models','Google DeepMind','Gemini 2.5 introduces a thinking model','Gemini 2.5 Pro Experimental combines a stronger base model with post-training aimed at reasoning, coding, and complex problem solving.','https://blog.google/innovation-and-ai/models-and-research/google-deepmind/gemini-model-thinking-updates-march-2025/'),
('2025-05-22','Models','Anthropic','Claude 4 advances coding and tool-assisted reasoning','Claude Opus 4 and Sonnet 4 introduce extended thinking with tool use and capabilities aimed at longer agent workflows.','https://www.anthropic.com/news/claude-4'),
('2025-08-07','Models','OpenAI','GPT-5 combines fast responses and deeper reasoning','OpenAI introduces a unified system that routes between quick responses and deeper reasoning, with expanded coding and multimodal capabilities.','https://openai.com/index/introducing-gpt-5/'),
('2026-09-02','Models','Google DeepMind','Gemini 3.8 Flash and Flash Cyber arrive','Google announces models focused on agent workflows and coding, including a variant designed for cybersecurity work.','https://blog.google/innovation-and-ai/models-and-research/gemini-models/3-8-flash-and-3-8-flash-cyber/'),
('2026-09-03','Models','OpenAI','GPT-6 Astra targets complex professional work','OpenAI introduces a model with reported advances in computer use, software engineering, science, and multi-step professional tasks.','https://openai.com/index/gpt-6-astra/'),
('2026-09-03','News','OpenAI','OpenAI publishes the GPT-6 Astra safety overview','The overview describes capability evaluations and safeguards accompanying the model launch, with a link to its full system card.','https://openai.com/index/safety-overview-gpt-6-astra/'),
('2026-09-09','News','Google','Google updates its AI subscription features','New plan features extend AI assistance across productivity apps, with availability varying by plan and region.','https://blog.google/products-and-platforms/products/google-one/fall-2026-ai-plan-updates/'),
('2026-09-15','Models','Google DeepMind','Gemini 3.8 Live adds more capable voice interaction','Two live dialogue models target conversational efficiency and more complex voice-driven tasks, including an extended-thinking variant.','https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-8-live-gemini-3-8-live-extended-thinking/'),
('2026-09-15','News','Google','Gemini Notebook adds new study tools','Google announces live conversations and interactive learning overviews for working with notebook sources.','https://blog.google/innovation-and-ai/products/gemini-notebook/new-study-tools-september-2026/'),
]

if __name__ == '__main__':
    path=Path(__file__).resolve().parents[1]/'dist'/'data.json'
    old=json.loads(path.read_text('utf-8')) if path.exists() else {'lastChecked':'2026-09-20','feeds':[],'entries':[]}
    merged={e['url'].rstrip('/'):e for e in old['entries']}
    for date,kind,publisher,title,summary,url in ROWS:
        merged[url.rstrip('/')] = dict(date=date,type=kind,publisher=publisher,title=title,summary=summary,url=url,automated=False)
    old['entries']=sorted(merged.values(),key=lambda e:(e['date'],e['title']),reverse=True)
    path.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Seeded {len(ROWS)} verified milestones; {len(merged)} total entries')
