---
part: Part II - Market and Validation
part_num: II
chapter_num: 4
title: Markets, Users & AI Product Strategy
dek: Where AI creates durable value instead of a demo - and how to price it.
slug: 04-markets-users-product-strategy
reading_time: 18 min read
---

Every founder in 2026 can build a convincing demo in a weekend. That is precisely the problem. The model does the impressive part for free, so the demo proves nothing about whether you have a business - and the graveyard is full of products that died the week a user asked, "Can't I just do this in ChatGPT?" This chapter is about the judgment that separates a durable AI product from a gimmick: choosing a market that feels real pain, reading the fit signals that actually matter for AI, escaping the thin-wrapper trap, and pricing for the value you deliver rather than the seats you occupy.

## Problem-solution fit for AI: value versus gimmick

The foundational shift of the AI era is that **capability is no longer the scarce resource**. When GPT-class reasoning is a metered API call, the question "can software do this?" almost always answers yes. The scarce resources are trust, integration, and reliability at the tail. A gimmick impresses in the happy path and collapses on the 15% of cases that make up the actual job; a durable product is one a customer would feel real, budgeted pain from losing on a Tuesday.

The single most useful filter is the **ChatGPT test**: if a competent user could get 80% of your output by pasting their problem into a frontier chatbot, you do not have a product, you have a prompt with a logo.[^valueadd] Passing it requires that your value live in something the raw model cannot reach: proprietary or permissioned data, a workflow the model cannot execute on its own, an integration surface that is painful to assemble, or an accountability guarantee - an SLA, an audit trail, a human-in-the-loop escalation - that a chatbot will never offer.

{sn: The corollary: your first demo should deliberately show the ugly case - the ambiguous ticket, the malformed input, the edge that breaks toys. If it survives that, you have something.}

::: definition
**Durable AI value** - value that persists after the novelty of "the AI did that" wears off, because it is anchored to a measurable business outcome, a data asset that compounds, or a workflow the customer cannot easily unwind.
:::

Consider our running example. **Cortex** is an autonomous AI support agent for mid-market SaaS companies. A gimmick version is a chat widget that answers questions in a friendly tone - genuinely nice, and utterly indistinguishable from a weekend build. The durable version resolves tickets end to end: it reads the customer's actual account state through their CRM and billing system, executes the refund or the plan change, writes the resolution back, and hands off cleanly when it is not confident. The difference is not the model. It is that Cortex is wired into systems of record and is accountable for an outcome the buyer already pays humans to produce. Through 2026, the leading agent vendors - Sierra, Decagon, Ada - repriced the category around *resolved work*, publishing resolution-rate benchmarks instead of feature lists.[^superkind]

{case: **The outcome bar** - When agent vendors stopped selling "AI assistants" and started selling resolved tickets, the gimmick tier stopped clearing buyer scrutiny. A friendly-toned chat widget is now table stakes; a published resolution rate is the ask.}

## Segmenting for AI: who feels the pain enough

AI does not change *whether* you need a sharp ICP - it changes *which* segment converts. The winning segment has three properties: the work is **high-volume and repetitive** (so automation compounds), the **cost of the status quo is legible** (so you can price against a number the buyer already knows), and the buyer has **tolerance for probabilistic output** (so a 92%-correct agent is a win, not a compliance incident).

That last property is where founders misjudge. Regulated, low-latency, or zero-error-tolerance segments - clinical diagnosis, wire transfers, legal filings - feel like huge markets but punish the stochastic nature of a model. The sweet spot is work that is expensive, voluminous, and *forgiving at the margin* because errors are recoverable and a human backstop exists. This is why **vertical AI agents are outgrowing horizontal SaaS**: industry-specific agents grew 18-32% annually against 12-15% for horizontal tools, because a narrow segment lets you tune for its tail cases and sell completed work instead of software seats.[^saasmag]

