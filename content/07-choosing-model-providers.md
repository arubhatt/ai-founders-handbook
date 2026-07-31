---
part: Part III · The Stack
part_num: III
chapter_num: 7
title: Choosing Model Providers & Hugging Face
dek: Your model is a supplier, not a soulmate. How to pick one — closed API, open weight, or self-hosted — without betting the company on a vendor you'll want to leave in six months.
slug: 07-choosing-model-providers
reading_time: 22 min read
prev_url: index.html
prev_title: Ch 6 · Customer Validation for AI
next_url: index.html
next_title: Ch 8 · The Content & Data Stack
---

The single most consequential technical decision an AI startup makes in its first year is also the one founders agonize over least: **which model sits behind the product**. They will spend weeks on a logo and minutes on a choice that determines their gross margin, their latency, their failure modes, their compliance surface, and — if they're careless — their independence. This chapter is about making that choice deliberately, and building it so you can unmake it.

The good news for a 2026 founder is that you almost certainly should not train a model. The bad news is that "just use an API" hides a dozen sub-decisions, each with a cost attached. We'll walk the whole decision tree — from the build-versus-buy spectrum, through frontier providers, the open-weight route on Hugging Face, and the inference layer that quietly sets your unit economics — and we'll make every decision concrete by watching **Cortex**, our running example, an autonomous customer-support agent that resolves tickets end-to-end for mid-market SaaS companies.

:::definition Open weights ≠ open source
"Open weight" means the trained parameters are downloadable and you can run the model yourself. It says nothing about the *license*. A model can be open weight yet legally restricted (Llama's community license), while "open source" in the OSI sense — freedom to use, study, modify, and redistribute for any purpose — is rarer than the marketing implies. Always separate the artifact (weights you can download) from the rights (what the license lets you do with them).{sn: This distinction bites startups constantly: teams download a model, ship it, and only discover the acceptable-use or scale clauses during an acquisition's due diligence.}
:::

## The build-versus-buy spectrum

There is no single "build or buy" switch. There is a spectrum of ownership, and each step to the right buys you control at the price of capital, talent, and time.

{figure: diagrams/model-decision-tree.svg | **Figure 7.1** — The model-sourcing decision tree. Most startups should live in the left two branches for as long as possible; every step right adds a standing engineering and compliance cost.}

