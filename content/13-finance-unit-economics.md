---
part: Part V - Company Building
part_num: V
chapter_num: 13
title: Finance & Unit Economics for AI
dek: The number that decides your fate is gross margin, and your cost of goods is tokens and GPUs.
slug: 13-finance-unit-economics
reading_time: 20 min read
---

Software companies got fat on 80% gross margins because the marginal cost of the next customer was a rounding error. AI companies do not get that gift. Every request your product serves burns real compute, and that compute lands in cost of goods sold, not in the R&D line where investors forgive it. This chapter is about the one number that quietly decides whether your beautiful AI product is a business or a science project: the margin left after you pay for the tokens.

## AI COGS: inference, not just servers

In a classic SaaS profit-and-loss statement, **cost of goods sold (COGS)** is hosting, a support team, and some third-party tooling — a thin, mostly fixed layer under a torrent of near-free revenue. In an AI company, COGS grows almost linearly with usage, because the dominant term is **inference**: the compute you spend generating each response. The industry has re-learned this the hard way. The average AI product shipped a **52% gross margin** in 2026 versus the ~80% that defined mature SaaS, and inference alone consumes roughly **23% of revenue** at scaling-stage AI B2B companies.[^avante] Traditional SaaS runs total COGS of 10–25% of revenue; AI puts a single line item at the top of that range before you have paid for anything else.[^valueadd]

Your AI COGS has five buckets, and founders who only budget the first one get blindsided by the other four:

| COGS bucket | What it is | Typical share of AI COGS | Scales with |
| --- | --- | --- | --- |
| **Inference** | Token generation (API or self-hosted GPU) | 50–70% | Requests × tokens/request |
| **Retrieval & data** | Vector DB, embeddings, re-ranking, search calls | 8–15% | Corpus size × query volume |
| **Orchestration & tooling** | Agent framework hosting, tool/API calls, function runners | 5–12% | Steps per task |
| **Observability & evals** | Tracing, logging, LLM-as-judge scoring in prod | 3–8% | Request volume |
| **Human-in-the-loop** | Escalation agents, labeling, review of low-confidence output | 5–20% | 1 − automation rate |

{sn: The nastiest hidden cost is **evals in production** (see Chapter 10). If you run an LLM-as-judge on every response to catch regressions, you have just added a second inference call to every request — double your token bill unless you sample.}

The mental shift is this: **inference is a variable input cost, like flour for a bakery, not a fixed asset like the oven.** You cannot amortize it away with scale. If anything, it grows with success. Two structural choices determine its size, and both live in other chapters: which provider and model you buy (see Chapter 7) and how you architect routing, caching, and context (see Chapter 9). Here we only turn those choices into numbers.

:::definition
**AI COGS** — the sum of all usage-variable costs incurred to serve one unit of product value: inference tokens, retrieval, tool calls, in-production evaluation, and any human review. If a cost rises when a customer uses you more, it belongs in COGS, not R&D.
:::

## Unit economics: cost and margin per action

Seat-based pricing is a lie for AI products, because a "seat" that fires 5,000 agent runs a month costs you fifty times more to serve than one that fires 100. The only honest unit of analysis is the **action**: one resolved ticket, one generated document, one completed agent task. Compute your fully-loaded cost per action, compare it to the price you charge for that action, and you have your true unit economics.

Cortex, our autonomous support agent for mid-market SaaS companies, sells on exactly this unit: **price per resolved ticket**. This is the emerging standard. Intercom's Fin charges **$0.99 per resolved conversation**;[^intercom] Zendesk launched outcome pricing at **$1.50 per automated resolution** on committed volume ($2.00 pay-as-you-go); Sierra charges roughly **$1.50 per resolved interaction** and rode that model from $100M to $200M ARR and a $15.8B valuation; Decagon pairs a ~$50K platform fee with a custom per-resolution rate.[^witn][^sierra] Cortex prices at **$1.20 per resolved ticket** — cheap enough to undercut a human ticket (which costs the customer $15–$35 fully loaded) by an order of magnitude, expensive enough to have a business, *if the cost side cooperates.*

Now the cost side. A single resolved ticket is not one model call — it is a conversation. Cortex's naive v1 architecture, running everything through a frontier model, looked like this:

