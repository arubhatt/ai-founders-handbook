---
part: Part III - The Stack
part_num: III
chapter_num: 10
title: Production Evals & Monitoring
dek: Shipping is not the end of evaluation. How to catch silent quality drift before your customers do.
slug: 10-production-evals-monitoring
reading_time: 17 min read
---

Your pre-launch eval suite is a photograph: a fixed set of cases, scored once, green before you shipped. Production is a river. The model you called yesterday is not guaranteed to be the model you call today, the questions your users ask drift week over week, and a prompt tweak that improved one cohort quietly broke another. The founders who survive year two are the ones who treat evaluation as a **continuously running system**, not a launch-gate checkbox — because the alternative is learning about a quality collapse from an angry customer, a churned account, or a screenshot on X.

This chapter is about the machinery that watches quality after launch: continuous evals on live traffic, drift and regression monitoring, production guardrails and hallucination detection, and the discipline of surviving provider updates you never consented to. We build directly on the eval-set **design** principles from Chapter 6 (golden datasets, rubrics, LLM-as-judge calibration) and assume the tracing and observability plumbing from Chapter 9 is already emitting spans. Here we turn that plumbing into an early-warning system.

## From pre-launch evals to continuous evals

A pre-launch eval runs once against a curated dataset and answers "is this good enough to ship?" A **continuous eval** runs forever against a sample of real traffic and answers a harder question: "is this *still* good enough, right now, for the inputs users are actually sending?" The two share a rubric and a judge but differ in every operational dimension — cadence, sampling, cost model, and who gets paged when they fail.

The core mechanic is a loop: **production traffic → sample → auto-score → alert on regression → feed the failures back into the eval set.** Everything in this chapter is an elaboration of those five steps. The auto-scorer is usually a cheaper model acting as **LLM-as-judge** against the same rubric you validated pre-launch (see Chapter 6), plus deterministic checks — schema validation, regex for banned phrases, latency thresholds — that cost nothing and catch the dumb failures a judge would waste tokens on.

