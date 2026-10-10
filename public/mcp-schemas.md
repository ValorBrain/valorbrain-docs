# MCP tool schemas

Generated from `/opt/valorbrain/src/mcp-tools.ts`: one section per registerTool() call.
This is the description and input shape the MCP server advertises.
Tool count: https://docs.valorbrain.com.br/docs/api/generated-mcp (catalog).

## memory_retrieve

Unified retrieval — one well-formed call is enough; the server expands and fuses. Routing: why→causal, last session→timeline, related→neighbors, else→hybrid.

```
z.object({
              query: z.string(),
              mode: z.enum(["auto", "keyword", "semantic", "causal", "timeline", "discovery", "complex", "hybrid"]).optional().default("auto"),
              limit: z.number().optional().default(12),
              max_results: z.number().optional(),
              compact: z.boolean().optional().default(true),
              vault: z.string().optional(),
              expand: z.boolean().optional().describe("Server-side expansion + fusion; default auto"),
              snippet_chars: z.number().optional().default(200),
              budget: z.number().optional(),
              recall_format: z.enum(["json", "markdown"]).optional(),
              min_score: z.number().optional().describe("Min composite score (0-1)"),
            }),
    }
```

## memory_recent

Answer "what did agent X do recently?" — work-product docs (decision/milestone/handoff/lesson/problem/observation) by source_agent, newest first.

```
z.object({
              agent: z.string().optional().describe("Author slug"),
              hours: z.number().optional().default(24).describe("Window hours (default 24, max 720)"),
              since: z.string().optional().describe("ISO lower bound (overrides hours)"),
              types: z.array(z.string()).optional(),
              limit: z.number().optional().default(12).describe("Max items (default 12, max 40)"),
              query: z.string().optional(),
              vault: z.string().optional(),
            }),
    }
```

## memory_draft

Prepare the exact memory content for a user-authorized save. Does not persist it. Returns a signed draft and an operation key; edited content needs a new draft.

```
memoryDraftSchema}
```

## memory_store

```
z.object({
              type: z.union([
                z.enum(['decision', 'observation', 'problem', 'milestone', 'handoff', 'lesson', 'note']),
                z.string(),
              ]),
              title: z.string().min(5).max(200),
              content: z.string().min(20),
              collection: z.string().optional().describe("Default: your agent collection (agent-<you>), tenant-visible"),
              tags: z.array(z.string()).optional(),
              confidence: z.number().min(0).max(1).optional(),
              visibility: z.enum(['tenant', 'private'])
                .optional()
                .default('tenant')
                .describe("'tenant' (default) = whole company; 'private' = only you."),
            }),
    }
```

## task_state

Cross-session working state. goal sets what done means (in memory_prepare __goals__ until complete); progress records milestones; read: goal+ledger+progress. Ledger: checkpoint needs verified_by with coverage; open question needs settled_by; next never empty.

```
z.object({
        action: z.enum(["goal", "progress", "ledger_open", "ledger_checkpoint", "ledger_open_question", "ledger_next", "read"]),
        slug: z.string().min(2).max(60).optional(),
        description: z.string().min(10).max(500).optional().describe("goal/ledger_open: what done means; progress: milestone title"),
        status: z.string().optional().default("active").describe("goal: active|paused|complete"),
        detail: z.string().optional(),
        session: z.string().optional().describe("session key (default: MCP token session)"),
        what: z.string().optional().describe("checkpoint: what now holds"),
        verified_by: z.string().optional().describe("checkpoint: what verified it"),
        coverage: z.string().optional().describe(
          "checkpoint: coverage scope (count or named set)",
        ),
        question: z.string().optional().describe("open question text"),
        settled_by: z.string().optional().describe("cheapest test that could refute it"),
        next: z.string().optional().describe("open/next: single next action"),
      }),
    }
```

## memory_forget

Remove a memory. Prefer path or docid for precise deletion. Query does fuzzy match (less safe).

```
z.object({
              query: z.string().optional().describe("fuzzy match"),
              path: z.string().optional().describe("exact path — safe"),
              docid: z.string().optional().describe("exact id — safe"),
              confirm: z.boolean().optional().default(true).describe("true deactivates; false previews"),
              vault: z.string().optional(),
            }),
    }
```

## working_context

Slice of memory_prepare (compatibility): stable facts + recent decisions/how-tos. Prefer memory_prepare.

