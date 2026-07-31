---
part: Part III - The Stack
part_num: III
chapter_num: 8
title: The Content & Data Stack
dek: The retrieval plumbing behind every good AI product — embeddings, vector stores, and the pipelines that keep them honest.
slug: 08-content-data-stack
reading_time: 20 min read
---

Your model is a commodity; your context is not. Two startups can call the same frontier model with the same prompt and ship products that feel a generation apart, and the difference is almost never the prompt — it is what got retrieved and stuffed into the window before generation began. This chapter is about that machinery: how you turn a messy corpus of documents into vectors, where you keep them, how you search them well, and how you stop the whole thing from silently rotting the day after you launch.

We assume you already know what RAG *is* and how the retrieved context lands in a prompt (see Chapter 3), which embedding provider you lean toward (see Chapter 7), and that the infrastructure to run all this is Chapter 9's problem. Here we go deep on the plumbing itself, and we do it through **Cortex**, our running example: an autonomous customer-support agent for mid-market SaaS companies. Cortex ingests each customer's help center, product docs, and historical support tickets, then answers live conversations. If its retrieval is wrong, it hallucinates a refund policy that does not exist — so for Cortex, the content stack is not a supporting system. It *is* the product.

## Embeddings and chunking done right

An embedding turns a span of text into a vector so that semantically similar spans land near each other. The **chunk** — the unit of text you embed and later retrieve — is the single most consequential design decision in the stack, and the one teams most often get wrong. One systematic 2026 analysis attributed roughly 80% of RAG failures to the ingestion and chunking layer rather than the LLM.[^prem] When retrieval fails, you are not debugging the model; you are debugging how you cut up your documents nine steps upstream.

The naive move — split every document into fixed 1,000-token blocks — destroys meaning at the boundaries and buries the signal. The 2026 production default is narrower and smarter: start with a recursive splitter at **400–512 tokens with 10–20% overlap**, respecting natural boundaries (headings, paragraphs, list items), and escalate to semantic or page-level chunking only when your retrieval evals (see Chapter 10) prove you need it.[^firecrawl] Two nuances matter. First, overlap is not free: a January 2026 study found it often provided *no measurable benefit* while inflating index size and cost, so treat it as a knob to test, not a default to trust.[^firecrawl] Second, there is a **context cliff** around 2,500 tokens where answer quality degrades as chunks get bigger — bigger is not safer.[^firecrawl]

{sn: The precision/context tension: small chunks retrieve precisely but starve the model of surrounding meaning; big chunks give context but dilute the vector so it matches everything and nothing. You cannot win both with one chunk size.}

The pattern that resolves the tension is **hierarchical (or parent-document) chunking**: embed small child chunks for precise matching, but return the larger parent section to the model for context. You find with a scalpel and feed with a ladle. This is now the most widely adopted production pattern.[^firecrawl] For Cortex, a child chunk is a single paragraph of a help article; the parent is the whole article section, so a hit on "how do I rotate my API key" retrieves the exact sentence but hands the model the full key-management section.

The highest-leverage upgrade to embeddings is **contextual retrieval**: before embedding each chunk, prepend a short, LLM-generated sentence situating it in its source document ("This chunk is from the *Billing* article, section *Refunds*, and describes the 30-day window"). Anthropic reported that contextual embeddings alone cut retrieval failures ~35%; pairing them with contextual BM25 (hybrid search, covered below) reaches ~49%; adding reranking reaches ~67%.[^anthropic] It costs one cheap LLM call per chunk at ingest time — trivially amortized against every future query.

::: definition
**Contextual retrieval** — Augmenting each chunk with document-level context (title, section, a one-line summary) *before* embedding, so the vector encodes not just the chunk's words but where it lives. The disambiguation happens at index time, once, instead of failing silently at query time, forever.
:::

On the embedding model itself — a Chapter 7 decision — two 2026 facts shape your chunking economics. **Matryoshka** representation lets one model emit 2048/1024/512/256-dimensional vectors from a single pass, so you can truncate to smaller dimensions and shrink storage without re-embedding.[^voyage] And **quantization** is dramatic: `voyage-3-large` at int8 precision and 512 dimensions scored ~8.6% higher than OpenAI's full 3,072-dim float32 vectors while using roughly one-twenty-fourth the storage.[^voyage] Binary quantization cuts storage a further 32× versus float32 at equal dimensions.[^cohere] The lesson: default to 768–1,024 dimensions, reach for quantization early, and never pay to store 3,072-dim float32 vectors unless an eval says you must.

