---
part: Part V - Company Building
part_num: V
chapter_num: 15
title: Pitfalls & Crises in AI
dek: The failure modes unique to AI companies - and how to survive the day the model breaks.
slug: 15-pitfalls-crises-ai
reading_time: 20 min read
---

Every startup faces crises. AI startups face a category that did not exist a decade ago: the day your product silently gets worse and no one on your team changed a line of code. Your core dependency is a black box you rent, it mutates without warning, and when it fails it fails for you and every competitor at the same instant. This chapter is the field manual for that world - the taxonomy of AI-native failures, and the playbook to detect, contain, and recover from each.

## The AI-Specific Failure Catalog

Traditional software fails deterministically: a bug is a bug, a null is a null, a fix is permanent. AI systems fail **probabilistically and non-locally**. The same input produces a good answer on Tuesday and a lawsuit on Wednesday, and the root cause may live inside a model you neither trained nor host. Founders who carry a SaaS mental model into an AI company misdiagnose these incidents for weeks.

{sn: The through-line: in classical software you own your failure surface. In AI you rent most of it. Every item below is a failure of something you do not fully control.}

Six failure classes are genuinely new, and each has a distinct signature, blast radius, and owner. Treating them as one undifferentiated "the AI is acting weird" bucket is the mistake - triage collapses when you cannot name what broke.

| Failure class | Signature | Typical trigger | Blast radius | Owner |
|---|---|---|---|---|
| **Model regression** | Quality drops overnight, no deploy | Silent provider update; alias re-pointed | All traffic on that model | This chapter |
| **Hallucination / safety** | Confident, wrong, sometimes harmful output | Edge-case prompt; RAG gap; jailbreak | One user, then headlines | This chapter |
| **Provider dependency** | Hard outage, deprecation, rate-limit wall | Vendor incident; sunset email | 100% availability | This chapter |
| **Cost blowup** | Bill 5-40x forecast | Reasoning-token creep; retry storms; abuse | Runway | Ch. 13 |
| **Eval/monitor blind spot** | You learn from a customer, not a dashboard | Missing metric; no canary | Trust, silently | Ch. 10 |
| **Data/flywheel poisoning** | Model degrades as it "learns" | Feedback loop on bad labels | Long-term quality | Ch. 5 |

The detection layer that catches most of these - online evals, drift monitors, canary prompts, alerting - is **Chapter 10's** domain, and we lean on it here without re-deriving it. This chapter starts the moment the pager goes off.

:::rule
In an AI company, your uptime and your quality are two different numbers, and only one of them shows up on your status page. Monitor the one that does not.
:::

## Model Regressions and the Overnight Quality Drop

This failure mode has no analog in classical software, so founders are least prepared for it. You wake up, nothing in your repo changed, and your product is measurably dumber. The cause is almost always upstream: the provider updated the weights behind a model alias, re-pointed a default, or shipped a new snapshot tuned for benchmarks you do not care about.

It is not paranoia - it is documented. Researchers have tracked measurable behavior drift in the *same* named model across dates, with silent provider-side updates the only plausible explanation.[^drift] The broader pattern is well understood: newer frontier models optimize for reasoning and safety scores over the "helpful assistant" behavior of the GPT-4 era, so a model that scores *higher* on standardized tests can feel *worse* on your task.[^worse] GPT-5.5 at its highest reasoning setting posted the top score on the AA-Omniscience knowledge benchmark (57%) while confabulating on roughly 86% of the questions it got wrong - the highest confident-error rate of any frontier model measured.[^omni] A benchmark win is not a win for your users.

{sn: The cruelest property of a regression: it is invisible to your CI. Every test that mocks the model still passes. Only tests that hit the *live* model catch it, and most teams do not run those on a schedule.}

### Cortex meets the regression

Our running example, **Cortex** - the autonomous customer-support agent for mid-market SaaS - is about to have the worst Tuesday of its corporate life. In **Chapter 10** we wired Cortex with an online eval harness: a golden set of 300 real tickets replayed hourly against production, scoring resolution rate and escalation correctness. At 02:14, that harness fires the alert nobody wanted. Overnight, autonomous resolution rate has fallen from 71% to 52%. No deploy. No config change. The provider pushed a new snapshot behind the model alias Cortex calls by default, and the new snapshot is chattier, quicker to punt to a human, and - worse - occasionally inventing refund policies that do not exist.

This is the crisis this chapter hinges on. The rest is how the team survives it.

The regression playbook, in order:

1. **Confirm it is upstream, not you.** Diff your last 48h of deploys first - 30 seconds, your CI log answers it. If clean, replay your golden set against a *pinned* prior snapshot. If pinned recovers quality, you have a confirmed provider regression.
2. **Pin immediately.** Never call a model by a floating alias in production. Cortex should have been calling `claude-sonnet-5-20260514`, not `claude-sonnet-latest`. The pin is your rollback lever; with no pin to roll back *to*, you have no lever.
3. **Roll back to the last-good pin.** This is containment: quality restored while you investigate, at the cost of running an older model.
4. **File the provider ticket with evidence.** Your golden-set deltas are the artifact. Providers move faster with reproducible before/after numbers.
5. **Re-qualify the new snapshot deliberately.** You will adopt it eventually - the old one gets deprecated (see Deprecation, below). Re-run your full eval suite, tune prompts against the new behavior, and cut over on *your* schedule.

:::warning
If any part of your stack calls a model by a `-latest` or undated alias, you have handed a stranger the right to ship to your production without a code review. Pin every model id, everywhere, today. This single discipline converts most regression crises from outages into non-events.
:::

The largest sunset yet shows why the calendar is non-negotiable.[^gpt4]

{case: **The GPT-4 sunset, early 2026** - OpenAI retired its GPT-4-era models (GPT-4o, GPT-4.1, GPT-4.1 mini, o4-mini) from ChatGPT on February 13, 2026, with full retirement following, forcing teams onto GPT-5.x models that behaved measurably differently on production tasks. Teams that had pinned dated snapshots got a migration window; teams on floating aliases got an involuntary, uncontrolled behavior change.}

## Hallucination and Safety Incidents

A regression degrades quality. A hallucination or safety incident degrades *trust* - and increasingly, exposes you to *liability*. The legal ground shifted hard, and every AI founder needs the new posture: **courts now hold companies liable for what their chatbots say.**

The precedents stacked up fast. The 2024 Air Canada tribunal ruling - the airline liable for a chatbot's fabricated bereavement-fare policy - was the opening.[^airc] Then the doctrine hardened. In May 2025, a US federal judge in the Garcia (Setzer) case rejected the argument that chatbot output is protected speech and ruled it could be treated as a **product** under product-liability law;[^product] in January 2026, Character.AI and Google settled that case and four related suits.[^settle] On May 12, 2026, Germany's Higher Regional Court of Hamm held a company liable for false statements its own chatbot made about its physicians' qualifications.[^germany] The insurance market has priced it in: in 2025 a Lloyd's-backed policy - via coverholder Armilla, underwritten by syndicate Chaucer - began covering losses from AI underperformance and hallucination.[^insurance]

{sn: "The AI said it, not us" is now a losing legal argument in multiple jurisdictions. Design as though every generated sentence is a statement your company published on its letterhead - because that is how a court reads it.}

For Cortex, the exposure is concrete. An autonomous support agent that invents a refund policy may be forming a binding representation to a customer, and its operator - your customer, the SaaS company - will look straight through Cortex to *you*. The refund-policy hallucination from the regression above is therefore two incidents, not one: a quality regression *and* a safety incident, and the safety half has the longer tail.

### Containing a safety incident

The mechanics differ from a regression: you cannot simply roll back and relax, because harm may already be in the wild.

- **Kill switch to a safe fallback.** Cortex needs a hardcoded degraded mode: when confidence is low or the topic is money/legal/medical, stop generating and hand to a human with a templated, pre-approved message. This is the single most important safety primitive in an agent product. Build it before you need it.
- **Constrain, do not just prompt.** Ground factual claims in retrieval (RAG, see **Chapter 3**) with citations, and refuse to state policy that is not in the retrieved source. "I don't have that on file, let me get a human" is a *feature*.
- **Log everything, retain the trace.** When you get a legal inquiry, the full prompt/context/output trace for that interaction is your evidence. If you cannot reconstruct exactly what the model saw and said, you cannot defend it.
- **Scope the blast radius by query.** Search your logs for every interaction that hit the same failure pattern, not just the one that got reported. One reported hallucination usually has dozens of silent siblings.

:::definition
**Confident wrongness** - the defining hazard of generative systems: output that is fluent, plausible, and authoritative while being false. More dangerous than a crash because it does not announce itself - users extend it the trust they would give a correct answer.
:::

## Provider Dependency and Deprecation

Your model provider is simultaneously your most critical infrastructure and a vendor you cannot audit, cannot SLA into submission, and cannot stop from changing under you. This dependency shows up as three distinct crises: the hard outage, the planned deprecation, and the cost blowup.

### Hard outages