```
z.object({
              format: z.enum(["markdown", "json"]).optional().default("markdown"),
              vault: z.string().optional(),
            }),
    }
```

## get

Read a document by path or docid, with optional line range (fromLine/maxLines for a snippet).

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

Declare which memories you actually used BEFORE the final answer: docids ('#ab12cd') or paths — the COMPLETE working set; [] = empty. Declared use, not proof of causality.

```
z.object({
              // FB-0143: an explicit empty array is a legitimate
              // empty-working-set declaration, with or without a receipt —
              // it records no usage event. Some MCP clients (kiro-cli 2.20)
              // drop an empty array from the arguments before sending, so an
              // omitted docids also counts as [] when a receipt is present.
              // Omitted without a receipt is still rejected by the refine below.
              docids: z
                .array(z.string())
                .min(0)
                .optional()
                .describe("Docids or paths used; [] = empty working set"),
              verdict: z
                .enum(["confirmed", "corrected"], { error: "verdict must be 'confirmed' or 'corrected'" })
                .optional()
                .describe("User confirmed or corrected the memory"),
              outcome: z
                .enum(["success", "failure", "partial"], { error: "outcome must be 'success', 'failure' or 'partial'" })
                .optional()
                .describe("Did acting on these memories work"),
              query: z
                .string()
                .max(2000)
                .optional(),
              note: z.string().optional(),
              receipt: ContributionReceiptRequestSchema.optional(),
              saved_tokens: z.number().int().min(1).max(100_000_000).optional(),
              waste_avoided: z.string().max(120).optional(),
              discounted: z.number().int().min(0).max(50).optional(),
              vault: z.string().optional(),
            }).refine((input) => input.docids !== undefined || input.receipt !== undefined,
              "docids is required (empty array allowed) unless receipt is requested"),
    }
```

## memory_grep

Regex search over raw memory text returning path + line — for EXACT things (value, key, id, date), unlike memory_retrieve's similarity. Postgres ARE syntax: \\d, \\y and classes work; lookahead does not.

```
z.object({
              pattern: z.string().describe("Regex (Postgres ARE)"),
              collection: z.string().optional(),
              since: z.string().optional(),
              path: z.string().optional(),
              docid: z.string().optional(),
              timeout_ms: z.number().optional().describe("Scan cap ms (1000-30000)"),
              context: z
                .boolean()
                .optional(),
              case_sensitive: z.boolean().optional(),
              limit: z.number().optional().describe("Max lines (default 40, max 200)"),
              doc_limit: z.number().optional(),
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

Explain why a KG fact holds: Datalog proof tree for inferred facts, absent when the triple is not in the caller's tenant graph, unverified when the triple exists without a recorded derivation (runtime-derived facts on the current pg_ripple) or without an extraction-mirror entry. Pass entity names/IDs for subject and object (or object_literal for literal facts).

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

Curate a memory's surfacing: pin (+0.3 boost), unpin, snooze (hide N days, default 30), unsnooze. Target by docid, path, or query.

```
z.object({
              action: z.enum(["pin", "unpin", "snooze", "unsnooze"]),
              query: z.string().optional().describe("Path or search query (required if no docid)"),
              docid: z.string().optional().describe("Doc id (#abc123); takes precedence"),
              until: z.string().optional().describe("snooze: ISO date (default 30 days)"),
              vault: z.string().optional(),
            }),
    }