{sn: The single most common mistake here is running your *offline* eval suite on a cron and calling it "continuous." That tells you the model still passes yesterday's frozen cases. It tells you nothing about the novel inputs arriving today — which is exactly where regressions hide.}

The economics force a decision that pre-launch evals never do. Offline, you run every case because the dataset is small and you run it rarely. Online, an LLM-as-judge assessment costs roughly **$0.01–$0.10 per trace** depending on judge model and input size,[^langfuse] and that cost scales linearly with traffic — every trace you judge burns fresh tokens forever. So you tier your evaluation by cost and coverage:

| Eval layer | Coverage | Method | Cost profile | Catches |
|---|---|---|---|---|
| Deterministic checks | 100% of traffic | Regex, schema, latency, refusal detection | ~Free | Malformed output, banned phrases, timeouts |
| Small-model scorers | 100% of traffic | Distilled classifier / SLM judge | ~$0.001/trace | Faithfulness, toxicity, PII, off-topic |
| LLM-as-judge | 1–10% sample | Frontier judge vs. rubric | $0.01–$0.10/trace | Nuanced quality, tone, resolution correctness |
| Agent-as-judge | Flagged only | Multi-step judge with tool access | High | Trajectory errors, tool-misuse on anomalies |
| Human review | <1%, targeted | SME labeling queue | Very high | Ground truth, judge calibration, edge cases |

{sn: The 2026 consensus, visible across Langfuse, Braintrust and Galileo docs, is *cheap-and-wide plus expensive-and-narrow*: run distilled evaluators on 100% of traffic and reserve frontier or agent judges for the sample and the flagged anomalies. Never run your most expensive judge on every request — it does not scale and it does not need to.}

**Cortex**, our autonomous support agent for mid-market SaaS, runs exactly this stack. Every resolved ticket gets three free deterministic checks (did it produce valid tool calls, did it avoid the banned-phrase list, did it close under the latency SLA) and one distilled **faithfulness scorer** that verifies every claim in the reply traces back to a retrieved doc. Then 5% of resolved tickets are sampled into a frontier LLM-as-judge that scores **resolution quality** on a 1–5 rubric: did this actually solve the customer's problem, or did it merely sound helpful? That 5% sample, running every fifteen minutes, is the sensor that will later save the company.

:::rule
Continuous evals are cheap-and-wide plus expensive-and-narrow. Deterministic and distilled scorers on 100% of traffic; a frontier judge on a small, constant sample; a human on the anomalies.
:::

<figure class="diagram">
<svg viewBox="0 0 720 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The continuous evaluation loop from production traffic through sampling, scoring, regression alerting, and back into the eval set">
  <style>.dg text{font-family:var(--sans);fill:var(--ink);font-size:13px} .dg .box{fill:var(--paper-2);stroke:var(--rule-2)} .dg .accent{fill:var(--accent-bg);stroke:var(--accent)} .dg .rec{fill:var(--sage-bg);stroke:var(--sage)} .dg .lbl{fill:var(--muted);font-size:11px;font-weight:600} .dg .flow{stroke:var(--rule-2);stroke-width:1.6;fill:none}</style>
  <defs><marker id="arrowCh10" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--rule-2)"/></marker></defs>
  <g class="dg">
    <rect class="box" x="12" y="98" width="120" height="54" rx="9"/>
    <text x="72" y="122" text-anchor="middle">Production</text>
    <text x="72" y="139" text-anchor="middle">traffic</text>
    <rect class="box" x="176" y="98" width="120" height="54" rx="9"/>
    <text x="236" y="122" text-anchor="middle">Sample</text>
    <text x="236" y="139" text-anchor="middle" class="lbl">1–10% + 100% cheap</text>
    <rect class="accent" x="340" y="98" width="120" height="54" rx="9"/>
    <text x="400" y="122" text-anchor="middle">Auto-score</text>
    <text x="400" y="139" text-anchor="middle" class="lbl">judge + rules</text>
    <rect class="accent" x="504" y="98" width="120" height="54" rx="9"/>
    <text x="564" y="122" text-anchor="middle">Alert on</text>
    <text x="564" y="139" text-anchor="middle">regression</text>
    <rect class="rec" x="504" y="12" width="120" height="54" rx="9"/>
    <text x="564" y="36" text-anchor="middle">Triage</text>
    <text x="564" y="53" text-anchor="middle" class="lbl">rollback / patch</text>
    <rect class="rec" x="258" y="12" width="150" height="54" rx="9"/>
    <text x="333" y="36" text-anchor="middle">Feed back into</text>
    <text x="333" y="53" text-anchor="middle">eval set</text>
    <path class="flow" d="M132 125 H176" marker-end="url(#arrowCh10)"/>
    <path class="flow" d="M296 125 H340" marker-end="url(#arrowCh10)"/>
    <path class="flow" d="M460 125 H504" marker-end="url(#arrowCh10)"/>
    <path class="flow" d="M564 98 V66" marker-end="url(#arrowCh10)"/>
    <path class="flow" d="M504 39 H408" marker-end="url(#arrowCh10)"/>
    <path class="flow" d="M258 39 H72 V98" marker-end="url(#arrowCh10)"/>
  </g>
</svg>
<figcaption><strong>Figure 10.1</strong> - The continuous-eval loop: every production regression becomes a new permanent test case.</figcaption>
</figure>

## Monitoring quality, drift and regressions

Standard observability — latency, error rate, token spend (Chapter 9) — will not detect a quality collapse. Your p99 can be flat, your 5xx rate zero, your costs nominal, and your agent can still be silently giving worse answers. **Quality regressions are invisible to infrastructure metrics.**[^valuestream] You need metrics that measure the *content* of outputs, and you need to watch them for two distinct failure modes: drift and regression.

**Drift** is gradual and usually driven by the world changing around you. **Input drift** happens when the distribution of user prompts shifts away from what you optimized for — a support agent tuned on 2024 product questions now fielding questions about features shipped in 2026.[^galileo-drift] **Output drift** and **embedding drift** happen when your responses slowly wander in tone, length, or semantic content even though no single day looks anomalous. Embedding-based drift detection — clustering the vector representations of inputs and outputs and watching the centroids move — is the standard technique, and tools like **Arize Phoenix** ship it built in alongside RAG retrieval-quality evaluation.[^phoenix]