Cortex does not target "companies that do customer support." It targets **mid-market SaaS support teams** (roughly 50-500 employees) drowning in Tier-1 tickets - password resets, billing questions, plan changes - where each ticket has a known fully-loaded cost, volume is high, and a wrong answer means an annoyed customer, not a lawsuit. Enterprise support has procurement cycles and bespoke compliance; SMB support has no budget. Mid-market feels the pain, controls its own budget, and can say yes in a quarter.

| Segment axis | Gimmick-prone segment | Durable AI segment |
|---|---|---|
| Task volume | Occasional, bespoke | High-frequency, repetitive |
| Cost of status quo | Diffuse, hard to name | Legible (salaries, per-ticket cost) |
| Error tolerance | Zero (legal, medical, payments) | Recoverable, human backstop exists |
| Data access | Locked, siloed, permissioned out | Reachable via API / integration |
| Buyer authority | Committee, long procurement | Departmental owner, quarterly budget |

::: rule
**Founder's Rule:** Sell to the buyer who can name the number your AI moves - in dollars, hours, or tickets - by the end of the first call.
:::

{sn: A useful test for "pain enough": would the buyer keep paying if you removed the AI branding and just billed them for the outcome? If yes, the pain is real. If the AI *is* the pitch, it is a gimmick.}

## Product-market-fit signals for AI products

The classic PMF instruments still apply, but AI products throw off two dangerous false positives. **First, demo euphoria.** AI products get abnormally strong early traction because the demo is magic - and then churn hard when users hit the reliability wall. Signup curves lie; retention curves do not. **Second, usage without value.** Users poke at your AI out of curiosity, inflating engagement metrics that have nothing to do with willingness to pay.

The signals that actually matter for AI, in rough order of trustworthiness:

- **Retention curve flattening.** Does a cohort plateau at a non-trivial level after the novelty decays, or decay to zero? A flat tail is the single strongest PMF signal, and for AI it must survive the "magic wore off" moment. Best-in-class SaaS in 2026 targets net dollar retention with annual churn below 5%.[^everhelp]
- **The outcome metric moves.** For Cortex the north-star is **deflection rate** - the share of tickets fully resolved without a human. If it climbs cohort-over-cohort and stays high in month three, that is PMF. If it spikes in week one and sags as edge cases accumulate, that is a demo.
- **Segmented Sean Ellis score.** "How disappointed would you be if this went away?" above 40% - but segmented by ICP, because a blended score hides the fact that your mid-market cohort loves you and your tire-kickers do not.[^userintuition]
- **Expansion and pull.** Do customers route *more* ticket types to the agent unprompted? Expansion revenue and unprompted scope-creep are the clearest economic proof the value is real.
- **Willingness to pay per outcome.** The ultimate AI PMF test is whether a customer will sign a contract that pays *per resolved ticket* - because that means they trust the outcome enough to bet their budget on it.

{case: **The raised retention bar** - By 2026, teams running AI-driven support reported monthly churn reductions of 2-3 points - enough to move a company from median to top-quartile retention. AI PMF is now measured against a bar your buyers can already see.}

None of these signals is trustworthy without a rigorous evaluation harness: evals are what separate a genuine PMF signal from luck and let you defend your deflection numbers to a skeptical buyer. Treat them as validation infrastructure (see Chapter 6) and as the production monitor that keeps fit certified (see Chapter 10).