```

## lifecycle_status

Show document lifecycle statistics: active, archived, forgotten, pinned, snoozed counts and policy summary. Also lists the pin/snooze CANDIDATES with docid/path and metrics (FB-0028) so they can be acted on with memory_curate.

```
z.object({
              vault: z.string().optional().describe("Named vault (omit for default vault)"),
              candidates_limit: z.number().optional().default(10).describe("how many pin/snooze candidates to list (0 = counts only, max 100)"),
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

## entity_cards

Stable identity cards for the tenant + alias curation: alias_propose suggests merging same-thing names; alias_merge merges (tenant decision); alias_reject records NOT-same.

```
z.object({
              action: z.enum(["list", "alias_propose", "alias_merge", "alias_reject"]).optional().default("list"),
              limit: z.number().optional().default(50),
              offset: z.number().optional().default(0),
              entity_type: z.string().optional().describe("list: person|org|project|service|tool|concept|product|agent|location"),
              min_mentions: z.number().optional(),
              max_mentions: z.number().optional(),
              name_contains: z.string().optional(),
              quarantined: z.enum(["exclude", "include", "only"]).optional().default("exclude"),
              canonical: z.string().optional().describe("alias_merge: name that stays"),
              alias: z.string().optional().describe("alias_merge/reject: name that becomes the alias (comma list ok)"),
              longo: z.string().optional().describe("alias_reject: rejected candidate (omit = reject short name)"),
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

Bounded dialogue episodes (MemCell summaries). list shows recent episodes (optionally by user); get fetches by UUID.

```
z.object({
              action: z.enum(["list", "get"]),
              limit: z.number().optional().default(20),
              user_id: z.string().optional(),
              episode_id: z.string().optional().describe("get: episode UUID"),
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

THE entry point — call FIRST at session start and before acting on assumptions. Returns identity, task state (goals/ledger/progress), what changed, notifications, and relevant memory. First session call carries the versioned guide.

```
z.object({
              // FB-0162: memory_retrieve uses `query`. An agent that reaches
              // for memory_prepare with the same vocabulary should not have to
              // rediscover `message`. Accept `query` as an alias; require one.
              message: z.string().optional().describe("User message to prepare context for"),
              query: z.string().optional(),
              surface_id: z.string().optional(),
              collection: z.string().optional(),
              episode_id: z.string().optional(),
              recall_budget: z.number().optional().default(600),
              fast_mode: z.boolean().optional().default(false).describe(
                "Skip funnel retrieval; recall still covers docs by category."
              ),
              vault: z.string().optional(),
            }).refine((v) => Boolean((v.message ?? v.query ?? "").trim()), {
              message: "memory_prepare requires `message` (or the `query` alias)",
            }),
    }
```

## record_lesson

Record or verify a procedural lesson; dedupes on surface_id+content; verify=true bumps follow-through. approve_lesson_id approves a pending candidate; content refines it. retire_lesson_id retires a lesson (invalidated/superseded/archived).

```
z.object({
              surface_id: z.string().describe("Target surface"),
              content: z.string().describe("What to do / avoid"),
              evidence: z.string().optional(),
              episode_id: z.string().optional(),
              verify: z.boolean().optional().default(false),
              approve_lesson_id: z.string().optional().describe("Approve pending candidate; content refines text"),
              retire_lesson_id: z.string().optional().describe("Retire a lesson by id instead of recording (sets status invalidated/superseded/archived)"),
              retire_status: z.enum(["invalidated", "superseded", "archived"]).optional(),
              retire_reason: z.string().optional(),
              vault: z.string().optional(),
            }),
    }
```

## list_lessons

List procedural lessons for the tenant, filtered by surface or min follow-through score. Defaults to ACTIVE; status="pending" triages outcome=failure candidates.

```
z.object({
              surface_id: z.string().optional(),
              min_score: z.number().optional().describe("Minimum follow_through_score (0–1)"),
              status: z.enum(["pending", "active", "superseded", "invalidated", "archived"]).optional(),
              since: z.string().optional(),
              until: z.string().optional(),
              content_chars: z.number().optional().default(0).describe("Truncate content/evidence to N chars (0 = full)"),
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
              keys: z.array(z.string()).optional(),
              vault: z.string().optional(),
            }),
    }
```

## upsert_keyed_fact

Insert/update a temporal keyed fact snapshot (tenant, key, as_of unique). Weaker caller over a protected winner → pending proposal.

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

Correct a wrong/stale memory: persists the right value as an authority-keyed fact, supersedes prior values, soft-hides prose asserting the old value (scope='tenant' = opt-in sweep; dry_run previews; >25 held until confirm_prose_demotion). Authority follows the speaker: a token bound to a user carries that user's voice — when the human states a fact through you, claim it with authority='human' (transport identity ≠ authorship); userless tokens are capped at 'agent'.

```
z.object({
              fact_key: z.string(),
              fact_value: z.string(),
              as_of: z.string().describe("YYYY-MM-DD"),
              authority: z
                .enum(["human", "designated", "agent", "import"])
                .describe("human > designated > import > agent — claim 'human' only when the human stated the fact through you (your token carries their identity); otherwise 'agent'"),
              confirmed_by_user: z.boolean().optional(),
              evidence: z.string().optional(),
              losing_values: z
                .array(z.string())
                .optional()
                .describe("Wrong prior values to demote in prose"),
              losing_values_scope: z
                .enum(["fact_key", "tenant"])
                .optional()
                .describe("fact_key (default): docs also mentioning the key's entity; tenant: sweep, explicit opt-in."),
              dry_run: z
                .boolean()
                .optional()
                .describe("Preview only"),
              confirm_prose_demotion: z
                .boolean()
                .optional()
                .describe("Proceed with held preview (>25 docs)"),
              vault: z.string().optional(),
            }),
    }
```

## authority_restore_demotion

Undo one authority correction's prose demotion: restores confidences, un-hides docs, cancels pending work. Identify by demotion_work_id or fact_key; keyed fact untouched.

```
z.object({
        demotion_work_id: z.string().uuid().optional().describe("Work id from assert_authority_correction"),
        fact_key: z.string().optional().describe("Restore every doc demoted for this key"),
        confirm: z.boolean().optional().describe("Required when winner has human/designated authority"),
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

## diary

The agent's observational diary. WRITE events/decisions worth reviewing later (become searchable memories); READ recent entries.

```
z.object({
              action: z.enum(["read", "write"]),
              entry: z.string().optional().describe("write: entry text"),
              topic: z.string().optional().describe("write: topic tag"),
              agent: z.string().optional().describe("write: agent name; read: filter"),
              last_n: z.number().optional().describe("read: recent entries (default 10)"),
              vault: z.string().optional(),
            }),
    }
```

## whoami

Returns who THIS MCP connection is: tenant, user, agent slug, team member, identity summary.

```
z.object({}),
      }
```

## memory_health

Returns open proposal/conflict counts, high-priority items, and canonical sources with drift. Call at end of sessions.

```
z.object({
                  entity: z.string().optional(),
                  limit: z.number().optional(),
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

ValorBrain product-team channel (not end-user CRM). submit → FB-XXXX; check by id/'all'; respond writes ON the ticket (never your own platform's). No secrets.

```
z.object({
              action: z.enum(["submit", "check", "respond"]),
              title: z.string().min(5).max(200).optional(),
              description: z.string().min(10).max(5000).optional().describe("submit: what happened/expected/steps, or the ask"),
              response: z.string().min(10).max(5000).optional(),
              status: z.enum(["acknowledged", "in_progress", "resolved"]).optional(),
              category: z.enum(["bug", "feature", "question", "improvement", "praise", "feedback"]).optional().default("feedback"),
              priority: z.enum(["low", "normal", "high", "critical"]).optional().default("normal"),
              tags: z.array(z.string()).optional(),
              feedback_id: z.string().optional().describe("check/respond: FB-XXXX; check also 'all'"),
              vault: z.string().optional(),
            }),
    }
```

## feedback_submit

DEPRECATED — use feedback (actions submit/check/respond), the canonical product channel. One FB per distinct issue; no secrets.

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

## secrets

Cofre de segredos do tenant: a memória guarda só a referência `secret://<nome>`; o valor mora aqui e só sai por get (auditado). put cria/atualiza — inline (`value`) só para credencial que o usuário acabou de falar; máquina usa `from_env`/`from_file` (VAL-309: valor não transita a chamada). get resolve o valor e aceita nome aproximado em linguagem natural; list só metadados; rotate re-embrulha a chave; delete remove. Use: falou credencial → put (nome curto e estável); perguntou → get. Nunca escreva o valor em memória. Escopos: 'secrets:read' (get/list) / 'secrets:write' (put/rotate/delete); 'read'/'write' legados não cobrem. Nunca entra em retrieval.

```
z.object({
        action: z.enum(["put", "get", "list", "rotate", "delete"]).describe("Cofre: verbo"),
        name: z.string().optional().describe("put/get/delete: nome do segredo (vira secret://<nome>)"),
        value: z.string().optional().describe("put inline: valor — nunca devolvido por list. PREFIRA from_env/from_file (VAL-309): inline vaza no transcript"),
        from_env: z.string().optional().describe("put por referência (VAL-309): var VALORBRAIN_SECRET_IN_<NOME> do processo do MCP — valor não transita a chamada"),
        from_file: z.string().optional().describe("put por referência (VAL-309): basename no staging (/etc/valorbrain/secret-staging) — valor não transita a chamada"),
        description: z.string().optional().describe("put: para que serve"),
        expires_at: z.string().optional().describe("put: validade ISO (opcional)"),
        vault: z.string().optional(),
      }),
    }
```

## mental_models

Standing answer for a recurring question: memory_prepare serves it via SELECT (no LLM); consolidation tick rewrites it when scoped memory changes (flag mental_models, default off). create needs question + scope_json ({collections?: string[]}; {} = whole tenant).

```
z.object({
        action: z.enum(["list", "create", "update", "remove", "refresh"]),
        id: z.string().optional().describe("update/remove/refresh: model id"),
        question: z.string().optional().describe("create: recurring question; update: new question"),
        scope_json: z.record(z.string(), z.unknown()).optional().describe("{collections?: string[]} prefix filter; {} = whole tenant"),
        status: z.enum(["active", "paused"]).optional().describe("update: pause/resume"),
        settings: z.record(z.string(), z.unknown()).optional(),
      }),
    }
```

## acl_me

Your effective source-ACL domains (user+role+agent grants, with source/reason/validity) plus hidden-documents count. Missing domain can be permission, not a ranking miss.

```
z.object({}),
    }
```

## acl_grants

Administra os grants ALLOW do source ACL do tenant (user|role|agent → domínio de negócio, com validade temporal). list devolve grants + mapeamentos collection→domain (coleção sem mapeamento está FORA do regime — sempre legível); create exige reason (todo grant precisa dizer por quê) e aceita valid_from/valid_to ISO; revoke remove por id. Criar/revogar limpa o cache de resolução (60s) — vale no próximo request — e grava no mutation_audit. Exige escopo 'acl_grants:read' (list) ou 'acl_grants:write' (create/revoke) — legado read/write e token sem escopo não cobrem. Espelho REST: GET/POST/DELETE /api/v1/acl/grants (ADMIN do tenant).

```
z.object({
        action: z.enum(["list", "create", "revoke"]).describe("Acl grants: verbo"),
        subject_kind: z.enum(["user", "role", "agent"]).optional().describe("create: tipo do sujeito"),
        subject_id: z.string().optional().describe("create: users.id (UUID) | 'STAFF' | persona slug"),
        domain: z.string().optional().describe("create/list: domínio de negócio ('gtm', 'finance'…)"),
        reason: z.string().optional().describe("create: OBRIGATÓRIO — por que este acesso existe"),
        valid_from: z.string().optional().describe("create: ISO timestamp (opcional)"),
        valid_to: z.string().optional().describe("create: ISO timestamp (opcional)"),
        id: z.string().optional().describe("revoke: id do grant (UUID)"),
        vault: z.string().optional(),
      }),
    }
```

## read_log

Trilha de leitura do tenant (governança): quem leu, por meio de qual agente/canal, qual versão de cada documento entrou no contexto e quando. 1 linha por consulta; query é gravada como hash (nunca texto — LGPD); retenção 365 dias quentes + agregado. Filtros: doc (hash, prefixo ok), actor (user id), channel (mcp|rest|hook), operation, from/to ISO, limit (<=200). Toda consulta a esta trilha é registrada em mutation_audit (read_log.query). Exige escopo explícito 'read_log:read' — legado read/write e token sem escopo não cobrem. Espelho REST: GET /api/v1/read-log.

```
z.object({
        doc: z.string().optional().describe("Filtrar por hash de documento (prefixo ok) — 'quem leu ESTE documento'"),
        actor: z.string().optional().describe("Filtrar por user id do titular — 'o que ESTA pessoa leu'"),
        channel: z.enum(["mcp", "rest", "hook", "cli"]).optional().describe("Filtrar por canal"),
        operation: z.string().optional().describe("Filtrar por operação (ex.: memory_retrieve, 'POST /search', 'hook:context-surfacing')"),
        from: z.string().optional().describe("ISO timestamp inicial (inclusive)"),
        to: z.string().optional().describe("ISO timestamp final (inclusive)"),
        limit: z.number().optional().describe("Máximo de linhas (default 50, teto 200)"),
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

Your notification inbox (feedback responses, announcements, alerts) — only notices to you or broadcast. check: unread count + items; mark_read: by id or 'all'.

```
z.object({
              action: z.enum(["check", "mark_read"]),
              filter: z.string().optional().describe("check: 'unread' (default), 'all', or ID (N-XXXX)"),
              notification_id: z.string().optional().describe("mark_read: ID (N-XXXX) or 'all'"),
              vault: z.string().optional(),
            }),
    }
```

## team_message

Send an async message to a teammate (human or agent); they see it on their next briefing/inbox check.

```
z.object({
              to: z.string().describe("Recipient: teammate name or member id"),
              title: z.string().min(3).max(200),
              body: z.string().optional(),
              category: z.enum(["message", "request", "decision", "alert"]).default("message").describe("message = chat; request = asks action; decision = records a choice; alert = needs attention"),
              priority: z.enum(["low", "normal", "high", "critical"]).default("normal"),
              vault: z.string().optional(),
            }),
    }
```

## team_handoff

Durable async work assignment. create assigns work to a teammate with context (in their briefing until consumed; blocked_on_human parks it on a human). consume marks it done or closed.

```
z.object({
              action: z.enum(["create", "consume"]).optional().default("create"),
              to: z.string().optional().describe("recipient name or id"),
              summary: z.string().min(5).max(500).optional().describe("what needs doing"),
              open_questions: z.array(z.string()).optional(),
              files_changed: z.array(z.string()).optional(),
              priority: z.enum(["low", "normal", "high", "critical"]).optional().default("normal"),
              status: z.enum(["pending", "blocked_on_human"]).optional().default("pending")
                .describe("pending=actionable; blocked_on_human=parked on human"),
              handoff_id: z.union([z.string(), z.number()]).optional().describe("consume: handoff #id"),
              note: z.string().max(500).optional().describe("consume: completion note"),
              vault: z.string().optional(),
            }),
    }
```

## team_inbox

Check messages sent to you by teammates; returns unread count and recent messages.

```
z.object({
              unread_only: z.boolean().default(true).describe("If false, include already-read messages"),
              vault: z.string().optional(),
            }),
    }
```

## team_briefing

Slice of memory_prepare (compatibility): unread inbox, pending handoffs, team mission, recent activity.

```
z.object({
              vault: z.string().optional(),
            }),
    }