**Regression** is sudden. A prompt change, a retrieval-index rebuild, a dependency bump, or — the one you don't control — a provider updating a model underneath you. Regressions show up as a step-change in your quality metric, and the whole point of continuous evals is to make that step visible within minutes, not weeks.

The metrics worth alerting on, in rough priority order:

- **Task-success / resolution rate** — your north-star quality metric, scored by judge or inferred from downstream signal (did the ticket reopen?).
- **Faithfulness / groundedness** — fraction of claims supported by retrieved context; the leading indicator for hallucination.
- **Judge-score distribution**, not just the mean — a bimodal split where 20% of answers crater while the average holds is invisible if you only watch averages.
- **Retrieval quality** — recall and precision of the RAG step, since most "the model got worse" incidents are actually "retrieval got worse" (see Chapter 3).
- **Refusal and escalation rate** — a spike means the model is punting; a collapse means it stopped escalating things it should.

Set alert thresholds on rolling windows, not single traces — a 15-minute or 100-trace window smooths noise while still catching a genuine step-change fast. **Braintrust**, which raised an $80M Series B at an $800M valuation in February 2026, gates on exactly this in CI and in production, blocking deploys on score regression and alerting on live drops.[^braintrust] The build-vs-buy calculus mirrors Chapter 9: roll your own on Langfuse or Phoenix if you have the engineering bandwidth and want the data in your warehouse; buy Braintrust, Arize AX, or Galileo if you want the judge orchestration, dashboards, and CI gates out of the box.

{case: **Braintrust's Loop (2026)** - Braintrust's *Loop* agent turns the feedback loop into a product: it generates eval datasets, recommends scorers, and — the load-bearing feature — converts a flagged production failure into a permanent eval case in one click. This collapses the "closing the loop" step of Figure 10.1 from a data-engineering chore into a button, which is why the pattern has spread across the category.}

For Cortex, the metric that matters is resolution quality, and the team watches its **p10 on a rolling 100-ticket window**. Average resolution quality is a vanity number for them; a healthy agent that suddenly fails hard on a slice of tickets is the disaster scenario, and only the tail exposes it.

:::warning
If you only monitor averages, you are blind to the most dangerous failure mode: a model update or prompt change that catastrophically breaks a *subset* of inputs while leaving the aggregate untouched. Segment by cohort, intent, and customer tier, and alert on the tail.
:::

## Guardrails and hallucination detection in production

Evals tell you, after the fact, that quality dropped. **Guardrails** act *in the request path*, in real time, to stop a bad output before the user sees it. They are complementary: evals are your smoke detector, guardrails are your circuit breaker. Do not confuse the two — a guardrail that blocks toxic output does nothing to tell you your resolution quality is sliding, and a monitoring dashboard has never once prevented a hallucinated refund policy from reaching a customer.

A production guardrail stack in 2026 is layered, and the canonical architecture has roughly six stages: **input validation, prompt hardening, retrieval/RAG-rail filtering, output filtering (including hallucination detection), tool-call execution gating, and a managed moderation API.**[^digitalapplied] The two open-source anchors are **NVIDIA NeMo Guardrails**, which uses a DSL called Colang to define dialog and agentic rails across five pipeline stages and hits sub-100ms latency, and **Guardrails AI**, whose Hub had roughly 70 composable validators as of May 2026 spanning factuality, PII, safety, and brand risk.[^nemo][^digitalapplied] The emerging consensus treats them as complementary — NeMo for dialog and agentic rails, Guardrails AI for composable output validation.

The critical design constraint is **latency**. A guardrail sits in the synchronous request path, so a slow validator is a slow product. This is why the 2026 shift is toward **small, purpose-built models** for real-time checks: Galileo's **Luna-2** small language models detect hallucinations, prompt injection, PII, toxicity and bias in real time at a claimed 98% lower cost than LLM-based evaluation while hitting a 0.95 F1 score.[^galileo-guardrails] A frontier model as your inline hallucination check is too slow and too expensive; a distilled SLM is fast enough to run on every request.

### Hallucination detection that actually works

The most reliable production technique is not "ask a big model if this is true" — it's **grounding verification**. For any RAG or tool-using system, decompose the output into atomic claims and check each against the retrieved context. If a claim isn't supported by a source, it's a candidate hallucination, and you either suppress it, regenerate, or escalate. NeMo's fact-checking and retrieval rails do this against a knowledge base; you can also build it as a distilled scorer.[^nemo] This groundedness check is the same faithfulness metric you monitor in evals — the difference is you're now running it inline and blocking on it, not sampling and dashboarding it.