## Choosing a vector database or store

The market has fragmented into good options, so the wrong-answer surface has shrunk — but the "defensible default" question is sharper than ever. Do not start by asking which vector database is best. Ask how many vectors you will have, whether you already run Postgres, and whether you need to filter retrieval by metadata (tenant, product, recency) — for a multi-tenant product like Cortex, that last one is non-negotiable.

::: rule
**The Founder's Rule of Vector Stores:** if you have fewer than a few million vectors and already run Postgres, the right vector database is Postgres. Adopt a dedicated store only when a metric — latency, recall, or scale — forces you to.
:::

For most workloads under a few million vectors, **pgvector** inside your existing Postgres is the strongest choice: embeddings, source documents, and metadata live in one database you query with ordinary SQL joins, and with the `pgvectorscale` extension it stays competitive with dedicated engines up to roughly 50–100M vectors.[^firecrawl_vdb] You avoid a second datastore, a second consistency model, and a second thing to back up. The moment you outgrow it is a *good* problem, and the migration is mechanical.

{case: **Turbopuffer's object-storage economics (2026)** - Object-storage-native engines like Turbopuffer and LanceDB decouple storage from compute, and for write-heavy or very large corpora they can be an order of magnitude cheaper than memory-resident engines. Turbopuffer's floor is about $64/month but sits under $10 for a million reads and writes at standard dimensions — attractive when a corpus is huge but query volume is spiky.}

| Store | Best fit | Hybrid search | Ops burden | 2026 economics |
|---|---|---|---|---|
| **pgvector** (+pgvectorscale) | <50–100M vectors, already on Postgres | Via extensions / SQL | Lowest (no new system) | Free; you pay for Postgres you already run[^firecrawl_vdb] |
| **Qdrant** | Latency-sensitive OSS, self-host | Native | Medium (Rust, self-host or cloud) | 1GB free tier; latency leader among OSS[^firecrawl_vdb] |
| **Pinecone** | Managed, don't-touch-infra teams | Native | Lowest managed | Usage-based, free tier; closed-source[^firecrawl_vdb] |
| **Weaviate** | Native hybrid + rich filtering | Native (built-in) | Medium | OSS + managed cloud[^firecrawl_vdb] |
| **Turbopuffer / LanceDB** | 100M+ or write-heavy, cost-sensitive | Native (Turbopuffer) | Medium | ~10× cheaper on object storage[^firecrawl_vdb] |
| **Milvus / Zilliz, Vespa** | 100M+ at scale, hybrid at scale | Native | Higher | Enterprise-grade scale[^firecrawl_vdb] |

The load-bearing column is **hybrid search** — Weaviate, Qdrant, Turbopuffer, and Elasticsearch support it natively.[^appscale] If your product hinges on retrieval quality (it does), pick a store whose hybrid support is native rather than bolted on, or accept that you will run a separate keyword index alongside your vectors. Cortex runs pgvector per-tenant in early stage — each customer's corpus is small, and Postgres row-level security gives clean tenant isolation for free — with a documented path to Turbopuffer once any single tenant crosses tens of millions of vectors.

## RAG architecture patterns in production

A demo RAG pipeline is `embed(query) → top-k → prompt`. A production one is a graph with an ingestion side and a serving side that share nothing but the index, and the diagram below is the spine every serious system converges on.

