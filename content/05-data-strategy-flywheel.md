---
part: Part II - Market and Validation
part_num: II
chapter_num: 5
title: Data Strategy & the Data Flywheel
dek: Your compounding advantage is not the model - it is the data loop only your product can spin.
slug: 05-data-strategy-flywheel
reading_time: 18 min read
---

Every founder in 2026 rents the same frontier models from the same three or four labs. The weights are a commodity you cannot own and cannot hide. What you *can* own is the proprietary data exhaust your product generates while doing real work for real customers - and the machinery that turns that exhaust back into a better product. This chapter is about building that machinery deliberately, from day one, because a data flywheel that starts spinning in month three is worth more than a model architecture nobody can replicate but everybody can rent.

## Data as the AI moat

Model quality is converging and renting it is trivial. When your competitor can call the same Claude, Gemini, or GPT endpoint you can, the base intelligence is table stakes. The durable asset is **proprietary feedback data from real users doing real tasks** - data that is expensive to collect, slow to accumulate, and structurally impossible for an outsider to buy or scrape.[^flywheel] We treat moat *strategy* as Chapter 12's domain; here we care about the one moat made of data, and how you manufacture it.

Not all data is a moat. Draw a hard line between three tiers. **Commodity data** - public web text, generic images, anything scrapable - confers no advantage, because everyone has it and it is exactly what the labs already trained on. **Purchased data** - a Surge AI or Scale AI annotation contract - narrows the gap but is available to anyone with a budget, so it buys parity, not defensibility.[^scale] Only **process-generated data** - the signal that exists solely because your specific product mediated a specific real interaction - compounds into a moat. {sn: A useful test: if a well-funded competitor could recreate your dataset in ninety days with a checkbook, it is not a moat. It is an expense.}

The compounding is the whole point. Each turn of the loop makes the product incrementally better, which draws more usage, which yields more proprietary data, which sharpens the next turn. Practitioners peg the time to a *defensible* flywheel at 18 to 36 months - long enough that late starters cannot out-spend their way in, because they cannot buy back the calendar.[^flywheel]

::: rule
The model is rented. The data loop is owned. Optimize relentlessly for the thing you own.
:::

Consider **Cortex**, our running example: an autonomous AI customer-support agent for mid-market SaaS companies. Cortex's base reasoning comes from a frontier model any competitor can license. Its edge is that every ticket it has ever resolved or escalated - across hundreds of B2B SaaS deployments - carries a label for what a *correct* resolution looked like in that exact product's context. No competitor starting today can conjure that corpus, because it exists only as a byproduct of Cortex having done the work.

## Acquiring and labeling data, including synthetic

Before the flywheel spins on its own, you have a cold-start problem: you need enough data to make the product good enough that people will use it and generate more. There are four levers, and mature teams pull all four in sequence.

**Bootstrap from the founding team.** The first few hundred labeled examples should come from you and your domain experts, by hand. This is not beneath you; it is the highest-leverage labeling you will ever do, because you are simultaneously defining the label schema and discovering what "good" even means. For Cortex, that meant the founders sitting with three design-partner support teams and hand-resolving a few hundred tickets while writing down the decision rules.