AI APIs are, empirically, among the least reliable API categories tracked.[^outage] This is not hypothetical. On June 2, 2026, Anthropic's Claude threw 500 and 529 errors across the API, Console, and Claude Code in a global outage - one of a cluster of disruptions that month.[^claudeout] If your product hard-depends on a single provider, your uptime ceiling is *theirs*, which is worse than you think.

The architecture that survives this - a provider-abstraction layer, a warm fallback from a second vendor, graceful degradation - is **Chapter 7's** (provider choice) and **Chapter 9's** (infra and fallback) territory; we do not re-derive it. The crisis-response point is narrower: your fallback must be *tested in production regularly*, or it is decoration. A failover path exercised for the first time during an outage fails during the outage. Cortex runs a weekly game-day that forcibly disables its primary provider for ten minutes of live traffic; the first run exposed that the fallback's different tokenizer silently truncated context and tanked quality - exactly the thing you want to learn on a Tuesday, not during a page.

### Deprecation

Every model you build on has a scheduled death. The providers have formalized this: **Anthropic commits to at least 60 days' notice** and publishes a per-model retirement date;[^anthdep] **OpenAI gives at least six months for GA models, three for specialized variants, and as little as two weeks for previews.**[^deprecate] Deprecation is the one AI crisis you get advance warning for - which makes missing it inexcusable.

| Provider | Min. notice (GA) | Preview/specialized | Signal to watch |
|---|---|---|---|
| Anthropic | ~60 days | shorter for legacy | Per-model retirement date[^anthdep] |
| OpenAI | ~6 months | 3 mo / 2 wk (preview) | Deprecations doc + email[^deprecate] |
| Cloud-hosted (Bedrock/Vertex) | varies by model | varies | Provider lifecycle calendars |

The discipline: subscribe to every provider's deprecation feed, maintain a model-lifecycle calendar as a standing artifact, and keep every model no more than one "migration hop" from a supported successor. Treat the sunset email as a sprint ticket the day it arrives, not the week before the deadline.

Deprecation is not always confined to the *model*.[^sora]

{case: **The Sora shutdown, 2026** - OpenAI announced on March 24, 2026 that it was winding down its standalone Sora video app (discontinued April 26, API to follow), redirecting compute toward coding and enterprise products. The pattern is the recurring existential deprecation: foundation-model companies routinely absorb the exact feature a startup was built on. Sometimes it is not your *model* that gets deprecated - it is your *entire product wedge*. This is a defensibility problem (see **Chapter 12**) that arrives dressed as a deprecation crisis.}

### Cost blowups

The bill becomes a crisis when it outruns revenue, and 2026's fragmented, per-token-type pricing means two teams building similar apps can land 10x apart on cost.[^pricing] The economics - unit economics, gross-margin math, cost controls - are **Chapter 13's** to own. The only crisis-response point here: treat a cost spike as an *incident with its own runbook* - per-tenant token-budget circuit breaker, hard caps on output and reasoning tokens, retry-storm detection, and alerting on cost-per-resolution, not just total spend. Cortex bills per resolved ticket; the day the regression made the model chattier, cost-per-resolution jumped 30% *while* quality fell - one event, two crises.

## Crisis Response, the Pivot and Post-Mortems

Naming failures is table stakes. What separates companies that survive AI crises is a *rehearsed response loop*. When Cortex's resolution rate cratered at 02:14, the difference between a two-hour incident and a two-week trust collapse was whether the team ran a process or improvised one.

The loop has five stages, and every AI incident - regression, hallucination, outage, cost - runs the same path.

<figure class="diagram">
<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AI incident response flow: detect, contain, communicate, post-mortem, harden">
  <style>.dg text{font-family:var(--sans);fill:var(--ink);font-size:13px} .dg .box{fill:var(--paper-2);stroke:var(--rule-2)} .dg .accent{fill:var(--accent-bg);stroke:var(--accent)} .dg .rec{fill:var(--sage-bg);stroke:var(--sage)} .dg .lbl{fill:var(--muted);font-size:11px;font-weight:600} .dg .flow{stroke:var(--rule-2);stroke-width:1.6;fill:none}</style>
  <defs><marker id="arrow15" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--rule-2)"/></marker></defs>
  <g class="dg">
    <rect class="accent" x="8" y="70" width="118" height="56" rx="9"/>
    <text x="67" y="94" text-anchor="middle">Detect</text>
    <text class="lbl" x="67" y="112" text-anchor="middle">Ch.10 evals</text>
    <rect class="box" x="156" y="70" width="122" height="56" rx="9"/>
    <text x="217" y="94" text-anchor="middle">Contain</text>
    <text class="lbl" x="217" y="112" text-anchor="middle">rollback / pin</text>
    <rect class="box" x="308" y="70" width="122" height="56" rx="9"/>
    <text x="369" y="94" text-anchor="middle">Communicate</text>
    <text class="lbl" x="369" y="112" text-anchor="middle">customers first</text>
    <rect class="box" x="460" y="70" width="122" height="56" rx="9"/>
    <text x="521" y="98" text-anchor="middle">Post-mortem</text>
    <rect class="rec" x="612" y="70" width="100" height="56" rx="9"/>
    <text x="662" y="98" text-anchor="middle">Harden</text>
    <path class="flow" d="M126 98 L156 98" marker-end="url(#arrow15)"/>
    <path class="flow" d="M278 98 L308 98" marker-end="url(#arrow15)"/>
    <path class="flow" d="M430 98 L460 98" marker-end="url(#arrow15)"/>
    <path class="flow" d="M582 98 L612 98" marker-end="url(#arrow15)"/>
    <path class="flow" d="M662 70 C662 30, 67 30, 67 70" marker-end="url(#arrow15)"/>
    <text class="lbl" x="365" y="24" text-anchor="middle">harden feeds new detectors back to Detect</text>
  </g>
