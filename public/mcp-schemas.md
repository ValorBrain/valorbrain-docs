# MCP tool schemas

Generated from `/opt/valorbrain/src/mcp-tools.ts`. 93 registerTool() calls.
This is the description and input shape the MCP server advertises.

## memory_retrieve

Unified memory retrieval — one call is enough for most questions (server expands/fuses queries). Prefer a SINGLE well-formed query; do not fire 5 near-duplicate retrieves.

Auto-routing: why→causal, last session→timeline, related→neighbors, general→hybrid.

Params:
- limit / max_results: how many hits to return (default 12; try 15–20 for broad topics).
- expand: server-side query expansion + score fusion (default true).
- snippet_chars: chars of body preview per hit (default 200) so you often skip get().
- budget: TOKEN budget for category-ranked recall mode (different from max_results).

After search: multi_get only for full bodies when snippet is insufficient.

```
z.object({
              query: z.string().describe("Your question or search query (one clear query; avoid spamming variants)"),
              mode: z.enum(["auto", "keyword", "semantic", "causal", "timeline", "discovery", "complex", "hybrid"]).optional().default("auto"),
              limit: z.number().optional().default(12).describe("Max ranked results to return (alias: max_results)"),
              max_results: z.number().optional().describe("Alias for limit — max ranked results (FB-0022)"),
              compact: z.boolean().optional().default(true),
              vault: z.string().optional(),
              expand: z.boolean().optional().describe("Server-side expansion + RRF fusion. Default: auto (server decides based on corpus size). Set true to force, false for fastest response."),
              snippet_chars: z.number().optional().default(200).describe("Snippet length in compact mode (default 200)"),
              budget: z.number().optional().describe("TOKEN budget for category-ranked recall (not result count). Prefer limit/max_results for hit count."),
              recall_format: z.enum(["json", "markdown"]).optional(),
            }),
    }
```

## memory_store

We decided to use PostgreSQL instead of MongoDBThe API rate limit is 100/minRoot cause: missing FOR UPDATE in the queryDeployed v2.0 to production

```
z.object({
              type: z.enum(['decision', 'observation', 'problem', 'milestone', 'handoff', 'lesson', 'note'])
                .describe("Memory type. 'decision' for choices made, 'observation' for facts learned, 'problem' for issues found, 'milestone' for progress, 'handoff' for context to pass forward, 'lesson' for takeaways, 'note' for general."),
              title: z.string().min(5).max(200).describe("Short title (5-200 chars). Will appear in search results and dashboard."),
              content: z.string().min(20).describe("Full memory content in markdown. Include context, reasoning, and evidence."),
              collection: z.string().optional().describe("Collection name (default: '_valorbrain'). Use a custom name to group related memories."),
              tags: z.array(z.string()).optional().describe("Optional tags for categorization."),
              confidence: z.number().min(0).max(1).optional().describe("Confidence score 0-1 (default: 0.8 for decisions, 0.6 for observations)."),
              visibility: z.enum(['tenant', 'private'])
                .optional()
                .default('tenant')
                .describe("Who can read this memory. 'tenant' (default) = everyone in the company sees it, with you as the author. 'private' = only you. Company memory is the product default — go private only for personal or sensitive notes."),
            }),
    }
```

## task_state

The working state of the current task, persisted and cross-session. goal sets what done means (appears in __goals__ of every memory_prepare); progress records milestones (__progress__, 48h); read returns goal + ledger + recent progress. ledger is the five-line J-Space discipline with SERVER-ENFORCED epistemic rules: ledger_open requires goal+next; ledger_checkpoint requires verified_by WITH stated coverage ('verified without coverage is a mood, not a result'); ledger_open_question requires settled_by (the cheapest test that could refute it); next is never empty. Open a goal when starting long-horizon work; checkpoint at each verified step; re-read after compaction or session boundaries.

```
z.object({
        action: z.enum(["goal", "progress", "ledger_open", "ledger_checkpoint", "ledger_open_question", "ledger_next", "read"]),
        slug: z.string().min(2).max(60).optional().describe("goal: short stable identifier, e.g. 'ship-v2-release'"),
        description: z.string().min(10).max(500).optional().describe("goal/ledger_open: what done means; progress: the milestone title"),
        status: z.string().optional().default("active").describe("goal: active, paused, complete"),
        detail: z.string().optional().describe("progress: additional context, blockers, next steps"),
        session: z.string().optional().describe("ledger/read: session key (defaults to the MCP token session)"),
        what: z.string().optional().describe("ledger_checkpoint: what now holds"),
        verified_by: z.string().optional().describe("ledger_checkpoint: what verified it AND what the verification covered (e.g. 'full suite, 2 passes, all files')"),
        question: z.string().optional().describe("ledger_open_question: the unsettled question"),
        settled_by: z.string().optional().describe("ledger_open_question: the cheapest test that could refute it"),
        next: z.string().optional().describe("ledger_open/ledger_next: the single next action"),
      }),
    }
```

## set_goal

DEPRECATED — use task_state with action goal. Create or update an active goal. Goals persist across sessions and are delivered to any agent via the __goals__ block in memory_prepare.

```
z.object({
        slug: z.string().min(2).max(60).describe("Short stable identifier, e.g. 'ship-v2-release'"),
        description: z.string().min(10).max(500).describe("What the goal is, current status, next steps"),
        status: z.string().optional().default("active").describe("Goal status: active, paused, complete"),
      }),
    }
```

## report_progress

DEPRECATED — use task_state with action progress. Record a progress milestone. Appears in the __progress__ block of memory_prepare for the next 48 hours.

```
z.object({
        title: z.string().min(5).max(200).describe("What was accomplished, e.g. 'Completed API migration, 60% of release done'"),
        detail: z.string().optional().describe("Additional context, blockers, or next steps"),
      }),
    }
```

## memory_forget

Remove a memory. Prefer path or docid for precise deletion. Query does fuzzy match (less safe).