**Buy expert labels for what you cannot self-generate.** The labeling market has bifurcated sharply. Commodity annotation - bounding boxes, basic classification - is being eaten alive by AI-assisted pre-labeling and synthetic generation, and prices are collapsing. The durable, expensive work is **expert human data**: domain specialists producing the nuanced judgments a model cannot yet make.[^scale] The vendor landscape reshuffled violently in 2025: after Meta took a 49% stake in Scale AI for $14.3 billion, rival labs including Google, OpenAI, and xAI pulled contracts within days over conflict-of-interest concerns, and independents captured the flight - Surge AI (bootstrapped, $1.2B 2024 revenue), Mercor, and Turing became the fastest-growing alternatives.[^scale] {sn: The lesson for founders is second-order: your labeling vendor can become your competitor's parent overnight. Never let a single annotation supplier see your full label schema *and* your task distribution.}

{case: **The Scale-Meta fracture (June-July 2025)** - Meta's $14.3B for 49% of Scale AI triggered an exodus: rival labs cut ties within days, and Scale laid off roughly 14% of staff in July 2025. Surge AI, Mercor, and Turing absorbed the displaced demand. It is a live case study in supplier-concentration risk for any AI startup dependent on outsourced labels.}

**Generate synthetic data - carefully.** By 2026 synthetic data is mainstream: Gartner's much-cited projection - 75% of businesses using generative AI to create synthetic data by end of 2026, up from under 5% in 2023 - now looks conservative.[^synth] Tooling matured accordingly - NVIDIA acquired Gretel in a reported nine-figure deal, and Gretel Navigator's "Text to Dataset" lets you type *"generate 5,000 flood-damage insurance claims in Florida"* and get a populated schema back.[^synth] Synthetic data is superb for rare edge cases, adversarial examples, privacy-safe pipelines, and bootstrapping eval suites (evals are Chapter 6's turf). But there is a hard failure mode: **model collapse**, the degenerative drift that occurs when models train on their own outputs across generations. The mitigations are empirical - retain real anchors; even a modest real-data floor, on the order of 10%, sharply reduces perplexity drift.[^synth] For Cortex, synthetic tickets fill the long tail (the once-a-quarter refund-dispute-during-an-outage scenario) but never replace the real, human-verified resolutions that anchor the model.

**Use programmatic and weak supervision** (Snorkel-style labeling functions) to turn expert heuristics into labels at scale, then have humans review only the low-confidence and disagreement cases. This is the highest-ROI middle path once you have enough hand labels to write good rules.

| Source | Cost | Defensibility | Best for | Key risk |
|---|---|---|---|---|
| Founder hand-labeling | Very high per unit | High (defines schema) | Cold start, schema design | Doesn't scale |
| Expert vendor labels | High | Low-medium (buyable) | Domain nuance you lack | Supplier = future rival |
| Commodity vendor labels | Low & falling | None | Bulk classification | Being eaten by synthetic |
| Synthetic generation | Very low | Low alone | Edge cases, privacy, evals | Model collapse |
| Programmatic / weak supervision | Low | Medium | Scaling expert heuristics | Systematic label bias |
| **Process-generated (flywheel)** | Marginal (free byproduct) | **Very high** | The moat | Requires product usage first |

::: warning
Pure synthetic training without real anchors collapses. Treat synthetic data as a supplement that fills gaps in a real-data backbone, never as a substitute for it. Budget for a permanent floor of human-verified real examples.
:::

## Designing the data flywheel

The flywheel is not a metaphor you hope emerges; it is an engineering system you design. The canonical loop has four stages, each of which you must instrument deliberately.

<figure class="diagram">
<svg viewBox="0 0 720 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The data flywheel: more usage produces more proprietary data, which trains a better model, which yields a better product, which drives more usage.">
  <style>.dg text{font-family:var(--sans);fill:var(--ink);font-size:13px} .dg .box{fill:var(--paper-2);stroke:var(--rule-2)} .dg .accent{fill:var(--accent-bg);stroke:var(--accent)} .dg .rec{fill:var(--sage-bg);stroke:var(--sage)} .dg .lbl{fill:var(--muted);font-size:11px;font-weight:600} .dg .flow{stroke:var(--rule-2);stroke-width:1.6;fill:none}</style>
  <defs><marker id="fwArrow05" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--rule-2)"/></marker></defs>
  <g class="dg">
    <rect class="accent" x="285" y="18" width="150" height="46" rx="9"/>
    <text x="360" y="46" text-anchor="middle">More usage</text>
    <rect class="box" x="540" y="120" width="160" height="46" rx="9"/>
    <text x="620" y="148" text-anchor="middle">More proprietary data</text>
    <rect class="rec" x="285" y="230" width="150" height="46" rx="9"/>
    <text x="360" y="258" text-anchor="middle">Better product</text>
    <rect class="box" x="20" y="120" width="160" height="46" rx="9"/>
    <text x="100" y="148" text-anchor="middle">Better model</text>
    <path class="flow" d="M435 48 Q560 70 610 118" marker-end="url(#fwArrow05)"/>
    <path class="flow" d="M600 166 Q470 220 435 240" marker-end="url(#fwArrow05)"/>
    <path class="flow" d="M285 253 Q160 220 108 168" marker-end="url(#fwArrow05)"/>
    <path class="flow" d="M115 118 Q240 70 285 50" marker-end="url(#fwArrow05)"/>
    <text class="lbl" x="565" y="90" text-anchor="middle">capture</text>
    <text class="lbl" x="505" y="215" text-anchor="middle">deploy</text>
    <text class="lbl" x="150" y="215" text-anchor="middle">train / tune</text>
    <text class="lbl" x="205" y="90" text-anchor="middle">ship</text>
  </g>
</svg>
<figcaption><strong>Figure 5.1</strong> - The data flywheel: usage generates proprietary data, which trains a better model, which ships a better product, which drives more usage.</figcaption>
</figure>

The stages are **capture** (log production traffic, decisions, and outcomes), **curate** (filter, label, and select what is worth training on), **train** (fine-tune, distill, or update routing/retrieval on the curated set), and **deploy** (ship the improvement and measure the lift). NVIDIA's open-source Data Flywheel blueprint formalizes exactly this loop - collect production logs, evaluate with an LLM judge, fine-tune, and redeploy - and in NVIDIA's own internal tests it cut inference costs by up to 98.6% while holding accuracy, largely by distilling a big model's behavior into a small fine-tuned one once enough production data existed.[^nvidia] That cost collapse is the underrated payoff: a working flywheel doesn't just improve quality, it lets you replace an expensive frontier call with a cheap specialized model on the tasks you now have data for.

::: definition
**Data flywheel** - a self-reinforcing system in which product usage generates proprietary data, that data measurably improves the product, and the improved product drives more usage. The loop is "closed" only when a real production signal flows all the way back into a shipped model or system change.
:::

**Cortex's flywheel in motion.** Every ticket Cortex touches ends in one of two labeled states: *resolved* (the customer confirmed the fix, or never reopened it within the SLA window) or *escalated* (a human agent took over). Each terminal state is a free, high-quality label for what "good" looked like on that ticket. Resolved tickets teach the routing model which retrieval passages and action sequence produced a fix; escalated tickets flag exactly where the agent's confidence should have been lower - training signal for *when to hand off*. The retrieval layer (Chapter 8) is re-ranked on which documents actually appeared in successful resolutions. No synthetic corpus and no purchased dataset can produce this, because the label is defined by the outcome of Cortex's own action inside a specific customer's live product.

The trap founders fall into is building a flywheel that is technically closed but too slow to matter. If it takes six weeks to get a production signal back into the model, you get roughly eight turns a year. If it takes two days, you get a hundred. **Loop latency is a first-class metric** - instrument it and drive it down like you would p95 response time.

::: rule
Measure the time from a production signal to a shipped improvement. That loop latency, not model size, sets how fast your moat compounds.
:::

## Capturing feedback and implicit signals

Training data quality lives or dies at the capture layer, and most teams under-invest here catastrophically. There are two families of signal, and you need both.

**Explicit feedback** is what the user deliberately tells you: thumbs up/down, a corrected answer, an accepted or rejected suggestion, a star rating. It is high-signal but scarce - people rarely bother. The single highest-leverage UX decision is friction: an *inline* thumbs up/down, designed into the primary interaction surface rather than hidden behind a click, lifts submission volume by an order of magnitude over a separate modal form. Better still, capture **user edits** - when a user takes your model's draft and changes three words before sending, those edits are a gift-wrapped preference pair.

**Implicit feedback** is the behavioral exhaust: regeneration requests, session abandonment, dwell time, copy events, whether the user re-asked the same question, whether they escalated to a human.[^nvidia] Implicit signals are noisier per event but arrive in enormous volume and cannot be gamed by survey fatigue. A regeneration is a soft thumbs-down; an abandoned session after an answer is a strong negative; a copied code block is a strong positive. The art is mapping each behavior to a confidence-weighted label.

These labels feed preference-tuning pipelines directly. Explicit up/down and implicit positive/negative can be filtered into DPO or KTO training sets, or used to gate which examples enter supervised fine-tuning - a full RLHF pipeline is often overkill for an application startup, and gives only a minor, non-durable edge *unless* you already have a large engaged base generating the preferences.[^flywheel] Your advantage is not the RL algorithm - those are public - it is the proprietary preference data flowing in.

| Signal | Type | Volume | Noise | Maps to |
|---|---|---|---|---|
| Thumbs up/down (inline) | Explicit | Medium | Low | Direct preference label |
| User edit of output | Explicit | Medium | Very low | Preference pair (before/after) |
| Accept / reject suggestion | Explicit | High | Low | Binary label |
| Regeneration request | Implicit | High | Medium | Soft negative |
| Session abandonment | Implicit | Very high | High | Weak negative |
| Copy / export output | Implicit | High | Low | Strong positive |
| Escalation to human | Implicit | Medium | Very low | Hard negative + handoff signal |
| Task completion / non-reopen | Implicit | High | Low | Strong positive (outcome) |

For Cortex, the richest implicit signal is the **outcome itself**: did the ticket stay closed? A ticket the customer reopens within 48 hours is a delayed, unambiguous negative that no thumbs-down button would have captured, because the user felt satisfied in the moment and only discovered the failure later. Outcome-based labels - tied to what actually happened downstream - are the crown jewels of any flywheel, and they are available only to the company that owns the end-to-end workflow.

{case: **NVIDIA Data Flywheel Blueprint (2025-26)** - NVIDIA open-sourced a reference blueprint (with a Weights & Biases observability layer) that operationalizes the full loop: capture production logs and thumbs/edit/regeneration signals, evaluate candidate models with an LLM judge, run DPO/KTO or filtered fine-tuning, and redeploy. In one internal run it distilled a 70b production model into a fine-tuned 1b for a tool-calling task at comparable accuracy. A concrete template founders can study rather than reinvent.}

## Privacy, governance and data rights

Here is where founders quietly sabotage their own flywheel: they build the loop and only later discover they never had the *right* to train on the data flowing through it. Data you cannot legally use for training is not fuel - it is liability. Governance is a precondition for the flywheel to spin at all, not a compliance afterthought. (The regulatory deep-dive - EU AI Act, GDPR, sector rules - is Chapter 17; here we cover the data-rights mechanics specific to training.)

**Your training rights live in the contract, not the homepage.** Two controls are routinely conflated and are legally distinct: **zero data retention (ZDR)**, meaning the processor does not store your inputs/outputs beyond the immediate request, and **training opt-out**, meaning your data is not used to improve someone's model. A vendor can honor one and violate the other.[^zdr] You must resolve *both* directions:

- **As a consumer of model APIs:** confirm in the DPA/MSA (not the marketing page) that your customers' data is not used to train the *provider's* models, with explicit scope, covered endpoints, and exclusions. Enterprise tiers of the major providers contractually prohibit training on API data - but consumer and free tiers increasingly opt you *in* by default. GitHub Copilot, for instance, begins using Free/Pro/Pro+ interaction data for training by default on April 24, 2026 unless users opt out, while Business and Enterprise seats are exempt.[^copilot] {sn: Read the version-and-tier fine print. "We don't train on your data" is almost always true only of the enterprise SKU, and submitting thumbs-up feedback can explicitly opt *that specific conversation* back into training even on protected tiers.}
- **As a producer building on customer data:** your own customer contracts must *grant you the right* to use their data - ideally de-identified and aggregated - to improve your product. If your MSA is silent, assume you cannot, and you will discover this during a security review that stalls a six-figure deal.

::: warning
The most expensive data-governance failure is retroactive: shipping a flywheel for a year, then learning your contracts never permitted training on that data. Every example you trained on is now tainted, and unwinding it can mean re-training from a clean cut. Get the training-rights clause into your customer MSA *before* the flywheel starts, not after.
:::

For a B2B product like Cortex, the governance design is load-bearing to the sales motion. Cortex's contracts specify that resolved-ticket data may be used to improve the service in **de-identified, aggregated** form - customer names, account IDs, and PII stripped at the capture boundary, never at training time. Cross-tenant learning (patterns from Customer A improving Customer B's routing) is permitted only on abstracted signals - which retrieval strategy worked, not the content - so no customer's proprietary data leaks into another's model. Documented, de-identified provenance of this kind also eases the data-governance expectations regulators now attach to higher-risk systems, whose enforcement regime is Chapter 17's subject.[^aiact] The startups that treat governance as an enabling design constraint sell into regulated enterprises; the ones that treat it as paperwork get stuck in procurement forever.

::: takeaways
**Key takeaways**
- Model weights are rented and converging; your only durable, compounding asset is proprietary process-generated data and the loop that recycles it.
- Distinguish commodity, purchased, and process-generated data - only the third is a moat, because a competitor cannot buy back the calendar it took to accumulate.
- Bootstrap with founder hand-labels and expert vendors, scale with programmatic supervision, and use synthetic data for edge cases and privacy - but keep a real-data floor to avoid model collapse.
- Design the flywheel as an explicit capture -> curate -> train -> deploy loop, and treat *loop latency* as a first-class metric: more turns per year beats a bigger model.
- Capture both explicit (thumbs, edits) and implicit (regeneration, abandonment, outcomes) signals; inline feedback controls raise volume by an order of magnitude, and outcome-based labels are the crown jewels.
- Secure training rights contractually in both directions before the loop spins - ZDR and training opt-out are distinct, and retroactive governance failures can taint everything you trained on.
:::

::: exercise
**Hands-on: Map your flywheel**
1. Write down the single proprietary signal your product generates that no competitor could buy or scrape. If you cannot name one, your first job is to design the product so it produces one.
2. For that signal, specify the four loop stages concretely: how you capture it, how you curate/label it, what you train or tune on it, and how you deploy and measure the lift.
3. Estimate your current loop latency (production signal -> shipped improvement) in days, and set a target that at least doubles your turns per year.
4. Inventory your feedback surfaces: list every explicit and implicit signal you capture today and one high-value signal you are currently throwing away. Design the UX to capture it inline.
5. Pull your customer MSA and your model-provider DPA. Confirm, in writing, (a) that you have the right to train on customer data in de-identified form and (b) that your provider does not train on your inputs. Flag any gap as a blocker before you scale the loop.
:::

[^flywheel]: Data Flywheel: The Only AI Moat That Compounds. <https://www.rohitprabhakar.com/blog/market-of-one-data-flywheel-competitive-moat/>
[^scale]: Scale AI Competitors (2026): Who Won the Data Market After the Meta Deal. <https://www.teahose.com/guides/scale-ai-competitors>
[^synth]: Synthetic Data for AI in 2026: Guide + Best Tools. <https://futureagi.com/blog/synthetic-data-guide/>
[^nvidia]: NVIDIA Data Flywheel Blueprint. <https://github.com/NVIDIA-AI-Blueprints/data-flywheel>
[^zdr]: Zero Data Retention for AI APIs: What It Actually Means in 2026. <https://meridianblue.ai/blog/zero-data-retention/>
[^copilot]: GitHub Copilot's new policy for AI training: a governance wake-up call. <https://about.gitlab.com/blog/github-copilots-new-policy-for-ai-training-is-a-governance-wake-up-call/>
[^aiact]: Enforcement of Chapter V (GPAI obligations) under the EU AI Act. <https://artificialintelligenceact.eu/enforcement-of-chapter-v-under-the-eu-ai-act/></parameter>
<parameter name="changelog">Fact-checked all 2026 claims via web search; all major ones verified (Meta $14.3B/49% Scale stake, Scale ~14% July 2025 layoffs, Gartner 75%, NVIDIA 98.6%, Copilot Apr 24 2026 opt-out, GPAI enforcement Aug 2026). Corrections: Surge AI revenue set to $1.2B 2024 (verified); Gretel softened to "reported nine-figure deal" (price never disclosed, above ~$320M valuation); dropped unverified "Microsoft" from contract-pullers (kept Google/OpenAI/xAI). Removed the unsupportable "40x" inline-feedback figure plus its incorrect [^nvidia] citation and softened to an order-of-magnitude claim; fixed matching takeaway. Compressed the EU AI Act passage to a Ch17 cross-reference instead of explaining Article 10, and re-cited it to a proper EU AI Act source [^aiact] rather than the mismatched [^zdr]. Trimmed NVIDIA 98.6% duplication between body and case box. Cut restated filler in the moat section opener. Verified format: frontmatter keys present, unnumbered ## headings, valid callout types, single diagram figure with unique marker id, all [^id] footnotes defined, no footnotes inside sn/case blocks, Cortex present. reading_time set to 18 min. Stripped the stray non-chapter trailing markup that had leaked into the draft.