The newest pattern, pioneered by Galileo, dissolves the boundary between evals and guardrails entirely: **pre-production evaluations automatically become production guardrails**, where eval scores gate agent actions, tool access, and escalation at runtime.[^getmaxim] The rubric you validate offline becomes the runtime policy. This is where the two halves of this chapter converge.

{case: **Guardrails AI Hub at ~70 validators (May 2026)** - Guardrails AI's *Guard* wrapper orchestrates composable validators pulled from a Hub that reached roughly 70 validators by mid-2026, letting teams stack factuality, PII-leak, and brand-risk checks declaratively rather than hand-coding each one. The composability matters: guardrails are not one model but a pipeline you tune per output type.}

Cortex runs a tight inline stack. Before any reply leaves the agent, a Luna-class SLM verifies groundedness against the retrieved help-center docs, a PII filter scrubs anything that looks like a leaked customer record, and a **tool-call gate** blocks the agent from issuing a refund above a per-customer threshold without human sign-off — the last one being a guardrail against *action*, not just *text*, which is the category most founders forget until an agent does something expensive.

:::definition
**Guardrail vs. eval.** A *guardrail* runs synchronously in the request path and can block, rewrite, or escalate a single output before the user sees it. An *eval* runs asynchronously on sampled traffic and measures aggregate quality over time. You need both; neither substitutes for the other.
:::

## Surviving provider and model updates

Here is the industry's dirtiest open secret, and the reason continuous evals are non-negotiable for an AI startup: **the model behind your API call can change without you doing anything.** Even when you pin a version, the platform-level system prompt, safety layer, and routing evolve independently — two calls to the same pinned model on different days can behave differently because of what surrounds the model, not the weights themselves.[^silent] This is the *silent versioning problem*, and it is structural, not a bug.

The 2026 deprecation calendar makes the hard version of this concrete. Anthropic **retired the entire Claude 4.0 lineage on June 15, 2026** — calls to those snapshots now return an error — and the same Claude Sonnet 4 that was retired on the first-party API on that date carries a *different* end-of-life of October 14, 2026 on Amazon Bedrock.[^anthropic-dep][^lifecycle] OpenAI notified older GPT-5 and o3 snapshots for removal on December 11, 2026.[^openai-dep] Meanwhile the frontier keeps moving: **Claude Opus 4.8** launched May 28, 2026 at $5/$25 per million input/output tokens, Sonnet 4.6 at $3/$15, Haiku 4.5 at $1/$5, against OpenAI's GPT-5.4 at $2.50/$15.[^anthropic-price] Every one of those numbers is a migration you will eventually be forced to make.

There are three distinct threats, and they need three distinct defenses:

| Threat | What happens | Defense |
|---|---|---|
| **Hard deprecation** | Pinned model returns an error on a known date | Track the deprecation calendar; pre-migrate and eval the successor weeks early |
| **Silent regression** | Same model ID, different behavior day-to-day | Continuous evals with a constant sample; alert on the step-change |
| **Forced upgrade** | Provider sunsets your version; you must move | A/B the new model against your golden set before cutover; keep a rollback path |

The defenses compound. **Pin every model version explicitly** — never call a floating alias like `latest` in production, because that hands the provider a live edit button on your product. **Maintain a model-migration runbook** and treat every provider version bump as a deploy that must pass your full offline eval suite before it ships (see Chapter 6 for the suite). And keep the abstraction layer from Chapter 7 thin enough that swapping providers is a config change, not a rewrite — multi-provider optionality is your leverage when a single vendor's roadmap diverges from your needs.

But pinning is necessary, not sufficient: the version string can lie. The only defense against a regression on a pinned model is the sensor — a continuous eval on a constant sample against a stable rubric, so that when behavior shifts, your metric shifts within minutes.

{case: **The Opus "nerf" complaints (2026)** - In mid-2026 a widely-shared GitHub thread accused Anthropic of quietly degrading Opus performance on complex engineering work — the archetypal *silent regression* dispute. Whether or not weights changed, the episode's lesson is unambiguous: teams *without* their own continuous evals had only vibes and forum threads as evidence, while teams *with* them had a dated quality-score chart. Own your own measurement or you are arguing about feelings.}

**This is the Cortex moment the whole chapter has been building toward.** On a Tuesday afternoon, Cortex's upstream provider silently updated the model behind Cortex's pinned tier — same version string, changed behavior. Within roughly three hours, the rolling p10 on resolution quality dropped from 4.1 to 2.8 on the 5-point rubric; the 15-minute LLM-as-judge sample caught it long before support tickets started reopening at scale. Infrastructure metrics were pristine the entire time — latency flat, error rate zero, spend nominal. The only thing that fired was the continuous eval. The on-call engineer rolled traffic to the fallback provider through the Chapter 7 abstraction layer, and the incident stayed a footnote instead of a headline. **The next chapter's crisis is what happens to the startup that shipped Cortex's exact architecture *without* this sensor** (see Chapter 15) — same provider update, no early warning, discovered three weeks later through churn.

:::rule
Never call a floating model alias in production. Pin the version, and then distrust the pin — the version string is a promise the provider can silently break, so run a continuous eval as your ground truth.
:::

## Closing the loop: production signals into the eval set

A continuous-eval system that only alerts is a system that decays. Every regression it catches, every hallucination a guardrail blocks, every ticket a human overturns is a **new test case your offline suite was missing** — and the discipline that separates teams whose quality compounds from teams who fight the same fire twice is feeding those failures back in. This is the arrow in Figure 10.1 that returns to the eval set, and it is the mechanism that turns your Chapter 5 data flywheel into a *quality* flywheel.

The loop has four steps, and each needs an owner:

1. **Capture.** Every flagged production failure — low judge score, guardrail block, human override, customer thumbs-down — lands in a triage queue with its full trace (Chapter 9).
2. **Curate.** A human confirms it's a real failure (not a judge miscalibration), assigns the correct label, and writes the expected output. This is where your **golden dataset** grows, and where you also catch your judge drifting.
3. **Promote.** The curated case joins the offline eval set, so the next prompt or model change is tested against a failure that actually happened in your product, not a hypothetical.
4. **Regress-guard.** The new case now blocks any deploy that would reintroduce the failure — a permanent ratchet against backsliding.

{sn: Weight your golden set toward *observed* failures, not imagined ones. A hundred real production failures your users actually hit is worth more than a thousand synthetic edge cases you dreamed up in a planning meeting. The distribution of your test set should track the distribution of your risk.}

Tooling has made this nearly frictionless — Braintrust's Loop converts a production failure into an eval case in one click, and the same one-click promotion is now table stakes across Langfuse, Galileo and Arize.[^braintrust] But the tool is the easy part; the hard part is the **human curation discipline**, because a golden set polluted with mislabeled cases silently corrupts every downstream decision. Budget real SME time for step 2. And watch your judge: the same production samples that grow your eval set are the data you use to re-check that your LLM-as-judge still agrees with human labels, because a judge that has drifted is a broken instrument reporting confident nonsense (judge calibration is designed in Chapter 6; here you *maintain* it).

For Cortex, the Tuesday regression became case #4,417 in the golden set that same week: the exact prompts that scored 2.8, paired with the correct high-quality resolutions, now permanently gate every deploy. The provider can update the model again — and it will — but this specific failure can never silently return without turning the CI suite red. That is what a closed loop buys you: **every incident makes the system permanently harder to break in the same way twice.**

:::takeaways
**Key takeaways**
- Pre-launch evals are a photograph; production needs a continuously running video. The loop is: traffic → sample → auto-score → alert → feed back into the eval set.
- Tier evaluation by cost and coverage: deterministic and distilled scorers on 100% of traffic, a frontier LLM-as-judge on a small constant sample, humans on the anomalies.
- Infrastructure metrics cannot see quality collapse. Monitor task-success, faithfulness, and the *distribution* of judge scores — alert on the tail, not the mean.
- Guardrails act in real time to block bad outputs; evals measure quality over time. You need both, and small purpose-built models (e.g. Luna-2-class SLMs) make inline checks fast and cheap enough to run on every request.
- The model behind your pinned API call can change silently. Pin versions, track the deprecation calendar, keep a thin multi-provider abstraction — and run a continuous eval as ground truth because the version string can lie.
- Close the loop: every caught regression becomes a permanent eval case, turning your data flywheel into a quality ratchet.
:::

:::exercise
**Hands-on: Stand up a minimum-viable continuous-eval loop**
1. Pick your single north-star quality metric (e.g. resolution correctness) and write it as a 1–5 rubric — reuse your Chapter 6 eval rubric.
2. Instrument a **5% sample** of production traffic to run an LLM-as-judge scorer against that rubric on a 15-minute cadence, using a cheaper judge model to control cost (~$0.01–$0.10/trace).
3. Add **two free deterministic checks** on 100% of traffic: schema/format validation and a banned-phrase regex.
4. Plot the judge-score **p10 on a rolling 100-trace window** and set an alert on a step-change (e.g. p10 drops >0.8 points in one window).
5. Pin your model version explicitly and add a calendar reminder for your provider's next known deprecation date.
6. Build the one-click path: when a trace scores below threshold, promote it (with a human-written expected output) into your offline golden set so it gates the next deploy.
7. Simulate a regression — swap to a deliberately weaker model for ten minutes — and confirm the alert fires and the trace lands in your triage queue.
:::

[^langfuse]: LLM-as-a-Judge — Langfuse Documentation (per-assessment cost and production sampling). <https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge>
[^braintrust]: 8 best human-in-the-loop LLM evaluation platforms in 2026 — Braintrust (Series B, CI/CD gating, Loop agent). <https://www.braintrust.dev/articles/best-human-in-the-loop-llm-evaluation-platforms-2026>
[^valuestream]: AI Monitoring in Production 2026: LLM Observability & Drift Detection — ValueStream AI. <https://valuestreamai.com/blog/ai-monitoring-in-production-guide-2026>
[^galileo-drift]: 9 Best LLM Drift Monitoring Platforms in 2026 — Galileo (input, output, and embedding drift). <https://galileo.ai/blog/best-llm-output-drift-monitoring-platforms>
[^phoenix]: Fiddler AI vs Arize Phoenix (2026) — embedding drift visualization and hallucination detection. <https://aisecurityandsafety.org/en/compare/fiddler-ai-tool-vs-arize-phoenix/>
[^digitalapplied]: LLM Guardrails: Production Safety Layers Reference 2026 — Digital Applied (six-layer architecture; Guardrails AI Hub). <https://www.digitalapplied.com/blog/llm-guardrails-production-safety-layers-reference-2026>
[^nemo]: NeMo Guardrails 2026: NVIDIA's LLM Safety Toolkit (Colang, sub-100ms, fact-checking and retrieval rails). <https://appsecsanta.com/nemo-guardrails>
[^galileo-guardrails]: 5 Best AI Guardrails Platforms Compared in 2026 — Galileo (Luna-2 SLMs, 98% cost reduction, 0.95 F1). <https://galileo.ai/blog/best-ai-guardrails-platforms>
[^getmaxim]: Top 5 LLM Evaluation Platforms in 2026 — Maxim AI (evals-become-guardrails pattern). <https://www.getmaxim.ai/articles/top-5-llm-evaluation-platforms-in-2026/>
[^silent]: The Silent Versioning Problem in AI Inference — DigitalOcean. <https://www.digitalocean.com/community/tutorials/model-silent-versioning-problem>
[^anthropic-dep]: Model deprecations — Claude Platform Docs (Claude 4 retirement, June 15, 2026). <https://platform.claude.com/docs/en/about-claude/model-deprecations>
[^lifecycle]: AI Model Deprecation and Lifecycle Calendar — Anthropic, OpenAI, Google, Amazon Bedrock. <https://hidekazu-konishi.com/entry/ai_model_deprecation_and_lifecycle_calendar.html>
[^openai-dep]: Deprecations — OpenAI API (GPT-5/o3 snapshot removal, December 11, 2026). <https://developers.openai.com/api/docs/deprecations>
[^anthropic-price]: Claude Opus 4.8: Pricing, benchmarks, and which model to run in 2026 — CloudZero. <https://www.cloudzero.com/blog/claude-opus-4-8-pricing/>