<figure class="diagram">
<svg viewBox="0 0 720 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Production RAG pipeline from ingestion through generation">
  <style>.dg text{font-family:var(--sans);fill:var(--ink);font-size:13px} .dg .box{fill:var(--paper-2);stroke:var(--rule-2)} .dg .accent{fill:var(--accent-bg);stroke:var(--accent)} .dg .rec{fill:var(--sage-bg);stroke:var(--sage)} .dg .lbl{fill:var(--muted);font-size:11px;font-weight:600} .dg .flow{stroke:var(--rule-2);stroke-width:1.6;fill:none}</style>
  <defs><marker id="ragArrow08" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="var(--rule-2)"/></marker></defs>
  <g class="dg">
    <text class="lbl" x="20" y="26">INGEST (offline, event-driven)</text>
    <rect class="box" x="20" y="36" width="120" height="42" rx="9"/><text x="80" y="62" text-anchor="middle">Ingest + chunk</text>
    <rect class="box" x="170" y="36" width="120" height="42" rx="9"/><text x="230" y="55" text-anchor="middle">Embed</text><text x="230" y="70" text-anchor="middle" class="lbl">+context</text>
    <rect class="accent" x="320" y="36" width="120" height="42" rx="9"/><text x="380" y="62" text-anchor="middle">Store (index)</text>
    <path class="flow" d="M140 57 H168" marker-end="url(#ragArrow08)"/>
    <path class="flow" d="M290 57 H318" marker-end="url(#ragArrow08)"/>
    <text class="lbl" x="20" y="132">SERVE (online, per query)</text>
    <rect class="box" x="20" y="142" width="120" height="42" rx="9"/><text x="80" y="168" text-anchor="middle">Retrieve (hybrid)</text>
    <rect class="rec" x="170" y="142" width="120" height="42" rx="9"/><text x="230" y="168" text-anchor="middle">Rerank</text>
    <rect class="box" x="320" y="142" width="120" height="42" rx="9"/><text x="380" y="168" text-anchor="middle">Generate</text>
    <rect class="box" x="470" y="142" width="130" height="42" rx="9"/><text x="535" y="161" text-anchor="middle">Answer +</text><text x="535" y="176" text-anchor="middle" class="lbl">citations</text>
    <path class="flow" d="M380 78 V142" marker-end="url(#ragArrow08)"/>
    <path class="flow" d="M140 163 H168" marker-end="url(#ragArrow08)"/>
    <path class="flow" d="M290 163 H318" marker-end="url(#ragArrow08)"/>
    <path class="flow" d="M440 163 H468" marker-end="url(#ragArrow08)"/>
  </g>
</svg>
<figcaption><strong>Figure 8.1</strong> - The production RAG spine: an event-driven ingest path and a per-query serve path, sharing only the index.</figcaption>
</figure>

Three patterns separate production from prototype. First, **retrieve more than you send.** Pull 50–100 candidates from hybrid retrieval, then let a reranker (below) cut to the 5–10 that actually enter the prompt. Cheap recall up front, expensive precision at the end. Second, **always return citations.** Every generated claim should carry the chunk ID it came from, both so users can verify and so you can trace failures back to a specific document. For Cortex, an answer without a citation to a help article is a bug, not a stylistic choice — it is how a support agent earns trust instead of confidently inventing policy. Third, **filter before you search, not after.** Push tenant, product-version, and recency filters into the vector query so you never rank a chunk you would have to discard — critical when tenant B must never see tenant A's tickets.

Beyond baseline retrieval, two patterns are worth knowing but not defaulting to. **Query rewriting** — having a cheap model rephrase or decompose the user's question before retrieval — reliably helps on conversational and multi-part queries; Cortex uses it to turn "it's still broken" into a self-contained search query using conversation history. **Agentic / corrective RAG**, where the system retrieves, judges the result, and re-retrieves if confidence is low, buys accuracy at the cost of latency and token spend; reserve it for high-stakes answers, not every "where's my invoice." Benchmarks on text-and-table corpora confirm the two-stage hybrid-plus-reranker pipeline as the recommended baseline, with corrective loops as an upgrade, not a starting point.[^arxiv_bm25]

::: warning
Do not skip citations and provenance to ship faster. Retrofitting chunk-level attribution into a live RAG system means re-plumbing your generation layer and often re-ingesting your corpus. Every chunk should carry stable metadata — source URI, section, version, ingest timestamp — from the very first ingest run.
:::

## Data pipelines, freshness and sync

The demo indexes a corpus once. The product indexes a corpus that *changes* — help articles get edited, policies get rewritten, tickets get resolved — and here is the failure mode nobody sees coming: **semantic similarity has no temporal dimension.** A stale embedding scores exactly as high as a fresh one, so an out-of-date chunk gets retrieved with full confidence and the model answers from last quarter's refund policy. There is no error, no exception, no red line on a dashboard. Retrieval quality decays silently, and teams solve freshness last, usually after a customer catches a wrong answer.[^tianpan]

{case: **The RAG staleness problem named (April 2026)** - A widely-cited 2026 analysis dubbed this *index rot*: because stale and fresh vectors are indistinguishable to cosine similarity, knowledge bases degrade invisibly, and the fix is change-detection at ingest plus temporal metadata on every chunk so recency can be a retrieval signal rather than an afterthought.}

The batch answer — re-embed the whole corpus nightly — is wasteful and always a few hours stale. The 2026 production answer is **event-driven incremental sync via change data capture (CDC)**: tools like Debezium or Striim mine the database transaction log, and every insert, update, and delete emits a change event that flows through a streaming layer to re-embed *only* what changed, reflecting edits in the index within seconds.[^tianpan] You process deltas, not the corpus.

