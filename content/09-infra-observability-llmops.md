---
part: Part III - The Stack
part_num: III
chapter_num: 9
title: Infrastructure, Observability & LLMOps
dek: Running models like a grown-up — deploys, versioning, tracing, and the on-call that AI demands.
slug: 09-infra-observability-llmops
reading_time: 20 min read
---

The first time Cortex silently regressed, no test failed and no alarm fired. A one-word edit to a system prompt — "concise" swapped for "brief" — dropped ticket-resolution quality by nine points across a single mid-market tenant, and it took nineteen hours and an angry Slack from the customer before anyone noticed. Nothing was down. Everything was worse. That gap between "up" and "correct" is the entire discipline of this chapter, and it is why an AI startup cannot run on the DevOps playbook alone.

## LLMOps vs MLOps vs DevOps

Every generation of software operations inherited the last one's tools and then found a failure mode the old tools were blind to. **DevOps** made deploys fast, reversible, and observable, but it assumed the code you shipped was the code that ran: deterministic, testable with assertions, green or red. **MLOps** added the model as a versioned artifact — training pipelines, feature stores, drift detection — because a model's behavior lives in weights, not source, and weights rot as the world shifts underneath them.[^mlops] **LLMOps** is the third layer, and it exists because the thing you operate is neither your code nor your model: it is a **prompt-plus-context-plus-frontier-API** system whose most important component you did not train, cannot inspect, and do not control.[^llmops]

