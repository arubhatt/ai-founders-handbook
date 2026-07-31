---
part: Part I - Foundations
part_num: I
chapter_num: 2
title: "AI Fundamentals I: Models, Modalities & Inference"
dek: The technical bedrock every founder must hold in their head: what these models are, and what it actually costs to run them.
slug: 02-ai-fundamentals-models
reading_time: 18 min read
---

You do not need to derive backpropagation to build an AI company, but you do need a mechanical model of what happens between a user's request and a billed invoice — because that model is your product's cost structure, its latency budget, and half its defensibility. This chapter is that physics: the smallest complete set of ideas about models, modalities, and inference that lets a non-researcher founder make correct architecture and cost decisions under pressure.

We build the picture bottom-up — tokens, transformers, modalities, the taxonomy of models you actually choose between, and the economics of running them — and we keep coming back to **Cortex**, our running example: an autonomous customer-support agent for mid-market SaaS companies. Cortex reads a support ticket, checks the customer's account, and either resolves it or escalates. Every abstract idea here becomes, for Cortex, a line on a cost sheet.

## From tokens to transformers, for founders

A **language model** does exactly one thing: given a sequence of **tokens**, it predicts a probability distribution over the next token. Everything else — chat, code, agents — is scaffolding around that single primitive, repeated. This loop is where your bill comes from.

A token is a chunk of text, roughly 3-4 characters or about 0.75 English words. {sn: A blunt but load-bearing heuristic: **1 token ≈ 4 characters ≈ 0.75 words**. 1,000 English words ≈ 1,350 tokens. Code, JSON, and non-Latin scripts tokenize *worse* — often 1.5-3x more tokens per visible character.} The model never sees letters; it sees integer token IDs produced by a **tokenizer**. This matters commercially for two reasons. First, **you are billed per token, not per word or per request** — so the shape of your data determines your margin. Cortex's tickets are cheap prose, but the account JSON, API logs, and knowledge-base articles it stuffs into context are token-dense; a naive "just include everything" prompt can quadruple the input bill. Second, tokenization is language- and format-specific: the same Cortex flow costs materially more to serve a German or Japanese customer than an English one, purely from tokenization overhead. Bake that into pricing before a design partner in Munich becomes your worst-margin account.

The dominant architecture remains the **transformer**, and the one mechanism a founder must internalize is **attention**: to predict the next token, the model weighs its relevance against *every* prior token in the sequence. That "against every prior token" is the source of both the technology's magic and its cost curve. It is why context is powerful — the model can genuinely reason over a whole ticket thread — and why long context is expensive and slow, a tension we quantify later in this chapter.

:::definition
**Autoregressive generation** - The model produces output one token at a time, and each new token is fed back in as input to produce the next. A 500-token answer is 500 sequential forward passes through the network. This serial dependency, not raw model size, is why generation feels like typing rather than appearing instantly — and it is the single most important fact about inference cost.
:::

Two facts fall out of autoregression and govern your entire cost model. **Input tokens are cheap; output tokens are expensive** — typically 4-5x the price — because input is processed in one parallel pass while output must be generated serially. And **you cannot fully predict a request's cost in advance**, because output length is emergent. A support agent that "thinks out loud" or over-explains is not just annoying; it is a variable-cost leak on every ticket.

:::rule
**Founder's Rule 2.1** - Every product decision is a token decision. If you cannot estimate the input and output tokens of your core action on the back of a napkin, you do not yet understand your unit economics.
:::

## Modalities: text, vision, audio, multimodal

A **modality** is a type of data the model can consume or produce: text, images, audio, video. The 2026 frontier is **natively multimodal** — a single model that ingests and reasons across text, images, and audio in one forward pass, rather than bolting a separate vision or speech model onto a text core. This is a genuine capability shift, and it reshapes what products are buildable.

Modalities are priced and metered differently, and conflating them is a classic founder error. Images are converted to tokens by tile — a high-resolution screenshot can cost hundreds to low-thousands of input tokens. Audio is metered per **audio token** or per minute of stream, at a steep premium over text. OpenAI's **GPT-Realtime-2**, shipped May 2026, runs roughly **$32 per million audio-input tokens and $64 per million audio-output tokens** — an order of magnitude above text — with cached audio input far cheaper.[^realtime] Google's **Gemini 3.1 Flash** exposes a Live API for streaming voice and vision, with audio output around **$20 per million tokens**.[^gemini-live] Voice is not "text with a microphone"; it is a different cost class.