```
z.object({
              query: z.string().optional().describe("What to forget — fuzzy search for closest match (less precise)"),
              path: z.string().optional().describe("Exact collection/path to deactivate (e.g. 'gbrain_full_2026_06_20_companies/companies/vitru.md'). Safe — no fuzzy matching."),
              docid: z.string().optional().describe("Exact doc ID (e.g. '#cbde70' or '850559'). Safe — no fuzzy matching."),
              confirm: z.boolean().optional().default(true).describe("If true, deactivates. If false, previews what would be forgotten."),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## profile

Get the current user profile (static facts + dynamic context). Rebuild if stale.

```
z.object({
              rebuild: z.boolean().optional().default(false).describe("Force rebuild the profile"),
              rollback: z.boolean().optional().describe("Revert the profile to the previous snapshot (prime-agent /refine pattern)"),
              rollback_hash: z.string().optional().describe("Roll back to a specific content hash (defaults to the most recent history entry)"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## working_context

One-shot stable facts + recent decisions/how-tos + optional session scratchpad. Prefer this at session start.

```
z.object({
              session_id: z.string().optional().describe("Session id for scratchpad slice"),
              format: z.enum(["markdown", "json"]).optional().default("markdown"),
              vault: z.string().optional(),
            }),
    }
```

## scratchpad

Read/write/clear ephemeral reasoning notes for this session. Not indexed in hybrid search.

```
z.object({
              action: z.enum(["read", "write", "clear", "append"]).describe("Operation"),
              session_id: z.string().describe("Session id (required)"),
              text: z.string().optional().describe("Body for write/append"),
              vault: z.string().optional(),
            }),
    }
```

## get

USE THIS for reading a file. Returns the document content by path or docid with optional line range. If you only need a snippet, set fromLine/maxLines.

```
z.object({
              file: z.string().describe("File path or docid (#abc123)"),
              fromLine: z.number().optional(),
              maxLines: z.number().optional(),
              lineNumbers: z.boolean().optional().default(false),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## multi_get

Retrieve multiple documents by glob pattern or comma-separated list.

```
z.object({
              pattern: z.string().describe("Glob pattern or comma-separated paths"),
              maxLines: z.number().optional(),
              maxBytes: z.number().optional().default(10240),
              lineNumbers: z.boolean().optional().default(false),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## find_similar

USE THIS for 'what else relates to X', 'show me similar docs'. Finds k-NN vector neighbors of a reference document — discovers connections beyond keyword overlap that search/query cannot find.

```
z.object({
              file: z.string().describe("Path of reference document"),
              limit: z.number().optional().default(5),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## reindex

Refresh all collections from the database. Detects stale embeddings and re-embeds documents that need it. Also cleans up orphaned FTS entries.

```
z.object({
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## operations

Long operations submitted with run_async=true. status checks a handle (wait_ms long-polls instead of spinning); list shows recent operations in the tenant, newest first — find a lost handle or see whether a reindex is already running; cancel asks a runner to stop cooperatively at its next checkpoint.

```
z.object({
        action: z.enum(["status", "list", "cancel"]).describe("Operation verb"),
        handle: z.string().optional().describe("status/cancel: operation handle (op_...)"),
        wait_ms: z.number().optional().describe("status: block up to this long (max 60000)"),
        status: z.enum(["queued", "running", "succeeded", "failed", "cancelled"]).optional().describe("list: filter"),
        operation: z.string().optional().describe("list: filter by tool name"),
        limit: z.number().optional().describe("list: default 20, max 100"),
        vault: z.string().optional(),
      }),
    }
```

## operation_status

DEPRECATED — use operations with action status. Check a long operation submitted with run_async=true. Returns status, progress and, once finished, the result. Pass wait_ms to long-poll instead of spinning on it.

```
z.object({
        handle: z.string().describe("Operation handle (op_...)"),
        wait_ms: z.number().optional().describe("Block up to this long waiting for it to finish (max 60000)"),
        vault: z.string().optional(),
      }),
    }
```

## operation_list

DEPRECATED — use operations with action list. Recent long operations in this tenant, newest first. Use to find a handle you lost, or to see whether somebody else already has a reindex running.

```
z.object({
        status: z.enum(["queued", "running", "succeeded", "failed", "cancelled"]).optional(),
        operation: z.string().optional().describe("Filter by tool name"),
        limit: z.number().optional().describe("Default 20, max 100"),
        vault: z.string().optional(),
      }),
    }
```

## operation_cancel

DEPRECATED — use operations with action cancel. Ask a running operation to stop. Cooperative: the runner stops at its next checkpoint, so a half-written reindex is not left behind.

```
z.object({
        handle: z.string().describe("Operation handle (op_...)"),
        vault: z.string().optional(),
      }),
    }
```

## memory_used

Declare quais memórias você realmente usou na resposta (docids como '#ab12cd', ou caminhos). Uma linha no seu prompt de sistema chamando esta ferramenta antes da resposta final registra uso declarado separado de recuperação. Para um comprovante antes da resposta final, envie receipt:{task_id,result} e note explicando a contribuição. Retorna receipt.summary sem LLM adicional; uso declarado, não prova causalidade ou economia. docids:[] com receipt declara ausência de uso.

```
z.object({
              docids: z
                .array(z.string())
                .min(0)
                .describe("Docids ('#ab12cd') ou caminhos das memórias efetivamente usadas"),
              verdict: z
                .enum(["confirmed", "corrected"])
                .optional()
                .describe("V5: o usuário CONFIRMOU o que a memória dizia ('confirmed') ou CORRIGIU/contradisse ('corrected') nesta resposta. Declare junto com os docids."),
              note: z.string().optional().describe("Por que serviu (opcional, entra no registro)"),
              receipt: ContributionReceiptRequestSchema.optional(),
              vault: z.string().optional(),
            }).refine((input) => input.docids.length > 0 || input.receipt !== undefined,
              "docids must not be empty unless receipt is requested"),
    }
```

## memory_grep

Busca por expressão regular no texto cru das memórias, devolvendo caminho e número de linha. Use quando a pergunta é exata e não aproximada: um valor, uma chave, um identificador, uma data, o que mudou entre duas versões. `memory_retrieve` acha o que é parecido; este acha o que é igual, e devolve só a linha — o que custa muito menos token que um trecho inteiro. Sintaxe do Postgres (ARE): \\d, \\y e classes funcionam, lookahead não.

```
z.object({
              pattern: z.string().describe("Expressão regular (sintaxe POSIX do Postgres)"),
              collection: z.string().optional().describe("Restringe a uma coleção"),
              since: z.string().optional().describe("Só documentos modificados desde esta data (ISO)"),
              context: z
                .boolean()
                .optional()
                .describe("Inclui a linha anterior e a seguinte de cada acerto"),
              case_sensitive: z.boolean().optional().describe("Diferencia maiúscula (padrão: não)"),
              limit: z.number().optional().describe("Teto de linhas (padrão 40, máx 200)"),
              doc_limit: z.number().optional().describe("Teto de documentos varridos (padrão 200)"),
              vault: z.string().optional(),
            }),
    }
```

## usage_report

Uso medido deste tenant: operações por canal (MCP, REST, hook), por ferramenta, por pessoa/agente, latência p50/p95, resultados devolvidos e série diária. Use para responder 'quantas consultas fizemos este mês' e para dimensionar valor entregue. Contagem direta do ledger — sem estimativa.

```
z.object({
              period: z
                .enum(["today", "week", "month", "quarter"])
                .optional()
                .describe("Janela do relatório (padrão: month = 30 dias)"),
              vault: z.string().optional(),
            }),
    }
```

## harness_coverage

Cobertura de entrega dos harnesses/agentes deste tenant: cruza atividade (uso de ferramentas) com ingestão (sessões entregues). Um agente listado como SILENT consulta a memória mas nunca entrega sessões — configurado pela metade. Use quando o usuário perguntar se a integração está completa/saudável, ou periodicamente: a saída traz o conserto exato para levar ao usuário.

```
z.object({
        days: z.number().int().min(1).max(90).optional()
          .describe("Janela em dias (padrão 7)"),
        min_activity: z.number().int().min(1).optional()
          .describe("Mínimo de chamadas para contar como ativo (padrão 10)"),
        vault: z.string().optional(),
      }),
    }
```

## index_stats

Detailed index statistics with content type distribution, staleness info, and memory health.

```
z.object({
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## beads_sync

Sync Beads issues from Dolt backend (bd CLI) into ValorBrain search index. Queries live Dolt database — no stale JSONL dependency.

```
z.object({
              project_path: z.string().optional().describe("Path to project with .beads/ directory (default: cwd)"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## build_graphs

Build temporal and semantic graphs for MAGMA multi-graph memory. Run after indexing documents.

```
z.object({
              graph_types: z.array(z.enum(['temporal', 'semantic', 'all'])).optional().default(['all']),
              semantic_threshold: z.number().optional().default(0.7).describe("Similarity threshold for semantic edges (0.0-1.0)"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## find_causal_links

USE THIS to trace decision chains: 'what led to X', 'trace how we got from A to B'. Follow up intent_search with this tool on a top result to walk the full causal chain. Returns depth-annotated links with reasoning.

```
z.object({
              docid: z.string().describe("Document ID (e.g., '#123' or path)"),
              direction: z.enum(['causes', 'caused_by', 'both']).optional().default('both').describe("Direction: 'causes' (outbound), 'caused_by' (inbound), or 'both'"),
              depth: z.number().optional().default(5).describe("Maximum traversal depth (1-10)"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## kg_query

Query the knowledge graph for an entity's relationships. Supports multihop traversal (2-3 hops) via pg_ripple SPARQL when VALORBRAIN_KG_ENGINE=hybrid|ripple. Returns structured facts with temporal validity (valid_from/valid_to). Use for 'what does X relate to?', 'what was true about X on date Y?', 'who/what is connected to X?'. Accepts an entity name (e.g. 'ValorBrain') OR a canonical entity ID in the form 'vault:type:slug' (e.g. 'default:service:valorbrain').

```
z.object({
              entity: z.string().describe("Entity name or canonical ID ('vault:type:slug') to query"),
              as_of: z.string().optional().describe("Date filter (YYYY-MM-DD) — only facts valid at this date"),
              direction: z.enum(["outgoing", "incoming", "both"]).optional().default("both").describe("Relationship direction"),
              max_hops: z.number().int().min(1).max(4).optional().describe("Graph traversal depth (1=star only, 2-3=multihop). Default from VALORBRAIN_KG_MAX_HOPS (2)."),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## kg_explain

Explain why a KG fact holds, including Datalog inference proof trees when pg_ripple.record_derivations is enabled. Pass entity names/IDs for subject and object (or object_literal for literal facts).

```
z.object({
              subject: z.string().describe("Subject entity name or canonical ID"),
              predicate: z.string().describe("Predicate (e.g. depends_on, runs_on)"),
              object: z.string().optional().describe("Object entity name or canonical ID"),
              object_literal: z.string().optional().describe("Object literal value (mutually exclusive with object)"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## memory_evolution_status

Get the evolution timeline for a memory document, showing how its keywords and context have changed over time based on new evidence.

```
z.object({
              docid: z.string().describe("Document ID (e.g., '#123' or path)"),
              limit: z.number().optional().default(10).describe("Maximum number of evolution entries to return (1-100)"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## timeline

Show the temporal neighborhood around a document — what was created/modified before and after it. Token-efficient progressive disclosure: search → timeline (context) → get (full content). Use after finding a document via search to understand what happened around it.

```
z.object({
              docid: z.string().describe("Document ID (e.g., '#123' or short hash)"),
              before: z.number().optional().default(5).describe("Number of documents to show before the focus (1-20)"),
              after: z.number().optional().default(5).describe("Number of documents to show after the focus (1-20)"),
              same_collection: z.boolean().optional().default(false).describe("Constrain to same collection (like session scoping)"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## memory_curate

Curate a memory's surfacing: pin for permanent prioritization (+0.3 boost), unpin, snooze to hide for N days, or unsnooze. USE PROACTIVELY: pin when the user states a persistent constraint, makes an architecture decision, or corrects a misconception; snooze when vault-context repeatedly surfaces irrelevant content (30 days by default). Resolves by search query.

```
z.object({
              action: z.enum(["pin", "unpin", "snooze", "unsnooze"]).describe("Curate verb"),
              query: z.string().describe("Search query to find the memory"),
              until: z.string().optional().describe("snooze only: ISO date to snooze until (default 30 days)"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## memory_pin

DEPRECATED — use memory_curate with action pin/unpin. Pin a memory for permanent prioritization (+0.3 boost). USE PROACTIVELY when: user states a persistent constraint, makes an architecture decision, or corrects a misconception. Don't wait for curator — pin critical decisions immediately.

```
z.object({
              query: z.string().describe("Search query to find the memory to pin/unpin"),
              unpin: z.boolean().optional().default(false).describe("Set true to unpin"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## memory_snooze

DEPRECATED — use memory_curate with action snooze/unsnooze. Temporarily hide a memory from context surfacing. USE PROACTIVELY when vault-context repeatedly surfaces irrelevant content — snooze it for 30 days instead of ignoring it. Reduces noise for future sessions.

```
z.object({
              query: z.string().describe("Search query to find the memory to snooze"),
              until: z.string().optional().describe("ISO date to snooze until (e.g. 2026-03-01). Omit to unsnooze."),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## lifecycle_status

Show document lifecycle statistics: active, archived, forgotten, pinned, snoozed counts and policy summary.

```
z.object({
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## ripple_rag_retrieve

Neuro-symbolic RAG via pg_ripple.rag_retrieve with 500ms budget (VB-3203). Returns entity context JSON for LLM grounding.

```
z.object({
              question: z.string().describe("Natural language question"),
              k: z.number().optional().default(5),
              budget_ms: z.number().optional().default(500),
              sparql_filter: z.string().optional(),
              vault: z.string().optional(),
            }),
    }
```

## list_entity_cards

List stable identity cards for entities in the current tenant.

```
z.object({
              limit: z.number().optional().default(50),
              offset: z.number().optional().default(0),
              vault: z.string().optional(),
            }),
    }
```

## append_entity_card

Append IDENTITY/ATTRIBUTE/RELATIONSHIP/INSTRUCTION entries to an entity card.

```
z.object({
              entity_id: z.string(),
              entries: z.array(z.string()),
              vault: z.string().optional(),
            }),
    }
```

## episodes

Bounded dialogue episodes (MemCell summaries) for episodic retrieval. list shows recent episodes (optionally by user); get fetches one by UUID.

```
z.object({
              action: z.enum(["list", "get"]).describe("Episode verb"),
              limit: z.number().optional().default(20).describe("list: max episodes"),
              user_id: z.string().optional().describe("list: filter by user"),
              episode_id: z.string().optional().describe("get: episode UUID"),
              vault: z.string().optional(),
            }),
    }
```

## list_memory_episodes

DEPRECATED — use episodes with action list. List bounded dialogue episodes (MemCell summaries) for episodic retrieval.

```
z.object({
              limit: z.number().optional().default(20),
              user_id: z.string().optional(),
              vault: z.string().optional(),
            }),
    }
```

## get_memory_episode

DEPRECATED — use episodes with action get. Fetch a single memory episode by UUID.

```
z.object({
              episode_id: z.string(),
              vault: z.string().optional(),
            }),
    }
```

## kg_quarantine

Triples rejected by the SHACL pre-check awaiting human review. list shows the queue; approve re-validates and persists a triple into entity_triples; reject discards it permanently. Curator surface.

```
z.object({
              action: z.enum(["list", "approve", "reject"]).describe("Quarantine verb"),
              quarantine_id: z.string().uuid().optional().describe("approve/reject: the quarantine entry id"),
              limit: z.number().optional().default(50).describe("list: max entries"),
              vault: z.string().optional(),
            }),
    }
```

## list_kg_quarantine

DEPRECATED — use kg_quarantine with action list. List triples rejected by SHACL pre-check awaiting human review.

```
z.object({
              limit: z.number().optional().default(50),
              vault: z.string().optional(),
            }),
    }
```

## approve_kg_quarantine

DEPRECATED — use kg_quarantine with action approve. Re-validate and persist an approved quarantined triple into entity_triples.

```
z.object({
              quarantine_id: z.string().uuid(),
              vault: z.string().optional(),
            }),
    }
```

## reject_kg_quarantine

DEPRECATED — use kg_quarantine with action reject. Permanently discard a quarantined triple candidate.

```
z.object({
              quarantine_id: z.string().uuid(),
              vault: z.string().optional(),
            }),
    }
```

## kg_entity_resolve_report

VB-3306 dedup report: eval-suite hit rate + near-duplicate entity pairs.

```
z.object({ vault: z.string().optional() }),
    }
```

## memory_prepare

PMB-style single-call context assembly: recall + vault-facts + foresights + funnel (episodes, lessons, keyed facts, top docs).

```
z.object({
              message: z.string().describe("User message or query to prepare context for"),
              surface_id: z.string().optional().describe("Surface for lesson filtering"),
              collection: z.string().optional().describe("Collection scope for funnel search"),
              episode_id: z.string().optional().describe("Episode UUID for scoped hybrid retrieval"),
              recall_budget: z.number().optional().default(600),
              fast_mode: z.boolean().optional().default(false).describe(
                "Skip funnel document retrieval (embedding + hybrid search). " +
                "Recall still covers docs by category. Use for low-latency hooks."
              ),
              vault: z.string().optional(),
            }),
    }
```

## record_lesson

Record or verify a procedural lesson for a surface (PMB-style follow-through). Dedupes on surface_id + content; set verify=true to bump follow-through score.

```
z.object({
              surface_id: z.string().describe("Surface or workflow this lesson applies to"),
              content: z.string().describe("Lesson text (what to do / avoid)"),
              evidence: z.string().optional().describe("Supporting evidence or citation"),
              episode_id: z.string().optional().describe("Linked episode UUID"),
              verify: z.boolean().optional().default(false).describe("Bump verification count"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## list_lessons

List procedural lessons for the tenant, optionally filtered by surface or min follow-through score.

```
z.object({
              surface_id: z.string().optional().describe("Filter by surface"),
              min_score: z.number().optional().describe("Minimum follow_through_score (0–1)"),
              limit: z.number().optional().default(20),
              vault: z.string().optional(),
            }),
    }
```

## memory_arcs

Narrative memory arcs — threads linking episodes and goals. create opens an arc around a goal; list filters arcs by episode, status (active/completed/paused) or recency.

```
z.object({
              action: z.enum(["create", "list"]).describe("Arc verb"),
              title: z.string().optional().describe("create: arc title"),
              summary: z.string().optional().describe("create: arc summary"),
              goal: z.string().optional().describe("create: the goal this arc tracks"),
              episode_ids: z.array(z.string()).optional().describe("create: episodes to link"),
              episode_id: z.string().optional().describe("list: filter arcs containing this episode"),
              status: z.enum(["active", "completed", "paused"]).optional().describe("list: filter by status"),
              limit: z.number().optional().default(20).describe("list: max arcs"),
              vault: z.string().optional(),
            }),
    }
```

## list_memory_arcs

DEPRECATED — use memory_arcs with action list. List narrative memory arcs (threads linking episodes and goals).

```
z.object({
              episode_id: z.string().optional().describe("Filter arcs containing this episode"),
              status: z.enum(["active", "completed", "paused"]).optional(),
              limit: z.number().optional().default(20),
              vault: z.string().optional(),
            }),
    }
```

## create_memory_arc

DEPRECATED — use memory_arcs with action create. Create a narrative arc linking episodes and a goal.

```
z.object({
              title: z.string().describe("Arc title"),
              summary: z.string().optional(),
              goal: z.string().optional(),
              episode_ids: z.array(z.string()).optional(),
              vault: z.string().optional(),
            }),
    }
```

## keyed_facts_as_of

Time-travel query: latest value per fact_key where as_of <= date (YYYY-MM-DD).

```
z.object({
              as_of: z.string().describe("Query date YYYY-MM-DD"),
              keys: z.array(z.string()).optional().describe("Restrict to these keys"),
              vault: z.string().optional(),
            }),
    }
```

## upsert_keyed_fact

Insert or update a temporal keyed fact snapshot (tenant, key, as_of unique). Runs the same authority policy as corrections: a weaker caller over a protected winner becomes a pending proposal instead of a write.

```
z.object({
              fact_key: z.string(),
              fact_value: z.string(),
              as_of: z.string().describe("Snapshot date YYYY-MM-DD"),
              evidence: z.string().optional(),
              authority: z.enum(["human", "designated", "agent", "import"]).optional(),
              vault: z.string().optional(),
            }),
    }
```

## assert_authority_correction

Correctability (3C): persist a durable keyed fact with authority, mark prior values for the same key as superseded (non-winning), and soft-invalidate free-form docs in the tenant that still assert the old value without the new one. Pass losing_values when the wrong value only lived in prose (never as a keyed fact). Currency formats (R$20K vs 20000) are normalized. Tenant-scoped; no hardcoded accounts.

```
z.object({
              fact_key: z.string().describe("Stable key, e.g. account.alpha.received_brl"),
              fact_value: z.string().describe("Correct value"),
              as_of: z.string().describe("Snapshot date YYYY-MM-DD"),
              authority: z
                .enum(["human", "designated", "agent", "import"])
                .describe("human > designated > import > agent"),
              evidence: z.string().optional(),
              losing_values: z
                .array(z.string())
                .optional()
                .describe("Wrong prior values to demote in prose (e.g. ['20000','20k'] when correcting to 30000)"),
              vault: z.string().optional(),
            }),
    }
```

## list_arcs

DEPRECATED — use memory_arcs with action list. List narrative arcs (goal-oriented threads linked to episodes). Optional status filter.

```
z.object({
              status: z.enum(["active", "completed", "paused"]).optional().describe("Filter by status: active | completed | paused"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## lifecycle_sweep

Run lifecycle policies: archive stale docs, optionally purge old archives. Defaults to dry_run (preview only).

```
z.object({
              dry_run: z.boolean().optional().default(true).describe("Preview what would be archived/purged without acting"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## lifecycle_restore

Restore documents that were auto-archived by lifecycle policies. Does NOT restore manually forgotten documents.

```
z.object({
              query: z.string().optional().describe("Search archived docs by keyword to find what to restore"),
              collection: z.string().optional().describe("Restore all archived docs from a specific collection"),
              all: z.boolean().optional().default(false).describe("Restore ALL archived documents"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## list_vaults

Show all configured vault names and their SQLite paths. Returns empty if running in single-vault mode (default).

```
z.object({}),
    }
```

## vault_sync

Index markdown documents from a directory into a named vault. Use to populate a vault with content from a specific path.

```
z.object({
              vault: z.string().describe("Target vault name (must be configured in config.yaml or VALORBRAIN_VAULTS)"),
              content_root: z.string().describe("Directory path to index markdown files from"),
              pattern: z.string().optional().default("**/*.md").describe("Glob pattern (default: **/*.md)"),
              collection_name: z.string().optional().describe("Collection name in the vault. Defaults to vault name."),
            }),
    }
```

## diary

The agent's observational diary. WRITE to record events, decisions or context worth reviewing later (entries become searchable memories — useful where no hook support exists). READ recent entries to review past observations.

```
z.object({
              action: z.enum(["read", "write"]).describe("Diary verb"),
              entry: z.string().optional().describe("write: diary entry text"),
              topic: z.string().optional().describe("write: topic tag (e.g., 'technical', 'user_facts', 'session')"),
              agent: z.string().optional().describe("write: agent name; read: filter by agent name"),
              last_n: z.number().optional().describe("read: number of recent entries (default 10)"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## diary_write

DEPRECATED — use diary with action write. Write to the agent's diary. Use for recording important events, decisions, or observations in environments without hook support. Entries are stored as memories and are searchable.

```
z.object({
              entry: z.string().describe("Diary entry text"),
              topic: z.string().optional().default("general").describe("Topic tag (e.g., 'technical', 'user_facts', 'session')"),
              agent: z.string().optional().default("agent").describe("Agent name writing the entry"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## diary_read

DEPRECATED — use diary with action read. Read recent diary entries. Use to review past observations and events recorded by the agent.

```
z.object({
              last_n: z.number().optional().default(10).describe("Number of recent entries to return"),
              agent: z.string().optional().describe("Filter by agent name"),
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
            }),
    }
```

## whoami

Returns who THIS MCP connection is: tenant, user, agent slug (from token), team member if any, and the tenant identity summary. Call after connect to verify multi-user setup. No extra headers needed — the Bearer token already identifies you.

```
z.object({}),
      }
```

## memory_health

Returns open proposal/conflict counts, high-priority items, and canonical sources with drift. Call at end of substantive sessions.

```
z.object({
                  entity: z.string().optional().describe("Filter proposals by path/title/summary substring"),
                  limit: z.number().optional().describe("Max high-priority proposals (default 3)"),
                }),
      }
```

## list_proposals

Returns proposals for canonical docs that may need updating. Agents (Hermes/Claude/etc) consume these to execute write-back.

```
z.object({
                  limit: z.number().optional().describe("Max proposals (default 20)"),
                }),
      }
```

## store

Stores a markdown document in the tenant's memory. Use for explicit notes, decisions, or facts that the agent wants persisted.

```
z.object({
                  path: z.string().describe("Logical path/identifier (e.g. 'decisions/2026-05.md')"),
                  content: z.string().describe("Markdown content"),
                  title: z.string().optional().describe("Optional title for retrieval"),
                  collection: z.string().optional().describe("Collection name (default: 'memories')"),
                }),
      }
```

## export_docs

Export documents from a collection to a JSON array. Useful for backup, migration, or cross-instance transfer.

```
z.object({
                  collection: z.string().optional().describe("Collection to export (omit for all)"),
                  limit: z.number().optional().default(1000).describe("Max documents to export"),
                  format: z.enum(["json", "ndjson"]).optional().default("json").describe("Output format: json (array) or ndjson (one-per-line)"),
                }),
      }
```

## import_docs

Import documents from a JSON array. Each object needs collection, path, title, and body. Supports upsert (existing docs with same collection+path get updated).

```
z.object({
                  documents: z.string().describe("JSON string: array of {collection, path, title, body, content_type?, tags?, confidence?}"),
                  on_conflict: z.enum(["upsert", "skip", "error"]).optional().default("upsert").describe("How to handle existing docs with same collection+path"),
                }),
      }
```

## feedback

Channel to the ValorBrain product team (not end-user CRM). submit files a bug/feature/question/praise — returns FB-XXXX; check tracks status and team response by id or 'all'. WHEN TO CALL (agents): tool/MCP errors; empty or wrong memory_retrieve when knowledge should exist; ranking noise; missing capability; verified fix (praise). WHEN NOT TO: normal successful domain work, chat without a product defect, secrets in the body. One FB per distinct issue.

```
z.object({
              action: z.enum(["submit", "check"]).describe("Feedback verb"),
              title: z.string().min(5).max(200).optional().describe("submit: short title — what is this about?"),
              description: z.string().min(10).max(5000).optional().describe("submit: what happened / expected / steps, or what you want and why"),
              category: z.enum(["bug", "feature", "question", "improvement", "praise", "feedback"]).optional().default("feedback").describe("submit: type of feedback"),
              priority: z.enum(["low", "normal", "high", "critical"]).optional().default("normal").describe("submit: suggested priority (team may adjust)"),
              tags: z.array(z.string()).optional().describe("submit: optional tags"),
              feedback_id: z.string().optional().describe("check: FB-XXXX or 'all' to list recent"),
              vault: z.string().optional(),
            }),
    }
```

## feedback_submit

DEPRECATED — use feedback with action submit. Submit a bug report, feature request, question, praise, or improvement to the ValorBrain product team (not end-user CRM). Returns FB-XXXX for tracking via feedback action check. WHEN TO CALL (agents): ValorBrain tool/MCP errors; empty or wrong memory_retrieve when knowledge should exist; ranking noise; missing capability blocking work; verified fix (category=praise). WHEN NOT TO: normal successful domain work, chat without a product defect, secrets in the body. One FB per distinct issue. Human ops triage at ValorBrain Ops /feedback.

```
z.object({
              title: z.string().min(5).max(200).describe("Short title — what is this about?"),
              description: z.string().min(10).max(5000).describe("Detailed description. For bugs: what happened, what you expected, steps to reproduce. For features: what you want and why."),
              category: z.enum(["bug", "feature", "question", "improvement", "praise", "feedback"]).default("feedback").describe("Type of feedback"),
              priority: z.enum(["low", "normal", "high", "critical"]).default("normal").describe("Suggested priority (team may adjust)"),
              tags: z.array(z.string()).optional().describe("Optional tags for categorization"),
              vault: z.string().optional(),
            }),
    }
```

## feedback_check

DEPRECATED — use feedback with action check. Check the status and response of submitted feedback. Use the feedback ID (FB-XXXX) or 'all' to list recent.

```
z.object({
              feedback_id: z.string().describe("Feedback ID (e.g. FB-0001) or 'all' to list recent"),
              vault: z.string().optional(),
            }),
    }
```

## notifications

Your notification inbox for team and system messages: feedback responses, announcements, alerts. check returns unread count + recent items ('all' includes read; an N-XXXX id fetches one). mark_read dismisses by id or 'all'.

```
z.object({
              action: z.enum(["check", "mark_read"]).describe("Inbox verb"),
              filter: z.string().optional().describe("check: 'unread' (default), 'all', or a notification ID (N-XXXX)"),
              notification_id: z.string().optional().describe("mark_read: notification ID (N-XXXX) or 'all'"),
              vault: z.string().optional(),
            }),
    }
```

## notifications_check

DEPRECATED — use notifications with action check. Check your notification inbox for unread messages from the team or system. Includes feedback responses, announcements, and alerts. Returns unread count + recent items. Use 'all' to include read items, or a specific notification ID.

```
z.object({
              filter: z.string().optional().describe("'unread' (default), 'all', or a notification ID (N-XXXX)"),
              vault: z.string().optional(),
            }),
    }
```

## notifications_mark_read

DEPRECATED — use notifications with action mark_read. Mark a notification as read/dismissed. Use the notification ID (N-XXXX) or 'all' to mark everything read.

```
z.object({
              notification_id: z.string().describe("Notification ID (N-XXXX) or 'all'"),
              vault: z.string().optional(),
            }),
    }
```

## team_message

Send an async message to a teammate (human or agent). They'll see it in their inbox on their next briefing or inbox check. For questions, context, or coordination that doesn't need an immediate reply.

```
z.object({
              to: z.string().describe("Recipient: a teammate's name or member id"),
              title: z.string().min(3).max(200).describe("Short subject"),
              body: z.string().optional().describe("Message content"),
              category: z.enum(["message", "request", "decision", "alert"]).default("message").describe("message = chat, request = asks for action, decision = record a choice, alert = needs attention"),
              priority: z.enum(["low", "normal", "high", "critical"]).default("normal"),
              vault: z.string().optional(),
            }),
    }
```

## team_handoff

Durable async work assignment in the shared brain. create hands work to a teammate with context — the recipient should DO something with it (open questions, files changed); shows in their briefing until consumed; status=blocked_on_human parks it waiting on a human (anti-loop). consume marks a handoff done after finishing the work or closing a duplicate/resolved loop — prevents briefing clutter.

```
z.object({
              action: z.enum(["create", "consume"]).optional().default("create").describe("Handoff verb (default create)"),
              to: z.string().optional().describe("create: recipient teammate name or id"),
              summary: z.string().min(5).max(500).optional().describe("create: what this handoff is about / what needs doing"),
              open_questions: z.array(z.string()).optional().describe("create: questions for the recipient to resolve"),
              files_changed: z.array(z.string()).optional().describe("create: files involved"),
              priority: z.enum(["low", "normal", "high", "critical"]).optional().default("normal"),
              status: z.enum(["pending", "blocked_on_human"]).optional().default("pending")
                .describe("create: pending=actionable work; blocked_on_human=parked waiting on human (do not re-escalate)"),
              handoff_id: z.union([z.string(), z.number()]).optional().describe("consume: handoff id to consume"),
              note: z.string().max(500).optional().describe("consume: optional completion note"),
              vault: z.string().optional(),
            }),
    }
```

## team_handoff_consume

DEPRECATED — use team_handoff with action consume. Mark a team handoff as consumed (done). Use after finishing the work or when closing a duplicate/resolved loop. Prevents briefing clutter from stale pending handoffs.

```
z.object({
              handoff_id: z.union([z.string(), z.number()]).describe("Handoff id to consume"),
              note: z.string().max(500).optional().describe("Optional completion note"),
              vault: z.string().optional(),
            }),
    }
```

## team_inbox

Check messages sent to you by teammates. Returns unread count and recent messages. Mark read with notifications_mark_read once handled.

```
z.object({
              unread_only: z.boolean().default(true).describe("If false, include already-read messages"),
              vault: z.string().optional(),
            }),
    }
```

## team_briefing

Get oriented when starting work: your unread inbox, pending handoffs, the team's shared mission (foundations), and recent activity across the team. Call this at the start of a session to understand what needs attention and stay aligned with company direction.

```
z.object({
              vault: z.string().optional(),
            }),
    }
```

## team_roster

List who's on the team (humans and agents), their roles, and how to reach them. Use before messaging to know who handles what.

```
z.object({
              vault: z.string().optional(),
            }),
    }
```

## team_notify_human

Pull a human teammate into a conversation NOW via their messaging channel (Telegram/Discord/etc.). Use when you need a decision, approval, or unblock that only a human can make and it can't wait for them to check their inbox. The message is ALSO saved to their ValorBrain inbox. Resolve the human by name or role; 'manager'/'lead'/'human' match any human in your team. Reserve for things that genuinely need human attention — don't spam.

```
z.object({
              to: z.string().describe("Human teammate name, role, or 'manager'/'lead'/'human' to reach any human on the team"),
              title: z.string().min(3).max(200).describe("What you need — short, action-oriented"),
              body: z.string().optional().describe("Context: why you need them, what decision/approval"),
              priority: z.enum(["normal", "high", "critical"]).default("normal"),
              vault: z.string().optional(),
            }),
    }
```

## decisions

First-class, auditable decision records. record creates a hash-chained node (category/scenario/reasoning/outcome/confidence); relate links two decisions causally (caused/influenced/precedent_for); trace walks the causal chain up or downstream; similar finds precedents for a scenario; list filters by category/date/confidence. Use similar BEFORE deciding, record AFTER.

```
z.object({
        action: z.enum(["record", "relate", "trace", "similar", "list"]).describe("Decision verb"),
        category: z.string().min(2).max(100).optional().describe("record/list: decision category, e.g. 'architecture'"),
        scenario: z.string().min(10).optional().describe("record: what triggered this decision"),
        reasoning: z.string().optional().describe("record/relate: the rationale"),
        outcome: z.string().min(3).optional().describe("record: what was decided / the result"),
        confidence: z.number().min(0).max(1).optional().describe("record/relate: confidence 0-1"),
        decision_maker: z.string().optional().describe("record: who or what made the decision"),
        valid_from: z.string().optional().describe("record: valid from (YYYY-MM-DD)"),
        valid_until: z.string().optional().describe("record: expires/superseded (YYYY-MM-DD)"),
        source_doc_ids: z.array(z.string()).optional().describe("record: document IDs that informed this decision"),
        source_decision_id: z.string().optional().describe("relate: UUID of the upstream decision"),
        target_decision_id: z.string().optional().describe("relate: UUID of the downstream decision"),
        relationship_type: z.enum(["caused", "influenced", "precedent_for"]).optional().describe("relate: how source relates to target"),
        decision_id: z.string().optional().describe("trace: UUID of the decision to trace from"),
        direction: z.enum(["causes", "caused_by", "both"]).optional().default("both").describe("trace: direction"),
        max_depth: z.number().min(1).max(10).optional().default(5).describe("trace: max depth (1-10)"),
        query: z.string().min(5).optional().describe("similar: scenario to find precedents for"),
        start_date: z.string().optional().describe("list: from date (YYYY-MM-DD)"),
        end_date: z.string().optional().describe("list: to date (YYYY-MM-DD)"),
        min_confidence: z.number().min(0).max(1).optional().describe("list: minimum confidence"),
        limit: z.number().min(1).max(100).optional().default(20).describe("similar/list: max results"),
      }),
    }
```

## record_decision

DEPRECATED — use decisions with action record. Record a structured decision with category, scenario, reasoning, outcome, and confidence. Creates a first-class, queryable, auditable decision node with a hash-chained trace entry. Follow up with decisions action relate to build causal links.

```
z.object({
        category: z.string().min(2).max(100).describe("Decision category, e.g. 'architecture', 'vendor_selection', 'budget'"),
        scenario: z.string().min(10).describe("What was the situation that triggered this decision"),
        reasoning: z.string().optional().describe("Why this decision was made — the rationale"),
        outcome: z.string().min(3).describe("What was decided / the result"),
        confidence: z.number().min(0).max(1).optional().describe("Confidence score 0-1 (default 0.8)"),
        decision_maker: z.string().optional().describe("Who or what made the decision"),
        valid_from: z.string().optional().describe("When the decision becomes valid (YYYY-MM-DD)"),
        valid_until: z.string().optional().describe("When the decision expires/superseded (YYYY-MM-DD)"),
        source_doc_ids: z.array(z.string()).optional().describe("Document IDs that informed this decision"),
      }),
    }
```

## add_decision_relation

DEPRECATED — use decisions with action relate. Link two decisions with a causal relationship (caused / influenced / precedent_for). Builds auditable causal chains.

```
z.object({
        source_decision_id: z.string().describe("UUID of the source (earlier/upstream) decision"),
        target_decision_id: z.string().describe("UUID of the target (later/downstream) decision"),
        relationship_type: z.enum(["caused", "influenced", "precedent_for"]).describe("How source relates to target"),
        reasoning: z.string().optional().describe("Why this causal link exists"),
        confidence: z.number().min(0).max(1).optional().describe("Link confidence 0-1 (default 0.7)"),
      }),
    }
```

## trace_decision_chain

DEPRECATED — use decisions with action trace. Trace the full causal ancestry or downstream impact of a decision. Direction 'caused_by' = what led to this decision (upstream), 'causes' = what this decision led to (downstream).

```
z.object({
        decision_id: z.string().describe("UUID of the decision to trace from"),
        direction: z.enum(["causes", "caused_by", "both"]).optional().default("both").describe("Direction to trace"),
        max_depth: z.number().min(1).max(10).optional().default(5).describe("Maximum traversal depth (1-10)"),
      }),
    }
```

## find_similar_decisions

DEPRECATED — use decisions with action similar. Semantic precedent search across past decisions. Given a scenario description, finds decisions with similar category, scenario, or outcome. Use before making a decision to find relevant precedents.

```
z.object({
        query: z.string().min(5).describe("Scenario or question to find precedents for"),
        limit: z.number().min(1).max(50).optional().default(10).describe("Max results (default 10)"),
      }),
    }
```

## list_decisions

DEPRECATED — use decisions with action list. List decisions with optional filters (category, date range, min confidence). Ordered by most recent first.

```
z.object({
        category: z.string().optional().describe("Filter by category"),
        start_date: z.string().optional().describe("Filter from date (YYYY-MM-DD)"),
        end_date: z.string().optional().describe("Filter to date (YYYY-MM-DD)"),
        min_confidence: z.number().min(0).max(1).optional().describe("Minimum confidence threshold"),
        limit: z.number().min(1).max(100).optional().default(20).describe("Max results (default 20)"),
      }),
    }
```

## provenance

W3C PROV-O lineage of an entity. trace walks parent/used edges — where a fact came from (upstream) and what depends on it (downstream); export emits the full audit trail as RDF Turtle with hash-chain integrity metadata (regulator-ready).

```
z.object({
        action: z.enum(["trace", "export"]).describe("Provenance verb"),
        entity_id: z.string().describe("The entity (document hash, triple ID, keyed_fact key)"),
        direction: z.enum(["upstream", "downstream", "both"]).optional().default("both").describe("trace only: upstream = where it came from, downstream = what derived from it"),
        max_depth: z.number().min(1).max(10).optional().default(5).describe("trace only: maximum traversal depth (1-10)"),
      }),
    }
```

## trace_lineage

DEPRECATED — use provenance with action trace. Trace the full W3C PROV-O lineage of an entity — where it came from (upstream) or what was derived from it (downstream). Answers 'where did this fact come from?' and 'what depends on this?'

```
z.object({
        entity_id: z.string().describe("The entity to trace (document hash, triple ID, keyed_fact key)"),
        direction: z.enum(["upstream", "downstream", "both"]).optional().default("both").describe("upstream = where it came from, downstream = what derived from it"),
        max_depth: z.number().min(1).max(10).optional().default(5).describe("Maximum traversal depth (1-10)"),
      }),
    }
```

## export_provenance

DEPRECATED — use provenance with action export. Export the full W3C PROV-O provenance of an entity as RDF Turtle — regulator-ready audit trail with hash-chain integrity metadata.

```
z.object({
        entity_id: z.string().describe("Entity to export provenance for"),
      }),
    }
```

## conflicts

Contradictions across the tenant's knowledge. detect scans for value/temporal/relationship conflicts (also auto-detected by the consolidation tick); list shows them filtered by status/type/severity; resolve picks a strategy and winner. Curator surface.

```
z.object({
        action: z.enum(["detect", "list", "resolve"]).describe("Conflict verb"),
        status: z.enum(["detected", "reviewing", "resolved", "ignored"]).optional().describe("list: filter by status"),
        conflict_type: z.enum(["value", "type", "relationship", "temporal", "logical"]).optional().describe("list: filter by conflict type"),
        severity: z.enum(["critical", "high", "medium", "low"]).optional().describe("list: filter by severity"),
        limit: z.number().min(1).max(100).optional().default(20).describe("list: max results"),
        conflict_id: z.string().optional().describe("resolve: UUID of the conflict to resolve"),
        resolution_strategy: z.enum(["voting", "credibility_weighted", "most_recent", "first_seen", "highest_confidence", "authority", "manual_review"]).optional().describe("resolve: how the conflict was resolved"),
        resolved_value: z.string().optional().describe("resolve: the chosen value"),
        resolved_source: z.enum(["source_a", "source_b", "merged", "custom"]).optional().describe("resolve: which source won"),
        resolution_note: z.string().optional().describe("resolve: optional note explaining the resolution"),
      }),
    }
```

## detect_conflicts

DEPRECATED — use conflicts with action detect. Scan for contradictions across the tenant's knowledge: value conflicts (same fact_key, different values), temporal conflicts (valid_until < as_of), and relationship conflicts (contradictory triples). Returns detected conflicts with severity.

```
z.object({}),
    }
```

## list_conflicts

DEPRECATED — use conflicts with action list. List detected fact conflicts with optional filters (status, type, severity). Ordered by severity (critical first) then detection date.

```
z.object({
        status: z.enum(["detected", "reviewing", "resolved", "ignored"]).optional().describe("Filter by status"),
        conflict_type: z.enum(["value", "type", "relationship", "temporal", "logical"]).optional().describe("Filter by conflict type"),
        severity: z.enum(["critical", "high", "medium", "low"]).optional().describe("Filter by severity"),
        limit: z.number().min(1).max(100).optional().default(20).describe("Max results (default 20)"),
      }),
    }
```

## resolve_conflict

DEPRECATED — use conflicts with action resolve. Resolve a detected fact conflict by choosing a resolution strategy and winner. Strategies: voting, credibility_weighted, most_recent, first_seen, highest_confidence, authority, manual_review.

```
z.object({
        conflict_id: z.string().describe("UUID of the conflict to resolve"),
        resolution_strategy: z.enum(["voting", "credibility_weighted", "most_recent", "first_seen", "highest_confidence", "authority", "manual_review"]).describe("How the conflict was resolved"),
        resolved_value: z.string().describe("The chosen value"),
        resolved_source: z.enum(["source_a", "source_b", "merged", "custom"]).describe("Which source won"),
        resolution_note: z.string().optional().describe("Optional note explaining the resolution"),
      }),
    }
```