<figure class="diagram">
<svg viewBox="0 0 720 400" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two-by-two matrix positioning AI features by capability novelty against workflow depth, with the deep-workflow high-novelty quadrant highlighted as durable value.">
  <style>.dg text{font-family:var(--sans);fill:var(--ink);font-size:13px} .dg .box{fill:var(--paper-2);stroke:var(--rule-2)} .dg .accent{fill:var(--accent-bg);stroke:var(--accent)} .dg .lbl{fill:var(--muted);font-size:11px;font-weight:600} .dg .flow{stroke:var(--rule-2);stroke-width:1.6;fill:none} .dg .qt{font-size:12px;font-weight:600} .dg .qs{fill:var(--muted);font-size:10.5px}</style>
  <defs><marker id="ch4arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--rule-2)"/></marker></defs>
  <g class="dg">
    <path class="flow" d="M70 350 L70 40" marker-end="url(#ch4arrow)"/>
    <path class="flow" d="M70 350 L690 350" marker-end="url(#ch4arrow)"/>
    <text class="lbl" x="20" y="200" transform="rotate(-90 20 200)">Workflow depth &#8594;</text>
    <text class="lbl" x="360" y="380">Capability novelty &#8594;</text>
    <rect class="box" x="90" y="200" width="285" height="135" rx="9"/>
    <text class="qt" x="105" y="230">Table stakes</text>
    <text class="qs" x="105" y="250">Shallow + familiar.</text>
    <text class="qs" x="105" y="266">A summarize button. Cloned in a week.</text>
    <rect class="box" x="385" y="200" width="285" height="135" rx="9"/>
    <text class="qt" x="400" y="230">Demo candy</text>
    <text class="qs" x="400" y="250">Novel but shallow.</text>
    <text class="qs" x="400" y="266">Impressive toy. The ChatGPT test</text>
    <text class="qs" x="400" y="282">kills it. Thin-wrapper territory.</text>
    <rect class="box" x="90" y="55" width="285" height="135" rx="9"/>
    <text class="qt" x="105" y="85">Sticky integration</text>
    <text class="qs" x="105" y="105">Deep but not novel.</text>
    <text class="qs" x="105" y="121">Defensible via switching cost,</text>
    <text class="qs" x="105" y="137">not intelligence. Solid, not a rocket.</text>
    <rect class="accent" x="385" y="55" width="285" height="135" rx="9"/>
    <text class="qt" x="400" y="85">Durable AI value</text>
    <text class="qs" x="400" y="105">Novel capability, deep workflow.</text>
    <text class="qs" x="400" y="121">Cortex: resolves the ticket end to end,</text>
    <text class="qs" x="400" y="137">wired to CRM + billing, priced per outcome.</text>
    <text class="qs" x="400" y="163">Aim here.</text>
  </g>
</svg>
<figcaption><strong>Figure 4.1</strong> - Position every AI feature by novelty and workflow depth; only the top-right quadrant resists commoditization.</figcaption>
</figure>

## The thin-wrapper trap and where to add real value

A **thin wrapper** is a product whose entire value is a prompt plus a UI over a foundation model's API, with nothing underneath. The economics are brutal: analyses in 2026 found that a majority of AI wrapper startups generate little or no revenue, and the widely-cited projection is that roughly 80% of wrappers will fail as foundation-model providers ship the same features natively.[^valueadd] "OpenAI ships your feature" is not a tail risk; it is the base case for any product whose only asset is a clever prompt.

The trap is seductive because a wrapper reaches a demo fastest and shows the best early activation - the exact metrics that fool founders and seed investors. The escape is to build value in a layer the model provider will never own:

- **Proprietary data and a flywheel.** Every resolved ticket teaches Cortex which answers work for *this* customer's product, and that labeled outcome data compounds into an accuracy edge a generic chatbot cannot match. This is the most durable layer, and the subject of Chapter 5.
- **Workflow depth and systems of record.** The model can draft a refund; only a product wired into Stripe, Zendesk, and the customer's internal APIs can *execute* it, log it, and stand behind it.
- **Reliability engineering.** The eval harnesses, guardrails, fallback logic, and human-escalation paths that turn a 92% happy-path model into a 99%-dependable product are real, hard-won IP (see Chapters 6 and 10).
- **Distribution and trust.** An SLA, SOC 2, an audit trail, and a brand a support VP will stake their job on - none of which a raw API confers.