The operation everyone forgets is **deletes.** When a help article is retired, its chunks must leave the index immediately, or Cortex will keep citing a page that 404s. Your pipeline needs an explicit tombstone path — a delete event removes every chunk whose `source_id` matches — and updates must be handled as delete-then-insert so old chunk versions do not linger as ghosts alongside new ones. This is why stable, deterministic chunk IDs derived from source identity are not optional.

::: definition
**Index rot** — The silent divergence between what your vector index contains and what your source of truth actually says, caused by edits and deletions that never propagated. Undetectable by similarity scores; only source-linked freshness metadata and reconciliation catch it.
:::

A practical ingest contract for Cortex, expressed as the record every chunk carries:

```python
# Every chunk is idempotent, source-linked, and versioned.
chunk = {
    "id": stable_hash(source_id, chunk_index, content_version),
    "text": contextualized_text,      # child chunk + prepended context
    "embedding": embed(contextualized_text, dim=1024, dtype="int8"),
    "metadata": {
        "tenant_id": "acme",          # filter before search — hard isolation
        "source_id": "help/refunds",  # enables delete + reconcile
        "source_uri": "https://...",  # citation target
        "version": content_version,   # supersede old chunks on update
        "updated_at": "2026-07-30",   # temporal signal against index rot
    },
}
# On a CDC update event: delete WHERE source_id, then upsert new chunks.
```

Run a periodic **reconciliation** job regardless of how good your event stream is: walk the source of truth, confirm every live document has current chunks and every retired one has none. Streams drop messages; reconciliation is the backstop that turns silent rot into a caught discrepancy. Budget for it before you launch, not after the first embarrassing answer.

## Reranking, hybrid search and retrieval quality

Pure vector search has a blind spot that surprises people: it does not know words. Dense embeddings capture meaning, so they nail "automobile repair" ≈ "car maintenance" — but they fumble the exact tokens that matter most in support: product SKUs, error codes, API method names, version strings, a specific customer's account ID. On these, the decades-old keyword algorithm **BM25** beats dense retrieval, and 2026 benchmarks confirm BM25 outperforming even strong commercial embedding models on most metrics when queries contain rare, distinctive terms.[^appscale] For a Cortex ticket that says "getting `ERR_QUOTA_402` on the v3 batch endpoint," you want the chunk with that exact error code, and keyword search finds it while pure vectors drift toward "quota-related billing issues" in general.

**Hybrid search** runs both — dense and BM25 — and fuses the rankings, typically with **reciprocal rank fusion (RRF)**, which combines result lists without needing to normalize incompatible score scales. You get semantic recall and exact-match precision from the same query. This is the recall stage.

The precision stage is a **reranker**: a cross-encoder that scores each candidate against the query jointly (reading query and document together, not as two independent vectors), which is far more accurate but too slow to run over a whole corpus — so you run it over only the ~50–100 candidates hybrid search surfaced. The 2026 numbers make the case unambiguous. Hybrid retrieval plus a Cohere reranker delivered a **+17.4% relative Recall@5 over hybrid RRF alone and +39% over dense-only** on a text-and-table benchmark.[^arxiv_bm25] On a financial dataset, Cohere Rerank 3.5 scored +23.4% over hybrid search and +30.8% over BM25 alone.[^denser] The tax is latency: reranking adds roughly **100–300ms per query** (a hybrid-plus-Cohere top-50 pipeline measured p50 ≈ 230ms, p95 ≈ 410ms).[^appscale]

| Stage | What it does | Adds | When it earns its place |
|---|---|---|---|
| **Dense only** | Semantic recall | Baseline | Prototype; homogeneous prose |
| **+ BM25 (hybrid/RRF)** | Exact-term precision | ~small | Codes, SKUs, names, versions — i.e. support |
| **+ Reranker** | Cross-encoder precision cut | ~100–300ms[^appscale] | Quality-critical answers; large candidate sets |
| **+ Corrective loop** | Retrieve-judge-retry | 1+ extra round-trips | High-stakes; only when evals justify the cost |

::: rule
**Recall is cheap, precision is expensive — so buy them in that order.** Cast a wide, cheap net with hybrid search, then spend your latency and dollars reranking the shortlist. Never run your expensive stage over your whole corpus.
:::