</svg>
<figcaption><strong>Figure 15.1</strong> - The AI incident response loop: detection feeds containment, and hardening closes the loop by feeding new detectors back to the top.</figcaption>
</figure>

**Detect** is Chapter 10's job and the reason to invest there before you need it. **Contain** is the rollback/pin/kill-switch action - restore a known-good state *before* you understand root cause. Resist the engineer's urge to debug first; containment and diagnosis are separate phases, and inverting them extends the outage.

### Communicate: the AI-specific comms trap

**Communicate** is where AI companies uniquely self-destruct. The instinct is silence - hope customers do not notice the quality dip. It fails twice: customers *do* notice (2026 saw visible subscription churn tied directly to quality complaints[^worse]), and silence during a *safety* incident converts a bug into a cover-up. The rule: **communicate the quality incident to affected customers before they raise it, and never blame the model as if it were an act of God.** "Our upstream provider shipped a regression; we detected it in 12 minutes, rolled back, and here is the resolution-rate graph" builds trust. "The AI had a hiccup" destroys it. When the incident touches safety or a potentially harmful output, involve counsel early - given the 2026 liability rulings, your incident comms may become discovery.

{sn: A public, numeric, slightly-too-honest incident report is the best trust-building content an AI startup can publish. It signals you *measure* quality - which most of your competitors cannot claim.}

:::rule
Contain before you diagnose. Communicate before you're asked. Customers will forgive a model that broke; they will not forgive a vendor who hid it.
:::

### Post-mortem and harden

The **post-mortem** is blameless and mechanical: timeline, root cause, detection latency, time-to-contain, customer impact in real units (resolutions lost, tickets mis-answered). The **harden** stage closes the loop - and here is the AI-specific twist: *every incident must produce at least one new eval case*. Cortex's refund-policy hallucination becomes a permanent adversarial test in the golden set, so that exact failure can never silently return. This is how an AI company's quality moat compounds (see **Chapter 5** on the data flywheel and **Chapter 12** on moats): not from never failing, but from converting each failure into a detector that makes the next one impossible.

### When the crisis is existential: the pivot

Some crises are not incidents you recover from - they are signals to change the company. In 2026, roughly **80% of the thin-wrapper AI startups launched from 2023-2025 were on track to shut down**, most because they had no proprietary data or moat and foundation models shipped their feature natively.[^wrapper] If your recurring crisis is "the provider just launched what we do, for free," no runbook saves you - that is a strategy failure wearing a crisis costume. The tell is diagnostic: a *quality* or *cost* crisis is operational and survivable with the loop above; a *displacement* crisis - your wedge got absorbed, your differentiation evaporated - demands a pivot toward proprietary data, a defensible workflow, or a vertical the incumbents will not chase (see **Chapters 4 and 12**). The founders who die slowly are the ones who run the incident loop faster and faster on a business the loop cannot save.

:::takeaways
**Key takeaways**
- AI has six native failure classes - regression, hallucination/safety, provider dependency, cost blowup, monitoring blind spot, flywheel poisoning. Name them separately or triage collapses.
- Model regression is the failure with no classical analog: quality drops with zero deploys. Pin every model id; a floating alias hands a stranger commit access to your production.
- 2025-2026 case law treats chatbot output as a *product* your company is liable for. Build a kill-switch to a safe human fallback, ground claims in retrieval, and retain full traces.
- Deprecation is the one crisis with advance notice - Anthropic ~60 days, OpenAI ~6 months for GA. Missing it is inexcusable; treat every sunset email as a sprint ticket.
- Run one incident loop for every crisis: detect -> contain -> communicate -> post-mortem -> harden. Contain before you diagnose; communicate before you're asked.
- Every incident must mint a new eval case. That is how quality compounds - not by never failing, but by making each failure un-repeatable.
- Distinguish an operational crisis (survive it with the loop) from a displacement crisis (your wedge got absorbed - that needs a pivot, not a runbook).
:::