At the far left, you call a **frontier API** (OpenAI, Anthropic, Google) and rent intelligence by the token. At the far right, you **pretrain** your own foundation model — a path that in 2026 costs eight figures and a research team, and is almost never the right first move for a startup whose moat is a product, not a model.{sn: If your investors are excited that you're *training a foundation model*, be sure the excitement is about a genuine data or architecture advantage — not resume-driven development. The graveyard of 2023–2025 is full of startups that raised to train models they could have rented.} In between sit two options founders routinely overlook: **prompting and retrieval** on a hosted model (cheap, fast, reversible) and **fine-tuning or adapting** an open-weight model you host yourself (more control, real MLOps burden).

The heuristic that has aged well: **move right only when a concrete, measured limitation of the cheaper option forces you to.** Not because open weights feel more defensible, not because self-hosting feels cheaper on a spreadsheet — but because you hit a wall on quality, cost, latency, data residency, or availability that the option to your left cannot clear.

:::rule Founder's Rule
Rent capability until renting demonstrably fails you. The moment your data flywheel, your margins, or your compliance obligations *require* ownership, you'll know — with numbers, not vibes.
:::

For Cortex, this framing settles the first argument fast. Their moat is the resolution workflow and the proprietary ticket-outcome data they accumulate — not the base model. They start by renting a frontier API, instrument everything, and keep the option to move right open by never coupling their code to one vendor's SDK (more on that at the end of the chapter).

## Choosing a frontier model provider

If you're renting, you're choosing among a handful of frontier labs whose flagship models cluster within a few dozen Elo points of one another on public leaderboards.{sn: The public yardstick most founders cite is **Arena** (the artist formerly known as LMArena / LMSYS Chatbot Arena, rebranded January 2026), which ranks models by human pairwise votes fed into a Bradley–Terry/Elo model. Treat it as a signal of general preference, not of *your* task performance — which only your own evals measure (Chapter 6).} The July 2026 landscape alone saw four frontier releases in six weeks — Claude Fable 5, Grok 4.5, the GPT-5.6 family, and Kimi K3[^arena] — so any table of "best model" is stale on arrival. Choose on the **dimensions that don't churn**, not on this week's top of the leaderboard.

Seven dimensions decide a provider. Weight them for *your* workload:

| Dimension | Why it matters for a startup | How to test it |
|---|---|---|
| Task quality | Leaderboards ≠ your task. A model that tops Arena may lose on your tickets. | Your own eval set (Ch 6), not vibes |
| Latency & throughput | Agentic products make many calls per action; p95 latency compounds. | Load-test at your real prompt sizes |
| Price per token | Sets your COGS and gross margin (Ch 13). | Blended input+output at your ratio |
| Context window | Long context can replace retrieval complexity — at a price. | Test quality *and* cost at full length |
| Data & privacy policy | Enterprise buyers ask "do you train on our data?" in the security review. | Read the DPA; get zero-retention in writing |
| Reliability & rate limits | An outage in your provider is an outage in your product. | Check status history; negotiate limits |
| Roadmap & deprecation | Models get retired; your prompts are tuned to a version. | Ask the deprecation policy up front |

A few 2026 realities worth internalizing before you read any pricing page:

- **Price spans a ~600× range**, from ultra-budget "nano" tiers around $0.10 per million input tokens to premium reasoning models at $60+ per million output tokens.[^cloudzero] Output tokens cost two-to-six times input across every provider — so your input/output *ratio*, not the headline number, drives cost.
- **Cached input is ~90% cheaper** at OpenAI, Anthropic, and Google, which makes effective cost nearly equal for cache-heavy workloads and rewards prompt architectures that keep a stable prefix.[^finout]
- **Batch APIs give a flat ~50% discount** for work that tolerates up to 24 hours of latency — offered by OpenAI, Anthropic, Google, and Alibaba.[^cloudzero] Cortex runs its nightly eval suite and ticket-summarization backfills on the batch tier and halves that line item.
- **Large-context pricing differs sharply.** Some providers charge a surcharge past 200K tokens; others (Anthropic's Sonnet/Opus tiers) offer 1M-token context at a flat rate.[^finout] If your architecture leans on long context, this one clause can dominate your bill.

{case: **In the wild** — Cortex benchmarked three frontier tiers on 500 real anonymized tickets scored by their resolution eval. The mid-tier model resolved 91% as many tickets as the premium model at **28% of the cost**. They route the easy 80% of tickets to the mid-tier model and escalate only ambiguous cases to the premium one — a pattern we generalize below.}

:::warning Read the data-use clause before the pricing
The cheapest way to lose an enterprise deal is to discover, during their security review, that your model provider trains on prompts by default. Confirm zero-retention / no-training terms in the DPA, in writing, *before* you build on a provider — not after a buyer's legal team asks. This is a Chapter 11 sales problem you prevent here in Chapter 7.
:::

## The open-weight route and Hugging Face

The moment your workload is high-volume, latency-sensitive, privacy-constrained, or simply expensive at frontier prices, the open-weight route earns a serious look. In 2026 the open frontier is genuinely strong: Qwen 3.5, DeepSeek V4, Llama 4, Mistral Large 3, GLM-5, Kimi, and Gemma 4 all ship downloadable weights, and several trade blows with closed models on coding and reasoning benchmarks.[^hfopen]

**Hugging Face is the center of gravity** for finding, evaluating, and pulling these models. Reading a model's page like an engineer — not a tourist — is a skill worth developing:

- **The model card** is the spec sheet: intended use, training data disclosure, benchmark claims, known limitations, and the prompt/chat template you must match exactly or quality collapses.
- **The license** (top of the page) governs whether you can ship it at all — covered in its own section below because it's where startups get hurt.
- **Leaderboards** such as Hugging Face's Open LLM Leaderboard score models on reproducible public benchmarks (IFEval, BBH, MATH, GPQA, MUSR, MMLU-PRO).[^hflb] Use them to *shortlist*, then confirm on your own evals — public benchmarks leak into training data and reward the wrong things.
- **File format** signals how you'll run it. `safetensors` is the standard, safe-to-load tensor format for GPU serving; `GGUF` bundles weights plus metadata for efficient CPU/edge and local inference via runtimes like llama.cpp.[^gguf]
- **Quantization** (e.g., 4-bit/8-bit GGUF or AWQ builds) trades a little quality for large memory and cost savings — often the difference between needing one GPU and needing four.

:::definition Quantization
Compressing a model's weights to fewer bits per parameter (16-bit → 8- or 4-bit) to shrink memory and speed up inference. A well-quantized model keeps most of its quality at a fraction of the hardware cost — but "most" is task-dependent, so quantization is a change you must re-run your evals against, not a free lunch.
:::

```python
# A model choice is reversible when it hides behind an interface.
# Cortex defines one Provider protocol; every backend implements it.
from typing import Protocol

class Provider(Protocol):
    def complete(self, messages: list[dict], **kw) -> str: ...

class OpenAICompatible:
    """Works for OpenAI, and for Together / Fireworks / Groq / vLLM,
    which all expose an OpenAI-compatible endpoint — swap base_url only."""
    def __init__(self, base_url: str, api_key: str, model: str):
        from openai import OpenAI
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def complete(self, messages, **kw) -> str:
        r = self.client.chat.completions.create(
            model=self.model, messages=messages, **kw)
        return r.choices[0].message.content

# Switching an open-weight host is a one-line config change, not a rewrite:
gpt   = OpenAICompatible("https://api.openai.com/v1", KEY, "gpt-5.6-terra")
qwen  = OpenAICompatible("https://api.together.xyz/v1", KEY, "Qwen/Qwen3.5-235B")
```

### The license is the landmine

Downloadable does not mean usable-in-your-product. Licenses fall into tiers, and the difference between them is the difference between a clean acquisition and a diligence disaster.[^presenc]

| License | Commercial use | Catch for startups | 2026 examples |
|---|---|---|---|
| Apache 2.0 | Yes, unrestricted | None — no scale, field, or MAU limits | Qwen 3.5, Gemma 4 |
| MIT | Yes, unrestricted | None | DeepSeek V4 |
| Llama Community | Yes, with limits | 700M-MAU ceiling; can't train other models on outputs; **not licensed to EU-based entities for multimodal** | Llama 4 Scout |
| Gemma / custom | Usually yes | Vendor-specific acceptable-use terms | (pre-2026 Gemma) |
| OpenRAIL-M | Conditional | Use-case restrictions travel with the weights | Various |
| CC-BY-NC | **No** | Research/non-commercial only | Some research models |

Apache 2.0 is now the most-adopted open-weight license — roughly 38% of new Hugging Face releases in 2026 — precisely because it removes this friction.[^presenc] The unconditional-for-commerce picks are **DeepSeek V4 (MIT), Qwen 3.5 (Apache 2.0), and Gemma 4 (Apache 2.0** — Google dropped its custom terms in April 2026).[^presenc]

:::warning The Llama EU trap
Meta's community license carries a 700-million-monthly-active-user ceiling, forbids using Llama outputs to train non-Llama models, and — critically — its **multimodal** models are *not licensed to companies domiciled in the EU*.[^presenc] If you're an EU startup, or plan to sell into one, or might be acquired by one, a permissive Apache/MIT model removes a whole category of legal risk. Cortex, eyeing European customers, ruled Llama's multimodal line out on this clause alone.
:::

## The inference layer sets your margins

Choosing an open-weight *model* is only half the decision; you still have to *serve* it. This is where founders who "went open to save money" sometimes discover they've traded a predictable API bill for an unpredictable GPU bill. Four options, roughly in order of increasing operational burden:

| Option | You manage | Best when | Watch out for |
|---|---|---|---|
| Serverless token API (Together, Fireworks, inference.net) | Nothing | You want open models at open prices, fast | Per-token price varies 20%+ for the *same* model across hosts |
| Speed-optimized host (Groq) | Nothing | Latency is the product (real-time agents/voice) | Model selection narrower; price ≠ always lowest |
| Managed GPU / dedicated (Baseten, dedicated endpoints) | Config, autoscaling | Steady high volume; need isolation/SLAs | You pay for idle capacity |
| Self-host (vLLM/TGI on your cloud) | Everything | Scale, data residency, or custom kernels demand it | Real MLOps headcount (Ch 9) |

Two 2026 facts reshape this table. First, the **same open model can cost 20% more on one serverless host than another** — Llama 4 Maverick input tokens run meaningfully cheaper on Fireworks than on Together, for identical weights.[^inference] Shop the model, then shop the host. Second, **NVIDIA's Blackwell generation cut cloud inference cost roughly 10×** versus the prior generation, which is why serverless open-model pricing kept falling through 2026 and why "self-host to save money" is a weaker argument than it was two years ago.[^nvidia]

{case: **In the wild** — Groq's custom LPU hardware is purpose-built for inference throughput; teams building real-time voice and agentic loops choose it when *time-to-first-token* is the felt product quality, even when a token-for-token comparison isn't the cheapest. The lesson: the "best" inference provider is defined by your dominant constraint — cost, speed, or control — not a universal ranking.}

:::rule Founder's Rule
Decouple the model from the plumbing. If switching providers costs you more than a config change and a re-run of your eval suite, you don't have a supplier — you have an owner.
:::

## Putting it together: route, don't marry

The mature 2026 pattern isn't "pick the one model." It's a **portfolio**: a router that sends each request to the cheapest model that clears your quality bar, escalates hard cases, and fails over when a provider degrades. This is how you get frontier quality where it matters and open-weight economics everywhere else.

Cortex's final architecture, arrived at empirically:

- **Tier 1 (≈80% of tickets):** an open-weight model (Qwen 3.5, Apache-licensed) on a serverless host — cheap, fast, EU-clean.
- **Tier 2 (ambiguous tickets):** a frontier model, called only when Tier 1's confidence or eval score is low.
- **Fallback:** a second provider behind the same `Provider` interface, so a frontier outage degrades Cortex to "slower and pricier," never "down."
- **Everything measured:** every routing decision logged and scored against the resolution eval, so the routing thresholds are tuned with data (Ch 6), and the unit economics are known to the cent (Ch 13).

This gives Cortex the two things a single-vendor bet never can: **negotiating leverage** (a credible threat to leave) and **resilience** (no single point of failure). The cost is one interface and a router — cheap insurance against the fastest-moving supply market in tech.

:::takeaways Key takeaways
- **Model choice is a supplier decision, not an identity.** Rent capability until a measured limit forces you rightward on the build-vs-buy spectrum.
- **Choose providers on durable dimensions** — quality on *your* evals, latency, price, context, data policy, reliability, deprecation — not this week's leaderboard.
- **Exploit the pricing structure**: cached input (~90% off), batch tiers (~50% off), and input/output ratio matter more than the headline rate.
- **On Hugging Face, read the card, the leaderboard, the format, and — above all — the license.** Apache 2.0 / MIT (Qwen, DeepSeek, Gemma 4) are the clean commercial picks; Llama's license carries MAU and EU-multimodal traps.
- **The inference layer sets your margins.** Shop the host after you shop the model; serverless open-model pricing keeps falling.
- **Route, don't marry.** A provider-agnostic interface plus a quality-based router buys you leverage and resilience for the price of one abstraction.
:::

:::exercise Hands-on: the Provider Selection Scorecard
Build a one-page scorecard for *your* product before you write a line of integration code.

1. **Weight the seven dimensions** (quality, latency, price, context, data policy, reliability, deprecation) 0–5 for your workload. Which two dominate?
2. **Assemble a 100-example eval set** from real or realistic inputs, with a scoring rule a stranger could apply (Chapter 6).
3. **Score three candidates** — one frontier API, one open-weight-on-serverless, one wildcard — on your evals, measuring quality, p95 latency, and blended cost per request at your real input/output ratio.
4. **Draft your routing rule**: which tier handles the common case, what triggers escalation, and what the fallback is.
5. **Write the exit test**: how many lines of code, and how long, to switch your primary provider? If the answer is more than "a config change and a re-run," refactor behind an interface now.
:::

[^arena]: Arena (formerly LMArena / LMSYS Chatbot Arena), live model leaderboard, 2026. <https://lmarena.ai>
[^cloudzero]: CloudZero, "LLM API Pricing Comparison In 2026: Every Major Model, Ranked By Cost." <https://www.cloudzero.com/blog/llm-api-pricing-comparison/>
[^finout]: Finout, "OpenAI vs Anthropic API Pricing Comparison (2026)." <https://www.finout.io/blog/openai-vs-anthropic-api-pricing-comparison>
[^inference]: Inference.net, "LLM API Pricing Comparison 2026: 30+ Models, Every Provider." <https://inference.net/content/llm-api-pricing-comparison/>
[^hfopen]: Hugging Face, "The Best Open Source and Open-Weight LLM Models to Run Locally in 2026." <https://huggingface.co/blog/daya-shankar/open-source-llm-models-to-run-locally>
[^hflb]: Hugging Face, "Leaderboards and Evaluations" (docs). <https://huggingface.co/docs/leaderboards/index>
[^gguf]: Hugging Face, "GGUF" (Hub docs). <https://huggingface.co/docs/hub/gguf>
[^presenc]: Presenc AI, "Open-Weight License Landscape 2026." <https://presenc.ai/research/open-weight-license-landscape-2026>
[^nvidia]: NVIDIA, "NVIDIA Blackwell Cuts Cloud LLM Inference Costs 10× — The 2026 Pricing Landscape." <https://perspectives.nvidia.com/cloud-accelerator-pricing-llm-inference-scale-2026/>