::: warning
If your honest answer to "what do we own that OpenAI can't ship next quarter?" is "our prompt" or "our nicer UI," you are in the wrapper trap. Prompts are not IP; they leak, they get cloned, they get obsoleted by the next model release. Move value into data, workflow, or reliability before you raise on the demo.
:::

The nuance: **starting as a wrapper is fine; staying one is fatal.** The 2026 playbook is to wrap fast to reach the market, then use the resulting usage to accumulate a proprietary data and workflow moat before the window closes. Cortex ships on a frontier API on day one - it would be malpractice to train a foundation model - but its defensibility comes from the resolution data, integrations, and deflection guarantees it accumulates, not the model it rents. Where that moat comes from, and how to sequence its construction, is the whole of Chapter 12.

## AI business models and usage-based pricing

Pricing is where AI product strategy becomes a business. The historical default - **per-seat SaaS** - is actively breaking, because the entire promise of an AI agent is to do the work of seats. Charging per human seat while you eliminate human seats is a contradiction the buyer notices immediately. The data confirms the shift: pure per-seat pricing fell from 21% to 15% of SaaS companies between 2025 and 2026, and IDC forecasts that 70% of vendors will move off pure per-seat models by 2028.[^monetizely] The natural pricing unit for an agent is the **unit of work it completes**, not the number of people with a login.

Three models dominate, and the right choice follows directly from how legible and attributable your value is:

| Model | You charge for | Best when | Risk to you | 2026 signal |
|---|---|---|---|---|
| **Per-seat** | Named users with access | Humans are augmented, not replaced | Collapses as agents cut headcount | Falling: 21% &#8594; 15% of SaaS[^monetizely] |
| **Usage-based** | Tokens, API calls, tasks attempted | Value scales with volume; outcomes hard to attribute | Bill shock; you eat cost on failed/retried work | Dominant for AI infra; hybrid is the norm[^flexprice] |
| **Outcome-based** | Successful results (resolved ticket, booked meeting) | Outcome is measurable and cleanly attributable | You absorb model-cost variance en route to each outcome | Fastest-growing frontier; strong retention gains[^monetizely] |

Cortex lands on **per-resolution pricing** - it bills only when a ticket is fully resolved without a human, and charges nothing on escalations. This is the model the category converged on: through 2026, per-resolved-ticket pricing ran roughly $0.49-$2.00, with Intercom's Fin at a reference $0.99 per resolution and Zendesk moving its automation to $1.50-$2.00 per resolution while retiring its legacy bots.[^drag][^drag2] Per-resolution pricing is *self-validating*: the buyer pays only when Cortex demonstrably did the job, which demolishes purchasing resistance, and it forces Cortex's incentives into alignment with the customer's - every dollar of revenue is a ticket a human did not have to touch.