:::exercise
**Hands-on: Run a model-regression game-day**
1. Pick your most critical model call. Confirm it uses a *pinned, dated snapshot* id, not a floating alias. If it doesn't, fix that first - the rest of this exercise assumes a pin exists to roll back to.
2. Assemble a golden set of 50-100 real production inputs with known-good expected behavior. Score your current model on it and record the baseline.
3. Simulate the regression: point the call at a *different* snapshot (newer or older) and re-score. Measure the quality delta and the cost-per-call delta.
4. Time your containment: from "alert fires" to "rolled back to last-good pin," how many minutes? Anything over 15 means your rollback isn't a one-command operation - fix that.
5. Draft the customer comms you'd send, with a real metric and no blame-the-model language. Have someone outside engineering read it cold.
6. Convert the failure you found into one permanent eval case and add it to your monitoring (Chapter 10). You've hardened the loop once - now schedule this game-day monthly.
:::

[^drift]: Chen, Zaharia & Zou, "How Is ChatGPT's Behavior Changing over Time?" (Stanford/Berkeley), documenting measurable drift in a fixed model across dates. <https://arxiv.org/abs/2307.09009>
[^worse]: Is ChatGPT Getting Worse in 2026? What Changed. NxCode. <https://www.nxcode.io/resources/news/chatgpt-getting-worse-2026-what-changed-alternatives>
[^omni]: AA-Omniscience: Knowledge and Hallucination Benchmark. Artificial Analysis. <https://artificialanalysis.ai/evaluations/omniscience>
[^gpt4]: Retiring GPT-4o, GPT-4.1, GPT-4.1 mini, and OpenAI o4-mini. OpenAI. <https://openai.com/index/retiring-gpt-4o-and-older-models/>
[^airc]: B.C. man wins case against Air Canada after chatbot gave him bad advice. CBC News. <https://www.cbc.ca/news/canada/british-columbia/air-canada-chatbot-lawsuit-1.7116416>
[^product]: In early ruling, federal judge defines Character.AI chatbot as a product, not speech. Transparency Coalition. <https://www.transparencycoalition.ai/news/important-early-ruling-in-characterai-case-this-chatbot-is-a-product-not-speech>
[^settle]: Character.AI Lawsuit (2026 update): Garcia settlement and related suits. Wisner Baum. <https://www.wisnerbaum.com/ai-chatbot-lawsuit/character-ai-lawsuit/>
[^germany]: Germany: Court Rules Chatbot Operators Are Liable for AI Hallucinations. Library of Congress. <https://www.loc.gov/item/global-legal-monitor/2026-06-09/germany-court-rules-chatbot-operators-are-liable-for-ai-hallucinations/>
[^insurance]: Armilla reveals purpose-built AI liability insurance with Lloyd's underwriter Chaucer. Reinsurance News. <https://www.reinsurancene.ws/armilla-reveals-purpose-built-ai-liability-insurance-amid-rising-legal-and-regulatory-pressures/>
[^outage]: Your AI Provider Had Outages Last Month. Now What? TierZero. <https://www.tierzero.ai/blog/ai-provider-outages-2026/>
[^claudeout]: Anthropic confirms Claude is down worldwide. BleepingComputer. <https://www.bleepingcomputer.com/news/artificial-intelligence/anthropic-confirms-claude-is-down-worldwide/>
[^deprecate]: Deprecations - OpenAI API. <https://developers.openai.com/api/docs/deprecations>
[^anthdep]: Model deprecations. Claude Docs (Anthropic). <https://docs.claude.com/en/docs/about-claude/model-deprecations>
[^sora]: OpenAI sets two-stage Sora shutdown with app closing April 2026 and API following in September. The Decoder. <https://the-decoder.com/openai-sets-two-stage-sora-shutdown-with-app-closing-april-2026-and-api-following-in-september/>
[^pricing]: LLM API Pricing in 2026: The Complete Cost Comparison. AI Magicx. <https://www.aimagicx.com/blog/llm-api-pricing-comparison-2026>
[^wrapper]: Startup Strategy in the AI Era: Why 80% of Wrappers Die and 5 Moats That Survive. Value Add VC. <https://valueaddvc.com/blog/how-to-build-a-startup-in-a-market-where-ai-will-eventually-do-what-you-do>