For Cortex the full serving path is: rewrite the query using conversation context → hybrid retrieve 50 candidates (dense + BM25, RRF-fused, tenant-filtered) → rerank to the top 8 → generate with citations. The reranker is where quality is won: it is the difference between surfacing the article that *mentions* refunds and the one that *states the 30-day window*. Whether that pipeline actually improves answers — versus just feeling more sophisticated — is a question only retrieval evals can settle, and that is Chapter 10's domain. Build the pipeline here; prove it there.

::: takeaways
**Key takeaways**
- Chunking is the highest-leverage decision in the stack — ~80% of RAG failures originate there, not in the model. Start at 400–512 tokens, test overlap rather than assuming it, and adopt hierarchical (parent-document) chunking to resolve the precision/context trade-off.
- Contextual retrieval — prepending document context before embedding — cuts retrieval failures ~35% alone (up to ~49% with contextual BM25, ~67% with reranking) for one cheap LLM call per chunk at index time.
- Default your vector store to pgvector if you're under ~50–100M vectors and already on Postgres; graduate to a dedicated or object-storage-native engine only when a metric forces it.
- Use Matryoshka dimensions and int8/binary quantization to cut vector storage by more than an order of magnitude with negligible quality loss; never store 3,072-dim float32 by default.
- Freshness fails silently — stale embeddings score as high as fresh ones. Use CDC-driven incremental sync, handle deletes with tombstones, carry temporal metadata, and run reconciliation as a backstop against index rot.
- Retrieval quality is a two-stage problem: hybrid (dense + BM25/RRF) for cheap recall, then a cross-encoder reranker for expensive precision. It reliably beats dense-only by 30%+ on recall, at ~100–300ms.
:::

::: exercise
**Hands-on: Build and stress-test Cortex's retrieval core**
1. Take a real 50–200 page documentation set (your own product docs, or a public help center). Chunk it two ways: fixed 1,000-token blocks, and hierarchical 400-token child chunks with parent-section return. Embed both with a 1,024-dim model.
2. Add contextual retrieval to the hierarchical version: for each chunk, generate a one-line context header with a cheap model and prepend it before embedding.
3. Load all three indexes into pgvector with metadata columns for `source_id`, `version`, and `updated_at`. Add a BM25 index (Postgres full-text or a keyword engine) over the same chunks.
4. Write 20 realistic support queries — deliberately include 5 that hinge on exact tokens (error codes, SKUs, method names). Run each through: dense-only, hybrid (RRF), and hybrid + a reranker. Record which config retrieves the correct source chunk in the top 5.
5. Simulate index rot: edit 3 source documents and delete 1. Implement a delete-then-upsert path keyed on `source_id`, re-run the affected queries, and confirm no stale or ghost chunks are retrieved. Note how many queries would have returned wrong answers without the sync step.
:::

[^prem]: Building Production RAG: Architecture, Chunking, Evaluation & Monitoring (2026 Guide). PremAI. <https://blog.premai.io/building-production-rag-architecture-chunking-evaluation-monitoring-2026-guide/>
[^firecrawl]: Best Chunking Strategies for RAG (and LLMs) in 2026. Firecrawl. <https://www.firecrawl.dev/blog/best-chunking-strategies-rag>
[^anthropic]: Introducing Contextual Retrieval. Anthropic. <https://www.anthropic.com/engineering/contextual-retrieval>
[^voyage]: voyage-3-large: the new state-of-the-art general-purpose embedding model. Voyage AI. <https://blog.voyageai.com/2025/01/07/voyage-3-large/>
[^cohere]: Best Embedding Models for RAG (2026): Ranked by MTEB Score, Cost, and Self-Hosting. PremAI. <https://www.premai.io/blog/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/>
[^firecrawl_vdb]: Best Vector Databases in 2026: A Complete Comparison Guide. Firecrawl. <https://www.firecrawl.dev/blog/best-vector-databases>
[^appscale]: Hybrid Search and Re-ranking in Production RAG 2026: BM25, Dense, Cross-encoders, Fusion. AppScale Blog. <https://appscale.blog/en/blog/hybrid-search-and-reranking-production-rag-bm25-dense-cross-encoder-2026>
[^denser]: Hybrid Search for RAG: Combining BM25 and Dense Vector Search (2026 Guide). Denser.ai. <https://denser.ai/blog/hybrid-search-for-rag/>
[^arxiv_bm25]: From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents. arXiv. <https://arxiv.org/html/2604.01733v1>
[^tianpan]: The RAG Freshness Problem: How Stale Embeddings Silently Wreck Retrieval Quality. TianPan.co. <https://tianpan.co/blog/2026-04-10-rag-freshness-problem-stale-embeddings-silent-failure>