{sn: Rule of thumb for 2026: **audio ≈ 10-30x text per token, images ≈ hundreds-to-thousands of tokens each, video ≈ don't, unless it's the product.** Price the modality before you promise the feature.}

For Cortex, the modality decision is concrete. Most tickets are **text**: chat transcripts, emails, form fields — the cheap, obvious backbone. But a meaningful slice include a **screenshot** ("here's the error I'm seeing"), and a native-vision model that reads the screenshot directly, versus a human tagging it or a separate OCR service, is the difference between one-pass resolution and a multi-hop pipeline. The team's decision: text is the default path; **vision is invoked conditionally**, only when an image is attached, so the expensive modality is billed only when it earns its keep. **Voice** — a customer phoning support and Cortex answering live over a real number, now trivial via the Realtime API over SIP — is deferred to a later phase, precisely because at $32/$64 per million audio tokens it would dominate the cost model before the text product is proven.

:::warning
Native multimodality makes new features *technically* free to attempt and *financially* dangerous to ship by default. "Cortex can now answer phone calls" is a one-line API change and a 10-30x per-interaction cost increase. Modality expansion is a pricing decision disguised as a feature.
:::

## Open vs closed, dense vs mixture-of-experts, reasoning models

You are not choosing "an AI." You are choosing a point in a three-axis taxonomy, and each axis independently moves cost, control, and capability. (Which *specific* provider and model to sign with is Chapter 7's job; here we build the map so that choice is informed.)

### Axis 1: open-weights vs closed / API

**Closed models** (accessed only via a paid API — the frontier Claude, GPT, and Gemini families) give you top capability with zero infrastructure, but you rent them: the vendor sets the price, owns the roadmap, can deprecate a model under you, and sees your traffic. **Open-weights models** (weights you download and self-host — the DeepSeek, Qwen, Llama, GLM, and Kimi families) give you control, data residency, and a per-token cost that trends toward raw compute, but you own the serving problem: GPUs, autoscaling, evals (see Chapter 6), uptime. The 2026 reality is that the open-weights frontier is genuinely close on many tasks. The gap is no longer "toy vs frontier"; it is "who carries the operational burden."

{case: **GLM-5.2, June 2026** - Z.ai released [GLM-5.2](https://wavect.io/blog/open-weight-llm-comparison-2026/), a 744B-parameter mixture-of-experts model with ~40B active parameters, a 1M-token context window, MIT-licensed weights, and selectable reasoning-effort levels — a credible open-weights alternative to closed frontier models for teams willing to self-host or use a hosting provider.}

### Axis 2: dense vs mixture-of-experts

A **dense** model activates all its parameters for every token. A **mixture-of-experts (MoE)** model is partitioned into many "expert" sub-networks, and a lightweight **router** activates only a few per token — so a model can be huge in total knowledge yet cheap per token to run. DeepSeek's V3-lineage models are the canonical illustration: **671B total parameters but only ~37B active per token**.[^moe] GLM-5.2's 744B total run with ~40B active.[^glm] For a founder this is not trivia: **MoE is why a "very large" model can be economically servable.** The total parameter count tells you roughly how much the model *knows*; the active count tells you roughly what it *costs and how fast it runs*. When you read specs, look for both.

### Axis 3: reasoning vs fast

The most important 2026 axis. A **reasoning model** spends extra inference compute — generating hidden or visible **"thinking" tokens** — before its final answer, trading latency and cost for accuracy on hard, multi-step problems. This is **test-time compute**: for genuinely hard tasks, accuracy scales with thinking budget, and a smaller model given room to think can beat a larger one that answers instantly.[^ttc] Every major lab now exposes this as a knob — Claude via a `budget_tokens` parameter, Gemini via a `thinkingBudget` — so reasoning is a dial you set per request, not a separate product.[^ttc] Latency has come down hard: reasoning queries that took 30-120 seconds in early 2025 now resolve in 3-15 seconds for mid-tier models.[^ttc] But the thinking tokens are billed, and **the single biggest cost mistake of 2026 is routing every request through a reasoning model** when a fast model would have nailed it.[^ttc]

<figure class="diagram">
<svg viewBox="0 0 720 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Anatomy of an inference request from tokens in through prefill and decode to tokens out">
  <style>.dg text{font-family:var(--sans);fill:var(--ink);font-size:13px} .dg .box{fill:var(--paper-2);stroke:var(--rule-2)} .dg .accent{fill:var(--accent-bg);stroke:var(--accent)} .dg .rec{fill:var(--sage-bg);stroke:var(--sage)} .dg .lbl{fill:var(--muted);font-size:11px;font-weight:600} .dg .flow{stroke:var(--rule-2);stroke-width:1.6;fill:none}</style>
  <defs><marker id="arw2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--rule-2)"/></marker></defs>
  <g class="dg">
    <rect class="box" x="10" y="90" width="120" height="56" rx="9"/>
    <text x="70" y="114" text-anchor="middle">Tokens in</text>
    <text x="70" y="132" text-anchor="middle" class="lbl">prompt + context</text>
    <rect class="accent" x="190" y="90" width="150" height="56" rx="9"/>
    <text x="265" y="114" text-anchor="middle">Prefill</text>
    <text x="265" y="132" text-anchor="middle" class="lbl">parallel, 1 pass</text>
    <rect class="rec" x="400" y="90" width="150" height="56" rx="9"/>
    <text x="475" y="114" text-anchor="middle">Decode</text>
    <text x="475" y="132" text-anchor="middle" class="lbl">serial, N passes</text>
    <rect class="box" x="610" y="90" width="100" height="56" rx="9"/>
    <text x="660" y="114" text-anchor="middle">Tokens</text>
    <text x="660" y="132" text-anchor="middle">out</text>
    <path class="flow" d="M130 118 L188 118" marker-end="url(#arw2)"/>
    <path class="flow" d="M340 118 L398 118" marker-end="url(#arw2)"/>
    <path class="flow" d="M550 118 L608 118" marker-end="url(#arw2)"/>
    <text x="265" y="60" text-anchor="middle" class="lbl">drives TTFT · scales with input length</text>
    <path class="flow" d="M265 68 L265 88" marker-end="url(#arw2)"/>
    <text x="475" y="60" text-anchor="middle" class="lbl">drives total latency + cost · scales with output</text>
    <path class="flow" d="M475 68 L475 88" marker-end="url(#arw2)"/>
    <text x="475" y="200" text-anchor="middle" class="lbl">reasoning "thinking" tokens live here — billed, invisible</text>
    <path class="flow" d="M475 172 L475 190" marker-end="url(#arw2)"/>
    <rect class="box" x="400" y="158" width="150" height="14" rx="7" opacity="0.5"/>
  </g>
</svg>
<figcaption><strong>Figure 2.1</strong> - Anatomy of an inference request: input tokens are processed in one parallel prefill pass, then output is generated one token at a time in decode, where reasoning tokens and most of the cost live.</figcaption>
</figure>

Here is where Cortex's team makes its central technical bet. They **segment tickets by difficulty and route accordingly.**

| Ticket class | Share | Model class | Why | Illustrative unit cost |
|---|---|---|---|---|
| FAQ / password / billing lookup | ~55% | Fast, small (e.g. Haiku-tier, ~$1/$5 per M) | Answer is in the KB; no multi-step reasoning | Fractions of a cent |
| Standard troubleshooting | ~30% | Fast, mid (e.g. Sonnet-tier, ~$3/$15 per M) | Needs account context + a couple of steps | ~1-3 cents |
| Gnarly multi-system / edge case | ~12% | Reasoning model, budget on | Genuinely hard; wrong answer is costly | ~10-25 cents |
| Ambiguous / risky → human | ~3% | Escalate, no model spend | Not worth the risk | Human cost |

{sn: The router that decides *which* class a ticket belongs to is itself a cheap fast-model call — a few hundred tokens to classify before committing to an expensive path. Classifier-first routing is one of the highest-ROI patterns in applied AI, and it is Cortex's margin.}

The lesson generalizes: **do not pick "a model" for your product; build a routing layer and pick a model per request class.** Reasoning is a scalpel, not a default. Running all of Cortex's tickets through a reasoning model would roughly 5-10x the blended cost for a single-digit accuracy gain on the easy 85% — the definition of burning money and latency.[^ttc]

## Context windows, tokens and the economics of inference

The **context window** is the maximum number of tokens — input plus output — the model can attend to at once. Frontier and leading open models now reach **1M tokens**.[^glm] A million-token window sounds like an invitation to stop thinking about what you include. It is a trap.

Three costs scale with how much context you actually use. **Money**, because you pay per input token every call. **Latency**, because prefill time grows with input length. And **quality**, because models exhibit degraded recall in the middle of very long contexts — the "lost in the middle" effect — so more context can mean *worse* answers, not better. A 1M-token window is a capability ceiling, not an operating point.

The economics of a single request decompose cleanly, and this is the mental model to carry:

```
request cost ≈ (input_tokens  × input_price)
             + (output_tokens × output_price)   # incl. reasoning tokens
             + (cached_tokens × cache_read_price)  # if caching
```

Two levers dominate real bills. **Prompt caching**: providers let you cache a stable prefix — a long system prompt, a fixed knowledge base — and pay a deep discount, typically ~90% off, on subsequent reads of those tokens. Anthropic charges roughly 1.25x the base rate to *write* a 5-minute cache and **0.10x to read** it thereafter.[^cache] **Batch APIs**: non-realtime work run through a batch endpoint runs **~50% off** input and output at both major closed providers, and critically **the discounts stack** — Sonnet-tier batch-plus-cache-read has been quoted around **$0.15 per million input tokens, ~95% off list.**[^cache]

{case: **Stacking discounts, 2026** - Providers now let caching and batch discounts *combine*. Anthropic documents that a [Sonnet-tier batch + cache-read](https://usagebox.com/articles/prompt-caching-cost-optimization-claude-gpt-gemini-2026) request lands near $0.15 per million input tokens — roughly 95% below list — turning "process our whole knowledge base nightly" from a budget line into a rounding error.}

For Cortex this is decisive. Every ticket call includes a large, near-identical preamble: policies, tone guidance, tool schemas, and top knowledge-base articles — easily 8,000-15,000 stable tokens. Caching that prefix turns it from a full-price cost on every one of tens of thousands of daily tickets into a ~90%-discounted read. And the nightly job that re-embeds the knowledge base and back-tests Cortex against yesterday's resolved tickets is pure batch work — no user is waiting — so it runs at half price. The team's rule: **realtime, uncacheable tokens are the only truly expensive tokens; engineer everything else toward cache reads and batch windows.** (The full unit-economics build-out — blended cost per resolved ticket, gross margin, the effect of a bad-answer escalation — is Chapter 13.)

:::rule
**Founder's Rule 2.2** - The context window is a budget, not a target. Cheap tokens are cached tokens and batched tokens; expensive tokens are realtime, uncached output tokens. Architect to convert the second kind into the first.
:::

## Latency, throughput and where the compute goes

Users feel latency; your CFO feels throughput. Both are governed by the two-phase structure of inference, and this is the section most founders skip and later regret.

An inference request runs in two phases with completely different physics (Figure 2.1). **Prefill** processes the entire input prompt in a single parallel pass to build the model's internal state; it is **compute-bound** and its duration sets your **time to first token (TTFT)** — the "is it alive?" delay before anything appears.[^prefill] **Decode** then generates output tokens one at a time; each step is **memory-bandwidth-bound** (the whole model must be read from GPU memory per token) and its speed is measured as **time per output token (TPOT)** or its inverse, **tokens per second**.[^prefill]

:::definition
**TTFT vs TPOT** - **TTFT** (time to first token) is set by prefill and scales with *input* length: long context = slow start. **TPOT** (time per output token) is set by decode and is roughly constant per token: long answers = long total wait. Total latency ≈ TTFT + (output_tokens × TPOT). Optimize the wrong one and you fix the wrong problem.
:::

The founder consequences are direct. **Long inputs hurt TTFT** — Cortex stuffing a giant knowledge base into every prompt makes the agent feel sluggish before it says a word, which is exactly what caching (which lets prefill reuse cached state) and retrieval (fetch only relevant chunks — see Chapter 3) exist to fix. **Long outputs hurt total latency and cost linearly**, so a terse, well-instructed Cortex is both faster and cheaper than a chatty one — a rare case where the better UX is also the better margin. And **reasoning models pay their tax in the decode phase**: those thinking tokens are decode-phase output, which is why reasoning simultaneously raises latency and cost (Figure 2.1).

Throughput is the other side of the same coin. Providers serve many requests at once by **batching** them through the GPU, which is why your per-token price can be low despite frontier hardware — the vendor amortizes each GPU across many concurrent users. The 2026 landscape has specialized silicon competing hard on these numbers: **Groq's LPUs** lead on consistent low-latency decode for open models, **Cerebras** leads raw tokens-per-second on small-to-mid models, and GPUs dominate compute-heavy prefill and high-batch decode.[^inference] You will rarely touch this on a closed API — but the moment Cortex considers self-hosting an open-weights model (Chapter 7), TTFT, TPOT, and achievable batch size *are* the build, and the choice of accelerator is a first-order cost decision.

The synthesis for a founder: **your latency and your cost are the same physics viewed from two ends.** Input length drives prefill, TTFT, and input cost. Output length drives decode, total latency, and output cost. Caching attacks prefill; brevity and routing attack decode; batching attacks throughput. Cortex's entire performance-and-margin strategy is those four moves applied to those two phases — nothing more exotic. Master this loop and you can reason about any model, any provider, and any bill you will ever see.

:::takeaways
**Key takeaways**
- Models predict one token at a time; **you are billed per token, and output tokens cost 4-5x input tokens** because decode is serial while prefill is parallel.
- **Modality is a pricing decision**: audio runs ~10-30x text per token and images cost hundreds-to-thousands of tokens — invoke expensive modalities conditionally, never by default.
- Choose along three axes — **open vs closed, dense vs MoE, reasoning vs fast** — and read *both* total and active parameters; MoE is why huge models can be cheap to serve.
- **Don't pick a model; build a router.** Segment requests by difficulty and reserve reasoning models for the genuinely hard minority — routing every request through reasoning is the top 2026 cost mistake.
- The context window is a **budget, not a target**; caching (~90% off reads) and batch APIs (~50% off, stackable) turn expensive realtime tokens into cheap ones.
- **Latency and cost are one physics:** input length → prefill → TTFT + input cost; output length → decode → total latency + output cost. Cache, shorten, route, batch.
:::

:::exercise
**Hands-on: Model your core action's inference economics**
1. Write down your product's single most important AI action (for Cortex: "resolve one support ticket"). State it as one sentence.
2. Estimate its tokens: input (prompt + context + retrieved data) and output (the answer, plus a reasoning budget if you'd use a reasoning model). Use ~4 characters per token; count your JSON and non-English cases separately.
3. Segment the action into 3-4 difficulty classes and assign a model tier to each (fast-small, fast-mid, reasoning, human-escalate). Estimate the percentage share of each class from real or expected traffic.
4. Compute a **blended per-action cost**: for each class, `(input×input_price)+(output×output_price)`, then weight by share. Use current published 2026 prices for two candidate providers.
5. Now apply the levers: mark which input tokens are a stable, cacheable prefix (apply ~90% off) and which work could run in a batch window (apply ~50% off). Recompute the blended cost.
6. Compare the naive "everything through one frontier reasoning model" cost to your routed-plus-cached cost. The ratio is your architecture's margin — and your Chapter 13 starting point.
:::

[^realtime]: Model Drop: GPT-Realtime-2. <https://handyai.substack.com/p/model-drop-gpt-realtime-2>
[^gemini-live]: Best Realtime AI API for Developers (2026). <https://inworld.ai/resources/best-realtime-ai-api>
[^glm]: Open-Weight LLM Showdown 2026: DeepSeek vs Qwen vs Kimi vs GLM vs Llama. <https://wavect.io/blog/open-weight-llm-comparison-2026/>
[^moe]: 7 Top Mixture of Experts AI Models for Developers in 2026. <https://www.labellerr.com/blog/top-open-source-moe-llms/>
[^ttc]: Test-Time Compute Explained: Why the Best AI Models Now "Think" Before Answering. <https://www.aimagicx.com/blog/test-time-compute-explained-ai-thinking-models-2026>
[^cache]: Cut Your AI API Bill 70-90% with Prompt Caching: The 2026 Cost Math. <https://usagebox.com/articles/prompt-caching-cost-optimization-claude-gpt-gemini-2026>
[^prefill]: Prefill, Decode, and TTFT: The Three Numbers That Should Drive Your Inference Engine Choice. <https://automatosx.medium.com/prefill-decode-and-ttft-the-three-numbers-that-should-drive-your-inference-engine-choice-b9acdf7cd81a>
[^inference]: Fastest LLM Inference APIs in 2026: TTFT and Throughput Guide. <https://inworld.ai/resources/fastest-llm-inference-api>