```

## team_roster

List the team (humans and agents), roles, and how to reach them.

```
z.object({
              vault: z.string().optional(),
            }),
    }
```

## team_notify_human

Pull a human teammate into the conversation NOW via their messaging channel. For decisions/approvals only a human can make. 'manager'/'lead'/'human' match any human.

```
z.object({
              to: z.string().describe("Name, role, or 'manager'/'lead'/'human'"),
              title: z.string().min(3).max(200).describe("What you need"),
              body: z.string().optional(),
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
        source_doc_ids: z.array(z.string()).optional().describe("record: document refs that informed this decision — UUID, #docid, or collection/path; each must resolve to an active document of the tenant, else nothing is recorded"),
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
        source_doc_ids: z.array(z.string()).optional().describe("Document refs that informed this decision — UUID, #docid, or collection/path; each must resolve to an active document of the tenant, else nothing is recorded"),
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

W3C PROV-O lineage of an entity. trace walks parent/used edges — where a fact came from (upstream) and what depends on it (downstream); export emits the full audit trail as RDF Turtle (default) or JSON-LD (format=jsonld) with hash-chain integrity metadata (regulator-ready).

```
z.object({
        action: z.enum(["trace", "export"]).describe("Provenance verb"),
        entity_id: z.string().describe("The entity (document hash, triple ID, keyed_fact key)"),
        format: z.enum(["turtle", "jsonld"]).optional().default("turtle").describe("export only: serialization — turtle (default) or jsonld (W3C PROV-O JSON-LD, parseable by standard PROV/JSON-LD tooling)"),
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
        apply_canonical: z.boolean().optional().describe("resolve: apply a verified human decision to the canonical fact atomically"),
        expected_revision: z.string().optional().describe("resolve: revision returned by conflicts list"),
        as_of: z.string().optional().describe("resolve: effective date YYYY-MM-DD for canonical correction"),
        human_confirmation: z.string().optional().describe("resolve: class-A act-bound envelope supplied by an enrolled harness; never invent this proof"),
        confirmed_by_user: z.boolean().optional().describe("resolve: true only when the current authenticated human explicitly chose this value; makes canonical application the default"),
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
        apply_canonical: z.boolean().optional(),
        expected_revision: z.string().optional(),
        as_of: z.string().optional(),
        human_confirmation: z.string().optional(),
        confirmed_by_user: z.boolean().optional(),
      }),
    }
```