```text
Cortex cost per resolved ticket — naive (frontier-only)
  intent classification        1 call   ~2K tok   $0.03
  retrieval + rerank           2 calls  ~1K tok   $0.02
  reasoning / tool selection   3 calls  ~18K tok  $0.34
  answer drafting + revision   2 calls  ~9K tok   $0.21
  in-prod eval (judge)         1 call   ~4K tok   $0.08
  ─────────────────────────────────────────────────────
  inference subtotal                              $0.68
  retrieval infra + tool APIs                     $0.09
  observability                                   $0.02
  human escalation (18% of tickets × $0.22 amort) $0.04
  ─────────────────────────────────────────────────────
  fully-loaded COGS per resolved ticket           $0.83
```

At $1.20 price and $0.83 cost, Cortex's contribution margin is **$0.37, or 31%.** That is a company that dies at scale: every dollar of new revenue drags 69 cents of cost, sales and G&A eat the rest, and the burn multiple never converges. The founders' instinct — "we'll fix it with volume" — is exactly wrong, because there is no volume discount on a variable input.

{case: **Intercom Fin's honesty clause** - In 2026 Fin still charges $0.99 only when it fully resolves a conversation; if the AI hands off to a human, the customer pays nothing for that interaction. It is elegant marketing, but it is also a brutal unit-economics constraint: Fin eats the full inference cost of *every attempt*, including the failures it does not bill for. Your cost-per-action denominator is total actions; your revenue numerator is only the *successful* ones. Price the gap in.}

:::rule
Price per outcome, cost per attempt. Your margin lives in the gap between the two — measure it before you sign the contract, not after.
:::

## The gross-margin reality of AI products

Here is the uncomfortable table every AI founder should stare at. Gross margin is not a vanity metric; at exit it is a *valuation multiplier*, because a 70%-margin dollar of revenue is worth far more than a 50%-margin dollar.

| Product archetype | Typical gross margin (2026) | Why |
| --- | --- | --- |
| Thin API wrapper, frontier model, no routing | 25–45% | Every request pays full frontier price; no moat |
| Routed multi-model app + caching | 55–70% | Cheap models absorb easy traffic |
| Fine-tuned / distilled model on owned infra | 65–80% | Lower per-token cost, amortized training |
| Workflow SaaS with light AI feature | 70–82% | AI is a small fraction of total value delivered |
| Traditional SaaS (reference) | 78–85% | Compute is a rounding error |

Investors have caught on. In 2026 they check gross margin "more carefully than before to make sure AI inference costs are not quietly eating your profit margin"; a GPT-wrapper at 50–60% invites questions about defensibility, while proprietary or fine-tuned systems that clear 70%+ get the premium.[^aibiz] For a *SaaS company bolting AI onto an existing product*, the typical hit is **12–17 points of gross margin** — enough to reset a company's valuation category.[^saasmag]

The way out is not to charge more (the market caps your price) but to **engineer your COGS down**. The single highest-leverage move is **model routing**: send the easy majority of requests to a small, cheap model and reserve the frontier model for the hard minority. Route the easy ~60% down and you save roughly **38% of inference spend** with no measurable accuracy penalty; aggressive setups with semantic caching report 50–70%.[^sfai][^mindstudio] (The *how* — cascades, confidence thresholds, routers — is Chapter 9's territory. Here we only bank the savings.)

Cortex did exactly this. It added a router: a fast, cheap model (DeepSeek-V4 class, ~$0.14/$0.28 per 1M tokens[^tldl]) handles intent, retrieval, and the 62% of tickets that are routine password-reset-and-billing questions end to end. Only genuinely ambiguous tickets escalate to a frontier model (Claude Opus 4.8 class, $5/$25 per 1M[^morph]). Semantic caching kills repeat questions outright. The rebuilt cost stack:

```text
Cortex cost per resolved ticket — routed + cached
  cheap-model path (62% of tickets)      blended  $0.11
  frontier path (38% of tickets)         blended  $0.29
  ─────────────────────────────────────────────────────
  blended inference per resolved ticket           $0.18
  retrieval infra + tool APIs                     $0.06   (cache cuts calls)
  observability (sampled 20%, not 100%)           $0.01
  human escalation (11% × $0.22 amort)            $0.02
  ─────────────────────────────────────────────────────
  fully-loaded COGS per resolved ticket           $0.27
```

Same $1.20 price, new $0.27 cost: contribution margin jumps to **$0.93, or 78%.** Cortex went from a doomed 31% product to a fundable 78% product without touching its price or its accuracy target — purely by treating inference as an engineering cost to be optimized, not a bill to be paid. That is the whole game.

<figure class="diagram">
<svg viewBox="0 0 720 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Unit-economics waterfall for one Cortex resolved ticket, from price down to gross margin">
  <style>.dg text{font-family:var(--sans);fill:var(--ink);font-size:13px} .dg .box{fill:var(--paper-2);stroke:var(--rule-2)} .dg .accent{fill:var(--accent-bg);stroke:var(--accent)} .dg .rec{fill:var(--sage-bg);stroke:var(--sage)} .dg .lbl{fill:var(--muted);font-size:11px;font-weight:600} .dg .flow{stroke:var(--rule-2);stroke-width:1.6;fill:none} .dg .amt{font-size:12px;font-weight:700}</style>
  <defs><marker id="ARROWCH13" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--rule-2)"/></marker></defs>
  <g class="dg">
    <text x="12" y="24" class="lbl">ONE RESOLVED TICKET — routed architecture</text>
    <rect x="12" y="40" width="150" height="150" rx="9" class="accent"/>
    <text x="34" y="112" class="lbl">PRICE</text>
    <text x="34" y="132" class="amt">$1.20</text>
    <path d="M162 115 L200 115" class="flow" marker-end="url(#ARROWCH13)"/>
    <rect x="200" y="60" width="150" height="110" rx="9" class="box"/>
    <text x="220" y="105" class="lbl">− INFERENCE</text>
    <text x="220" y="125" class="amt">$0.18</text>
    <path d="M350 115 L388 115" class="flow" marker-end="url(#ARROWCH13)"/>
    <rect x="388" y="60" width="150" height="110" rx="9" class="box"/>
    <text x="408" y="105" class="lbl">− OTHER COGS</text>
    <text x="408" y="125" class="amt">$0.09</text>
    <path d="M538 115 L576 115" class="flow" marker-end="url(#ARROWCH13)"/>
    <rect x="576" y="40" width="132" height="150" rx="9" class="rec"/>
    <text x="596" y="105" class="lbl">GROSS MARGIN</text>
    <text x="596" y="126" class="amt">$0.93 · 78%</text>
    <text x="12" y="232" class="lbl">Naive frontier-only path for comparison:</text>
    <text x="12" y="252" class="amt">$1.20 price − $0.68 inference − $0.15 other = $0.37 · 31%</text>
    <text x="12" y="278" class="lbl">Routing + caching moves the same ticket from 31% to 78% margin at an unchanged price.</text>
  </g>
</svg>
<figcaption><strong>Figure 13.1</strong> - The unit-economics waterfall for one Cortex resolved ticket: price flows down through inference and other COGS to the margin that decides the company's fate.</figcaption>
</figure>

## Burn, runway and compute budgeting

AI startups burn differently from SaaS, and the difference is compute. GPU spend consumes **40–60% of technical budgets** in the first two years, and AI startups burn roughly **2× what SaaS companies spend on infrastructure.**[^valueadd] Your runway math has a term SaaS never had: a compute line that can spike with a viral week or a single runaway agent loop.

Compute budgeting splits into two very different problems. **Inference compute** scales with revenue and should be modeled as a variable COGS (dollars per action × actions). **Training / fine-tuning compute** is lumpy capex-like spend you incur ahead of revenue. If you self-host, an H100 runs a **market-median $2.29–$3.12/hr** in 2026 — as low as $1.38/hr on verified neo-clouds, but $6.88/hr on AWS p5 and ~$12/hr on Azure.[^cloudzero][^thunder] A single H100 running 24/7 is $1,500–$3,000/month; an eight-GPU fine-tuning cluster is $12,000–$24,000/month.[^thunder] Provider choice alone is a CFO decision, not just an infra one (see Chapter 7).

{case: **The neo-cloud arbitrage** - In 2026 the cheapest verified on-demand H100 sat at $1.38/hr while AWS charged over $7.50/hr for the identical chip — roughly a 5× spread. A startup spending $10K/month on H100 compute pays about $4,680/month less on a specialized provider than on a hyperscaler, exceeding $56,000 in preserved runway over a year. For a pre-revenue AI company, that is a month of extra life bought with a config change.}

Three disciplines keep compute from eating your runway:

- **Underwrite COGS at build time.** Before you ship a feature, estimate its cost per action at expected volume. A feature that is margin-negative at scale should be re-architected or repriced *before* launch, not after the invoice arrives.
- **Set token budgets and hard caps per request and per customer.** An agent with no step limit is an unbounded liability; one pathological ticket looping through a frontier model can cost more than a hundred normal ones. Cap steps, cap tokens, alert on anomalies.
- **Exploit credits, but do not build on them.** GPU credit programs and provider startup deals routinely offer $100K–$350K in compute; take them, but model your unit economics at *list price*, because credits expire and your margins must survive the cliff.

{sn: Prepaid API commits and reserved GPU capacity trade flexibility for a 20–40% discount. Only commit once your usage is predictable — an early over-commit is just burn with extra steps.}

:::warning
Compute credits are a runway extender, not a business model. Founders who show 75% gross margins that secretly depend on $250K of expiring cloud credits are not lying to investors — they are lying to themselves. Model everything at list price and treat credits as a bonus.
:::

## Financial modeling and the metrics investors probe

Build your model **bottom-up from the unit**, never top-down from a TAM percentage. Start with cost and price per action, layer in volume growth, model the COGS curve *bending down* as routing and caching mature (a defensible, dated assumption you must justify), then stack fixed costs to get to burn and runway. The single most important output is the trajectory of **gross margin over time** — investors want to see a credible path from today's 50s to the 70s, driven by specific engineering levers, not hope.

The metrics an AI-literate investor will probe in 2026, and where you need to land:

| Metric | 2026 benchmark | What it reveals |
| --- | --- | --- |
| **Gross margin** | 60–80% (AI-native); 50–60% flags wrapper risk | Whether inference is under control[^aibiz] |
| **Burn multiple** (net burn ÷ net new ARR) | Series A median ~1.2×; AI-native 0.8–1.2× | Capital efficiency[^aibiz] |
| **Revenue per employee** | $300K+ premium; $150K min at Series A | AI leverage on headcount[^arr] |
| **Rule of 40** (growth % + margin %) | 40 minimum; best VCs want 50+ | Growth-efficiency balance[^data] |
| **Cost per action & trend** | Falling quarter-over-quarter | Margin durability |
| **Gross-margin-adjusted CAC payback** | < 18 months | Whether thin margins break the CAC math |

Two AI-specific traps hide in these numbers. First, **CAC payback must be computed on gross-margin dollars, not revenue** — at 50% margin, a customer takes twice as long to pay back as the top-line suggests, so thin AI margins quietly wreck otherwise-healthy sales efficiency. Second, watch **NDR versus COGS growth**: usage-based AI revenue expands beautifully, but if a customer's usage doubles and your cost to serve them doubles with it, net-dollar retention flatters a P&L that is not actually getting more profitable. The good news: AI-native companies are already posting burn multiples of **0.8–1.2×**, beating traditional SaaS at nearly every stage, precisely because automation holds headcount down while revenue compounds.[^aibiz]

For Cortex, the model that raises a Series A is legible: **78% and rising gross margin** (with a stated path to low-80s as the router improves), **cost per resolved ticket falling ~15% per quarter**, **revenue per employee north of $400K** because the product *is* the labor, and a **burn multiple under 1.0×**. Every one of those numbers traces back to the same discipline — engineering inference down instead of paying it as a bill. That is what makes it an *AI* company worth funding rather than a SaaS company with a token problem. The fundraising story built on top of these numbers is Chapter 14.

:::rule
Model your unit economics at list price, on gross-margin dollars, with a COGS curve you can defend line by line. Everything an AI investor believes about your company, they infer from that one spreadsheet.
:::

:::takeaways
**Key takeaways**
- In AI companies, inference is a **variable COGS** that scales with usage — it cannot be amortized away, and it is why 52% gross margins, not 80%, are the 2026 norm.
- The honest unit of analysis is the **action** (a resolved ticket, a generated doc), not the seat. Compute fully-loaded cost per action against price per action.
- You price per **outcome** but pay per **attempt** — margin lives in the gap, widened by failed and escalated actions.
- **Model routing plus caching** is the highest-leverage margin lever: it moved Cortex from 31% to 78% margin at an unchanged price, without hurting accuracy.
- **Compute credits are runway, not a business model** — model everything at list price so your margins survive the cliff.
- Investors in 2026 probe gross margin, burn multiple, revenue per employee, and cost-per-action *trend*; compute CAC payback on gross-margin dollars.
:::

:::exercise
**Hands-on: Build your cost-per-action waterfall**
1. Pick your single most important product action (the thing you charge for). Instrument one week of production traffic to capture, per action: number of model calls, tokens in/out per call, and which model served each.
2. Multiply by current provider prices to get **inference cost per action**. Add retrieval, tool-call, observability, and human-escalation costs to reach **fully-loaded COGS per action**.
3. Divide COGS by your price per action → contribution margin. If it is below 60%, you have a routing/architecture problem, not a pricing problem.
4. Classify your traffic: what fraction of actions are "easy" and could be served by a model 10–30× cheaper? Estimate the blended inference cost if you routed that fraction down.
5. Rebuild the waterfall with routing and caching applied. The delta between the two waterfalls is your margin-improvement roadmap — put dates on each lever.
6. Project cost per action forward four quarters assuming falling model prices (~30–50%/yr) and improving routing. Hand that curve to your model as the COGS assumption behind gross margin.
:::

[^avante]: ICONIQ Growth, *2026 State of AI* (bi-annual snapshot), reporting a ~52% average AI gross margin and inference at ~23% of revenue; see also Avante Ventures, "AI Startup Gross Margins Run 50 to 60 Percent, Not the SaaS 80 Percent" (2026). <https://avanteventures.com/en/library/ai-startup-gross-margin-benchmark-2026>
[^valueadd]: The True Cost of Running an AI Product in 2026: GPU, API, and Inference Bills. <https://valueaddvc.com/blog/the-true-cost-of-running-an-ai-product-in-2026-gpu-api-and-inference-bills>
[^saasmag]: The AI COGS Problem: SaaS Gross Margin Compression 2026. <https://www.saasmag.com/ai-cogs-saas-gross-margin-compression/>
[^witn]: AI Agent Pricing in 2026: What Fin, Sierra, Decagon and Agentforce Actually Charge. <https://www.thewitn.com/blog/ai-agent-pricing-in-2026-what-fin-sierra-decagon-and-agentforce-actually-charge>
[^sierra]: How Does Sierra AI Make Money: Outcome-Based Pricing at a $15.8B Valuation. <https://valueaddvc.com/blog/how-does-sierra-ai-make-money-outcome-based-pricing-enterprise-agents-and-the-business-model-breakdown>
[^intercom]: AI Customer Service Agent Pricing Comparison: Fin vs Zendesk vs Agentforce. <https://www.intercom.com/learning-center/ai-customer-service-agent-pricing-comparison>
[^morph]: LLM API Providers (2026): 12 APIs Compared by Price per 1M Tokens. <https://www.morphllm.com/llm-api>
[^tldl]: LLM API Pricing (July 2026): Full Table. <https://www.tldl.io/resources/llm-api-pricing>
[^sfai]: The AI Project Model-Routing Economics: Why a Router Saves 38% of Inference Spend. <https://sfailabs.com/guides/the-ai-project-model-routing-economics-why-a-router-saves-38-of-inference-spend>
[^mindstudio]: How to Use Model Routing to Cut AI Agent Costs by 60%. <https://www.mindstudio.ai/blog/model-routing-cut-ai-agent-costs>
[^cloudzero]: H100 GPU Cost in 2026: Buy, Rent, and Cloud Pricing Compared. <https://www.cloudzero.com/blog/h100-gpu-cost/>
[^thunder]: AI GPU Rental Market Trends (July 2026): Complete Industry Analysis. <https://www.thundercompute.com/blog/ai-gpu-rental-market-trends>
[^aibiz]: 15 AI Startup Metrics Investors Track in 2026 (With Benchmarks). <https://aibusiness.vc/startups/ai-startup-metrics-investors-track>
[^arr]: Startup ARR Per Employee Benchmarks 2026: SaaS Capital Efficiency Data. <https://stealthagents.com/research/startup-arr-per-employee-benchmarks-2026>
[^data]: B2B SaaS Revenue Efficiency Benchmarks 2026: Magic Number, Rule of 40 & NRR by Stage. <https://www.data-mania.com/blog/b2b-saas-revenue-efficiency-benchmarks-2026-magic-number-rule-of-40-nrr-by-stage/>