{case: **The $0.99 anchor** - Intercom's Fin bills a flat $0.99 per resolution; above roughly 3,000 monthly conversations, outcome pricing typically beats per-seat once helpdesk fees and agent salaries are folded in. The market has already taught your buyer what a resolution is worth - price against that anchor rather than inventing a new unit.}

The catch founders underestimate: **outcome pricing pushes cost variance onto you.** Every failed attempt, retry, and long agent trajectory burns model tokens you paid for but cannot bill. If your inference cost per attempted resolution creeps toward your per-resolution price, your gross margin evaporates regardless of how many tickets you deflect. This is why the modern default is a **hybrid**: a platform base fee for predictability plus an outcome component for alignment - a structure 43% of SaaS companies used in 2026, projected to reach 61%.[^monetizely] The base fee covers your fixed integration and infrastructure cost; the per-outcome charge captures value.

::: rule
**Founder's Rule:** Price on the unit your customer counts their value in - and make sure your cost to produce that unit is a small, stable fraction of what you charge for it.
:::

The coupling between your pricing unit and your inference cost per that unit is the central unit-economics problem of an AI business, and it earns its own rigorous treatment - the gross-margin math, cost-of-goods modeling, and token-budget discipline that keep outcome pricing solvent live in Chapter 13. What matters here in strategy is the sequencing: **choose the outcome your buyer already counts, price against the market's existing anchor for it, then engineer your cost per outcome down until the margin is durable.** Get that loop right and pricing stops being a spreadsheet exercise and becomes your sharpest go-to-market weapon.

::: takeaways
**Key takeaways**
- Capability is cheap; trust, integration, and tail reliability are the scarce resources. Apply the **ChatGPT test** to every feature - if a chatbot gets 80% of the way, you have a prompt, not a product.
- Target segments with **high-volume repetitive work, legible status-quo cost, and tolerance for probabilistic output**. Vertical agents beat horizontal tools because they sell completed work, not seats.
- For AI, **retention beats activation** as a PMF signal - demo euphoria produces false positives. The strongest signal is willingness to pay *per outcome*.
- Starting as a wrapper is fine; staying one is fatal. Move value into **proprietary data, workflow depth, and reliability engineering** before the model provider ships your feature.
- Per-seat pricing is breaking. Price on the **unit of work** - usage or outcome - and default to a **hybrid** base-plus-outcome structure to survive cost variance.
:::

::: exercise
**Hands-on: Position and price your AI product**
1. Write your product's core feature on one line, then run the ChatGPT test: could a competent user get 80% of the output from a frontier chatbot today? If yes, name the specific data, workflow, or accountability layer you will add to fail that test.
2. Plot your top three features on the Figure 4.1 matrix (novelty vs. workflow depth). Any feature not in the top-right quadrant is either a roadmap risk or a deliberate loss-leader - label which.
3. Define your ICP by the three durable-segment axes: task volume, legible status-quo cost (in dollars), and error tolerance. Write the single number your product moves for that buyer.
4. Identify the **unit of value** your buyer already counts (resolutions, meetings, contracts, hours). Find the market's existing per-unit price anchor for it via a competitor.
5. Estimate your **inference cost per attempted unit** (including failures and retries) and divide by your proposed per-unit price. If that ratio exceeds ~30%, redesign toward a hybrid base-plus-outcome model and flag it for the unit-economics work in Chapter 13.
:::

[^valueadd]: Startup Strategy in the AI Era: Why 80% of Wrappers Die and 5 Moats That Survive. <https://valueaddvc.com/blog/how-to-build-a-startup-in-a-market-where-ai-will-eventually-do-what-you-do>
[^superkind]: The Best AI Customer Support Agents in 2026: Decagon, Sierra, Intercom Fin, and When to Build Your Own. <https://superkind.ai/blog/ai-customer-support-agents>
[^saasmag]: Vertical AI Agents Are Eating Horizontal SaaS in 2026. <https://www.saasmag.com/vertical-ai-agents-eating-horizontal-saas/>
[^everhelp]: The 2026 SaaS retention benchmarks every founder should know. <https://www.ever-help.com/blog/saas-retention-rate-benchmarks>
[^userintuition]: How to Measure Product-Market Fit in SaaS. <https://www.userintuition.ai/reference-guides/measure-product-market-fit-saas/>
[^monetizely]: The 2026 Guide to SaaS, AI, and Agentic Pricing Models. <https://www.getmonetizely.com/blogs/the-2026-guide-to-saas-ai-and-agentic-pricing-models>
[^flexprice]: Why AI Companies Have Adopted Usage Based Pricing in 2026. <https://flexprice.io/blog/why-ai-companies-have-adopted-usage-based-pricing>
[^drag]: The State of AI Support Pricing 2026: Every Model, Every Rate. <https://www.dragapp.com/blog/state-of-ai-support-pricing/>
[^drag2]: AI Agent Pricing in 2026: What Fin, Sierra, Decagon and Agentforce Actually Charge. <https://www.thewitn.com/blog/ai-agent-pricing-in-2026-what-fin-sierra-decagon-and-agentforce-actually-charge>