{sn: The uncomfortable truth of LLMOps is that your core dependency ships a new version on its own schedule, deprecates the old one, and never guarantees the numbers stay the same. You are operating someone else's model in production.}

Three properties break the inherited playbook. First, **non-determinism**: the same input yields different outputs, so `assertEqual` is useless and "correctness" is a distribution, not a boolean.[^nondeterm] Second, **cost is per-token and unbounded at request time**: a single malformed prompt or a runaway agent loop can 10x a bill in an afternoon, so spend is a first-class runtime signal, not a monthly finance report.[^cost] Third, **the model is exogenous**: providers deprecate `gpt-5.2`, silently re-tune a safety filter, or degrade under load, and your quality moves without a single line of your code changing. DevOps has nothing to say about any of these. LLMOps is the practice of making a non-deterministic, metered, externally-controlled system behave like production infrastructure anyway.

| Concern | DevOps | MLOps | LLMOps |
|---|---|---|---|
| Primary artifact | Code | Trained model + data | Prompt, config, context, tool defs |
| Versioned unit | Git commit | Model + dataset hash | Prompt version + model pin + params |
| Correctness | Deterministic tests | Offline metrics (AUC, F1) | Eval distributions, LLM-as-judge (Ch 10) |
| Failure mode | Crash, 500 | Drift, stale features | Silent quality regression, hallucination |
| Runtime cost | ~Fixed per box | Batch/GPU training cost | Per-token, per-request, unbounded |
| Rollback | Redeploy prior build | Repromote prior model | Re-pin prompt + model version instantly |
| Core dependency | Yours | Yours | **Someone else's frontier model** |

:::rule
Treat the prompt as production code and the model as a third-party dependency you can neither test nor trust. Version both, pin both, and monitor the boundary between them.
:::

The founder mistake is assuming LLMOps is a tool you buy. It is a discipline spanning four surfaces — versioning, observability, the caching/routing gateway, and reliability engineering — and the rest of this chapter is those four surfaces. For the model-routing *strategy* (which model for which job, buy-vs-host) see Chapter 7; for the eval *metrics* that decide whether a change is better see Chapter 10; for unit economics see Chapter 13. This chapter owns the plumbing.

## Prompt and config versioning and deploys

A prompt is code. It has inputs, control flow (few-shot examples, conditionals baked into templates), a runtime contract with the model, and it breaks silently when edited. Yet the default failure of early-stage AI teams is to treat prompts as content — a string edited in a dashboard, a Notion doc pasted into a config, a value someone changed on a Friday. Cortex's nineteen-hour regression was exactly this: an untracked, unversioned, un-evaluated edit to production behavior. The fix is **prompt CI/CD**: every prompt change is versioned, evaluated against a fixed dataset, gated on quality, and rolled out progressively — the same lifecycle as a code deploy.[^promptcicd]

{sn: The versioned unit is never the prompt alone. It is the *tuple*: prompt text + model id (`claude-opus-4-6`, not `claude-opus`) + temperature + tool schema + max tokens. Change any element and behavior can move. Pin all of them together or you have versioned nothing.}

Two architectures exist, and you will use both. **Prompts-in-Git** stores prompt templates as files (YAML or plain text) in your repo, syncs them to a registry, and pins versions in production for reproducible builds — LangWatch's Prompts CLI and PromptHub's Git-style branch/commit/merge model are built for this.[^langwatch][^prompthub] **Prompts-in-registry** stores them in a managed system (Langfuse, Braintrust) that non-engineers edit through a UI, with the runtime fetching by label (`production`, `staging`) at call time.[^langfuse] Git gives you review, blame, and atomic rollback tied to code; the registry gives you fast iteration without a deploy and lets a support lead fix a prompt at 2 a.m. The right answer for most startups: **author in Git, deploy through a registry**, treating the registry as a cache of what Git already reviewed.

The non-negotiable is the **quality gate**. When a prompt changes, an automated eval runs against a golden dataset and reports which cases improved and which regressed; the merge blocks if quality falls below threshold.[^promptcicd] Langfuse emits a `repository_dispatch` event (or a signed webhook) on every prompt version change, triggering your CI to run that eval before the new version is allowed to carry the `production` label.[^langfusecicd] This is the wall that would have stopped Cortex's "concise → brief" edit.

{case: **Langfuse 4** - In 2026 Langfuse shipped OpenTelemetry-native tracing and formalized a prompt CI/CD flow where a `production` label is applied only after a webhook-triggered eval passes, making "promote the prompt" a gated pipeline step rather than a dropdown change. See [langfuse.com](https://langfuse.com/resources/engineering/prompt-cicd).}

Deploy the same way you deploy code: **canary** a new prompt version to a small traffic slice, watch the eval and cost signals, then widen; **A/B** two versions live when you are choosing between them; keep the prior version one label-flip away for instant rollback.[^launchdarkly] Cortex now ships prompts like code: each version is a Git-reviewed YAML file with a pinned model and params, promoted through staging → 5% canary → 100% only after the golden-set eval clears, and any tenant can be pinned to a known-good version if their traffic regresses. The nineteen-hour incident is now a five-minute label revert.

:::warning
"Config" is not safe just because it lives outside your prompt. Temperature, `max_tokens`, tool JSON schemas, retrieval `top_k`, and the model id are all behavior. A team that versions prompts but lets an engineer bump temperature from 0.2 to 0.7 in an env var has an unversioned production change waiting to happen.
:::

## Observability: tracing, logs, token and cost metrics

You cannot debug what you cannot see, and an LLM request is nearly opaque by default: a string goes in, a string comes out, and everything that determined quality — which prompt version, which retrieved chunks, which tool calls, how many tokens, at what cost, in how many milliseconds — is invisible unless you instrument it. The unit of observability is the **trace**: a tree of spans covering the full request path, where each span carries the model, token counts, latency, and cost of one operation.[^tracing] For an agent like Cortex a single ticket is one trace with a dozen child spans — retrieve knowledge-base docs, call the LLM to plan, invoke the refund tool, call the LLM again to draft the reply — and the trace is the only way to answer "why was this answer wrong and this one expensive."

The 2026 standard that makes this portable is the **OpenTelemetry GenAI semantic conventions**. The GenAI SIG defined a common vocabulary of `gen_ai.*` attributes — model name, input/output token counts, finish reason, tool calls — so a span from a LangGraph agent looks identical to one from a raw Anthropic call. OpenTelemetry's CNCF graduation in May 2026, plus OTLP ingestion across vendors like Datadog and Grafana, made it the default wire format rather than a niche choice.[^otelgenai][^otelgrad] Most conventions are still experimental, but they are stable enough to build on, and standardizing here means you can swap observability backends without re-instrumenting your code. Instrument with an open standard — OpenLLMetry or OpenLIT emit OTel spans into whatever backend you already run — and you are not locked to one vendor's SDK.[^openllmetry]

{sn: Emit OTel GenAI spans, not vendor-proprietary events. The instrumentation is the expensive, invasive part; the backend is a commodity. Own the former, rent the latter, and keep the freedom to move.}

<figure class="diagram">
<svg viewBox="0 0 720 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The LLMOps request path from gateway through cache and router to providers, with tracing and evals branching off">
  <style>.dg text{font-family:var(--sans);fill:var(--ink);font-size:13px} .dg .box{fill:var(--paper-2);stroke:var(--rule-2)} .dg .accent{fill:var(--accent-bg);stroke:var(--accent)} .dg .rec{fill:var(--sage-bg);stroke:var(--sage)} .dg .lbl{fill:var(--muted);font-size:11px;font-weight:600} .dg .flow{stroke:var(--rule-2);stroke-width:1.6;fill:none}</style>
  <defs><marker id="arrowCh9" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--rule-2)"/></marker></defs>
  <g class="dg">
    <rect class="accent" x="8" y="52" width="96" height="44" rx="9"/>
    <text x="56" y="79" text-anchor="middle">Gateway</text>
    <rect class="box" x="140" y="52" width="96" height="44" rx="9"/>
    <text x="188" y="72" text-anchor="middle">Cache</text>
    <text class="lbl" x="188" y="88" text-anchor="middle">exact + semantic</text>
    <rect class="box" x="272" y="52" width="96" height="44" rx="9"/>
    <text x="320" y="72" text-anchor="middle">Router</text>
    <text class="lbl" x="320" y="88" text-anchor="middle">+ fallback</text>
    <rect class="box" x="404" y="24" width="120" height="40" rx="9"/>
    <text x="464" y="49" text-anchor="middle">Provider A</text>
    <rect class="box" x="404" y="84" width="120" height="40" rx="9"/>
    <text x="464" y="109" text-anchor="middle">Provider B</text>
    <rect class="rec" x="272" y="176" width="130" height="44" rx="9"/>
    <text x="337" y="203" text-anchor="middle">Tracing / obs</text>
    <rect class="rec" x="440" y="176" width="120" height="44" rx="9"/>
    <text x="500" y="203" text-anchor="middle">Evals (Ch 10)</text>
    <path class="flow" d="M104 74 H140" marker-end="url(#arrowCh9)"/>
    <path class="flow" d="M236 74 H272" marker-end="url(#arrowCh9)"/>
    <path class="flow" d="M368 66 L404 48" marker-end="url(#arrowCh9)"/>
    <path class="flow" d="M368 82 L404 100" marker-end="url(#arrowCh9)"/>
    <path class="flow" d="M56 96 V198 H272" marker-end="url(#arrowCh9)"/>
    <path class="flow" d="M402 198 H440" marker-end="url(#arrowCh9)"/>
    <text class="lbl" x="120" y="150" text-anchor="middle">every span emitted as OTel gen_ai.*</text>
  </g>
</svg>
<figcaption><strong>Figure 9.1</strong> - The LLMOps request path: one gateway fronts cache, router, and providers, and every hop emits a traced span into observability and evals.</figcaption>
</figure>

Three signals matter above all. **Traces** for debugging causality. **Token metrics** — input, output, and cached tokens per span — because tokens are the currency of both cost and latency. And **cost**, computed from tokens times the per-model rate and attributed down to per-user, per-tenant, and per-feature.[^costtrack] A production LLMOps dashboard shows total spend and calls, cost over time, cost by model, cost by operation, average cost per call, and cost per user — the last of which catches the one tenant whose usage pattern is quietly eating your margin.[^dashboard] Cortex dashboards cost per resolved ticket per tenant and pings sales when a tenant's number crosses its plan price; the profitability math itself is Chapter 13's.

:::definition
**Span** — one timed, attributed operation inside a trace (an LLM call, a tool invocation, a retrieval). **Trace** — the full tree of spans for one end-to-end request. In OTel GenAI conventions, each LLM span carries `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, and `gen_ai.response.finish_reason` as standard attributes.
:::

## Caching, routing and fallbacks in production

Between your application and the frontier providers belongs exactly one component: an **LLM gateway**. It puts a single OpenAI-compatible endpoint in front of many providers and centralizes caching, routing, fallback, spend limits, and observability, so those concerns live in one governed place instead of being reimplemented in every service.[^gateway] Building these piecemeal across your codebase is the most common infrastructure mistake an AI startup makes; the gateway is the correction.

**Caching** is the highest-leverage cost lever you own, and there are two kinds. *Provider prompt caching* discounts the repeated prefix of a request — a large system prompt, a fixed knowledge base — and in 2026 the economics are dramatic: Anthropic charges 1.25x base input for a 5-minute cache write and just **0.10x for every cache read, a 90% discount**, with OpenAI's automatic caching matching that 90% read discount on its newest flagships.[^anthropiccache][^cachecompare] For an agent like Cortex, whose every call carries the same multi-thousand-token support playbook and tenant context, structuring the prompt so stable content sits in the cacheable prefix is the difference between viable and ruinous margins. *Gateway caching* adds **exact-match** caching (identical request → stored response) and **semantic caching** (a fuzzy-matched, near-identical prompt served from cache) — Portkey and Cloudflare AI Gateway have the most mature implementations, while LiteLLM notably does not do semantic caching.[^cachecompare][^litellm]

:::warning
Semantic caching trades correctness for cost. Two prompts that embed as "similar" are not always answer-equivalent — "cancel my subscription" and "pause my subscription" sit close in vector space and want opposite actions. Never semantically cache anything that triggers a side-effecting tool call. For Cortex, informational answers are cacheable; refunds and cancellations never are.
:::

**Routing** decides which provider serves each request — by price, latency, throughput, or capability — and **fallback** decides what happens when the first choice fails. The strategy is Chapter 7's territory; the *mechanism* is the gateway's, and it is what turns provider fragility into a non-event. Configure an ordered fallback chain (primary model → same model on a second provider → a different model family) with a tight health-detection window and idempotency keys to avoid double-charging on retries.[^failover] The arithmetic is compelling: two providers each at 99.53% availability, combined with automatic failover, reach above 99.99% — cutting expected downtime from roughly 41 hours a year to about 12 minutes.[^failover]

| Gateway | License | Semantic cache | Fallback/routing | Prompt mgmt | Best when |
|---|---|---|---|---|---|
| **Portkey** | Apache 2.0 (open-sourced Mar 2026) | Yes (fuzzy) | Conditional, fine-grained | Yes, versioned | You need production governance + guardrails |
| **LiteLLM** | Open source (self-host) | No | Yes | Basic | You want to own the proxy on your infra |
| **OpenRouter** | Managed SaaS | No | Load-balance, price/latency sort | No | Fast access to 400+ models, one key |
| **Cloudflare AI Gateway** | Managed SaaS | Yes (edge) | Yes | No | You are already on Cloudflare's edge |

{case: **Portkey open-sources the gateway** - In March 2026 Portkey released its full production gateway under Apache 2.0, and by May 2026 it was the most feature-complete open-source option — 1,600+ models across 250+ providers, semantic caching, guardrails (PII redaction, jailbreak and prompt-injection filters), and versioned prompt management in one self-hostable proxy. See [wavect.io](https://wavect.io/blog/llm-gateway-router-comparison-2026/).}

Cortex fronts everything with a self-hosted gateway: exact + semantic cache on informational queries, provider prompt caching on the fixed playbook prefix, and a fallback chain that fails over between Anthropic and a second provider on a 5–15 second health signal, with idempotency keys so a mid-flight retry never issues a refund twice.

## Reliability, rate limits and incident readiness

AI is now infrastructure, and it fails like infrastructure — except the failures are stranger. 2026 made this concrete: on June 2, Anthropic's Claude had a major global disruption with elevated error rates across Opus 4.6, the API, and Claude Code; in the nine months to July 2026 OpenAI logged roughly 166 incidents, averaging about 18 a month, with four outages inside a single four-day window in July.[^claudeoutage][^openaioutage] If your product's core loop runs through one provider's API, your uptime is capped by theirs, and theirs is not 99.99%. The multi-provider failover of the previous section is not a nice-to-have; it is the only way to offer an SLA you can keep.

{sn: The June 2026 Claude outage is the industry's "AWS us-east-1" moment for AI — the day a critical mass of companies discovered that a single provider's incident was now *their* incident, with no failover in place. Do not learn this lesson in production.}

**Rate limits** are the failure you will hit first and most often. Providers meter you across usage tiers that rise with spend, and a traffic spike or a retry storm will hit `429` long before an actual outage.[^ratelimits] Handle them at the gateway: exponential backoff with jitter, a token-bucket limiter you enforce yourself so you throttle gracefully instead of hammering a limit, request queuing for non-interactive work, and load-balancing across multiple provider accounts or regions to widen your effective ceiling. Naive retry-on-`429` without backoff makes the incident worse — you DDoS your own provider relationship.

:::warning
The lazy retry loop — "on error, try again immediately" — is an outage amplifier. Under a partial provider degradation it converts one slow request into a retry storm that exhausts your rate limit and takes down the requests that would have succeeded. Always jittered backoff, always a retry budget, always a circuit breaker that fails over rather than hammering.
:::

Then there is the failure mode unique to AI: **the model is up but wrong**. Latency crept up, a provider silently swapped a model revision, a prompt regressed, hallucination rate climbed — none of it trips a `500`. This is why the three alerts every LLM team needs by tomorrow are not the classic ones: alert on **cost-per-request spiking** (a runaway agent loop or a prompt-injection attack), on **latency-per-token degrading** (provider trouble before it becomes an outage), and on **quality/eval score dropping** on live traffic (the silent regression).[^alerts] Standard APM watches for down; LLMOps must also watch for *worse*.

Be sober about putting an LLM in your own on-call loop. Many 2026 reliability teams wired a model into triage and alert summarization, but research shows most frontier models degrade significantly within roughly 1,000 tokens of input — long before their advertised context limit — so a model asked to reason over a fat incident dump is wrong more often than teams assume.[^oncall] Use LLMs to summarize and suggest in your incident response; keep a human on the decision.

{case: **The four-day July 2026 OpenAI cluster** - Four significant OpenAI outages landed inside a single four-day window in July 2026, part of ~166 incidents over nine months. Teams with a configured fallback chain rode them out as elevated latency; single-provider teams took the full downtime. See [thenextweb.com](https://thenextweb.com/news/openai-outage-chatgpt-codex-api-july-2026).}

Incident readiness for an AI product means a runbook that assumes provider failure as a *when*, not an *if*: documented failover you have actually rehearsed (a fire drill that forces traffic to the secondary), a per-tenant kill switch to pin or disable a misbehaving prompt version, cached and degraded-mode responses for when everything upstream is down, and a status page that distinguishes "down" from "degraded." Cortex's runbook does all four; when Anthropic degraded on June 2, Cortex's traffic shifted to its secondary provider inside the health-check window and customers saw slower replies, not silence. Full crisis management — comms, postmortems, customer trust — is Chapter 15's subject; the *engineering* readiness is yours to build before the crisis, not during it.

:::rule
Design for the provider outage you will definitely have, not the uptime the provider promises. If a single API's bad day is your bad day, you have not built infrastructure — you have built a dependency with extra steps.
:::

:::takeaways
**Key takeaways**
- LLMOps is a distinct discipline because the system is non-deterministic, metered per token, and built on a model you do not control — DevOps and MLOps tooling is necessary but not sufficient.
- The versioned unit is the tuple of prompt + model id + params + tool schema; run prompt CI/CD with golden-set quality gates, canary rollout, and instant label rollback.
- Instrument with OpenTelemetry GenAI conventions so traces, token metrics, and per-user cost are portable across backends; own the instrumentation, rent the backend.
- One gateway fronts caching (provider prompt cache at 0.10x reads, plus exact and semantic), routing, and fallback — never reimplement these per service, and never semantic-cache a side-effecting call.
- Multi-provider failover turns two ~99.5% providers into 99.99%; alert on cost, latency-per-token, and eval score — the failures that leave the API "up" but the product wrong.
:::

:::exercise
**Hands-on: Build your LLMOps spine in a weekend**
1. Put a gateway (Portkey self-hosted or LiteLLM) in front of every model call so one endpoint owns caching, routing, and fallback.
2. Move your top three prompts into version control as pinned tuples (text + model id + params), and wire a webhook so any change triggers a golden-set eval before it can carry the `production` label.
3. Instrument every call to emit OpenTelemetry `gen_ai.*` spans into one backend (Langfuse, or Grafana/Datadog via OpenLLMetry); confirm you can open a single request as a full trace.
4. Build a dashboard with cost-per-request and cost-per-tenant, and set the three alerts: cost spike, latency-per-token degradation, live eval-score drop.
5. Configure an ordered fallback chain across two providers with jittered backoff and idempotency keys, then run a fire drill — force-fail the primary and confirm traffic shifts inside your health-check window with no double-charged side effects.
:::

[^mlops]: Top LLM Observability Tools in 2026: A Pro Guide. MLflow. <https://mlflow.org/articles/top-llm-observability-tools-in-2026-a-pro-guide/>
[^llmops]: LLMOps Explained: The Complete 2026 Guide to LLM Operations. <https://zedtreeo.com/llmops-explained-guide-2026/>
[^nondeterm]: LLMOps vs MLOps: Complete 2026 Guide. Neil Dave. <https://theneildave.in/blog/llmops-vs-mlops.html>
[^cost]: Tracking LLM Operational Costs. APXML. <https://apxml.com/courses/mlops-for-large-models-llmops/chapter-5-llm-monitoring-observability-maintenance/tracking-llm-costs>
[^promptcicd]: Prompt CI/CD: version, gate, and roll out prompts like code. Langfuse. <https://langfuse.com/resources/engineering/prompt-cicd>
[^langwatch]: Prompt Management: Version & Deploy Prompts in Production. LangWatch. <https://langwatch.ai/blog/what-is-prompt-management-and-how-to-version-control-deploy-prompts-in-productions>
[^prompthub]: Best prompt management tools in 2026 (tested and compared). Braintrust. <https://www.braintrust.dev/articles/best-prompt-management-tools-2026>
[^langfuse]: What is prompt management? Versioning, collaboration, and deployment for prompts. Braintrust. <https://www.braintrust.dev/articles/what-is-prompt-management>
[^langfusecicd]: Prompt CI/CD: version, gate, and roll out prompts like code. Langfuse. <https://langfuse.com/resources/engineering/prompt-cicd>
[^launchdarkly]: Prompt Versioning & Management Guide for Building AI Features. LaunchDarkly. <https://launchdarkly.com/blog/prompt-versioning-and-management/>
[^tracing]: LLM Monitoring Best Practices: Complete Guide for 2026. OpenObserve. <https://openobserve.ai/blog/llm-monitoring-best-practices/>
[^otelgenai]: How OpenTelemetry Traces LLM Calls, Agent Reasoning, and MCP Tools. Greptime. <https://greptime.com/blogs/2026-05-09-opentelemetry-genai-semantic-conventions>
[^otelgrad]: Cloud Native Computing Foundation Announces OpenTelemetry's Graduation. CNCF. <https://www.cncf.io/announcements/2026/05/21/cloud-native-computing-foundation-announces-opentelemetrys-graduation-solidifying-status-as-the-de-facto-observability-standard/>
[^openllmetry]: OpenTelemetry for LLMs: Complete SRE Guide for 2026. OpenObserve. <https://openobserve.ai/blog/opentelemetry-for-llms/>
[^costtrack]: From Bills to Budgets: How to Track LLM Token Usage and Cost Per User. Traceloop. <https://www.traceloop.com/blog/from-bills-to-budgets-how-to-track-llm-token-usage-and-cost>
[^dashboard]: LLM Cost Monitoring with OpenObserve: Track Token Usage & Control AI Spend. OpenObserve. <https://openobserve.ai/blog/llm-cost-monitoring/>
[^gateway]: LLM Gateways Compared 2026: LiteLLM vs OpenRouter vs Portkey vs RouteLLM. Wavect. <https://wavect.io/blog/llm-gateway-router-comparison-2026/>
[^anthropiccache]: Anthropic API Pricing in 2026: Complete Guide — Models, Caching, Batch & Optimization. Finout. <https://www.finout.io/blog/anthropic-api-pricing>
[^cachecompare]: Prompt Caching in 2026: Anthropic, OpenAI, Azure Compared. Technspire. <https://technspire.com/en/blog/prompt-caching-2026-real-cost-wins>
[^litellm]: LLM Gateways Compared 2026: LiteLLM vs OpenRouter vs Portkey vs RouteLLM. Wavect. <https://wavect.io/blog/llm-gateway-router-comparison-2026/>
[^failover]: Best 5 AI Gateways for LLM Failover and Fallback in 2026. Future AGI. <https://futureagi.com/blog/best-ai-gateways-llm-failover-fallback-2026/>
[^claudeoutage]: Claude outage, June 2026: Reckoning with AI's increasing status as infrastructure. Thoughtworks. <https://www.thoughtworks.com/insights/blog/generative-ai/claude-outage-june-2026>
[^openaioutage]: OpenAI Outage: Reliability Concerns and 2026 Crisis. SynapNews. <https://www.synapnews.com/articles/openai-outage-reliability-concerns>
[^ratelimits]: Handling LLM API Failures: Rate Limits & Failover. MixRoute. <https://mixroute.ai/blog/handle-llm-api-failures/>
[^alerts]: Essential Observability: 3 Critical Alerts for LLM Systems. Dev|Journal. <https://earezki.com/ai-news/2026-04-26-the-3-alerts-every-llm-team-should-have-set-up-by-tomorrow/>
[^oncall]: Your on-call AI agent is wrong more than you think. Causely. <https://causely-blog.ghost.io/your-on-call-ai-agent-is-wrong-more-than-you-think/>