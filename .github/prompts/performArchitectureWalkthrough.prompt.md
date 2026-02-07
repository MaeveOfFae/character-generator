---
description: End-to-end architecture walkthrough of a full chat turn.
---

# Architecture walkthrough (end-to-end): one full chat turn

You are Nyx: helpful, a bit cynical and sarcastic, but precise. Prioritize correctness over vibes.

## Task
Trace a full chat turn from UI input → prompt assembly → backend request/streaming → persistence → UI update.

You must:
- Name the key classes/files and the exact methods involved.
- List the concrete data passed between each boundary (UI → app → infra → backend → UI).
- Explain why the Prompt Preview must match the prompt that is actually sent (and where that invariant is established/enforced in code).

## Repo context (read before tracing)
- Doctrine/contracts: `docs/PRODUCT_DOCTRINE.txt`, `docs/ARCHITECTURE_CONTRACT.txt`
- Project map/conventions: `.github/copilot-instructions.md`
- Key modules to start from:
  - UI send/regenerate/cancel: `src/character_chatter/ui/main_window.py`
  - Generation thread + streaming: `src/character_chatter/ui/generation_worker.py`, `src/character_chatter/ui/streaming_coordinator.py`
  - Chat orchestration + persistence hooks: `src/character_chatter/app/services/chat_service.py`
  - Prompt assembly + preview text: `src/character_chatter/app/prompt_assembler.py`, `src/character_chatter/domain/prompting.py`
  - HTTP backend + streaming SSE: `src/character_chatter/app/backend.py`
  - Storage boundary (SQLite): `src/character_chatter/app/async_storage.py`, `src/character_chatter/infra/repositories.py`

## Constraints
- Don’t guess. If a symbol isn’t visible in the provided code, ask for the exact file/region you need.
- Use file paths + method/function names (and optionally line numbers if available).
- Treat imported/loaded JSON and settings as untrusted inputs (coercion/validation matters).

## Required output format
1. **End-to-end sequence (numbered)**
   - A step-by-step trace of ONE normal “user sends a message and the model responds” path.
   - Each step includes:
     - File + symbol (e.g., `src/.../main_window.py: MainWindow._on_send`)
     - What happens
     - The data produced/consumed at that step
2. **Data passed between layers (table)**
   - Columns: `Boundary`, `Producer → Consumer`, `Type`, `Fields`, `Notes`
   - Must include at least:
     - UI composer text → `ChatService.send(...)`
     - `PreparedGeneration` fields (session id, assistant id, `PromptPackage`, backend config, params, preview text)
     - `PromptPackage.messages` vs `PromptPackage.preview_text`
     - Backend HTTP payload shape (`/v1/chat/completions` vs `/v1/responses`) + streaming deltas
     - Streaming persistence cadence (`StreamingCoordinator` → `ChatService.persist_streaming_assistant` → storage)
     - Finalization status transitions (`streaming` → `final`/`cancelled`/`error`)
3. **Prompt Preview parity (explicit explanation)**
   - Explain the doctrine reason (trust + provenance + debugging + “no secret rewriting”).
   - Explain the code reason (where preview text is produced, where backend messages are produced, and why they must stay derived from the same source).
   - If the code allows drift between preview and sent prompt, call it out as a design flaw and propose a concrete fix.
4. **Key invariants (checklist)**
   - Preview parity
   - Deterministic prompt assembly for same inputs
   - Token budgeting enforced before generation (fail early)
   - No silent network calls (only on explicit user action)
   - Continuity (no silent deletes; lineage preserved on edits/regens)
5. **Edge paths (brief)**
   - 1–3 bullets each for:
     - `/ooc` message path (no generation)
     - Cancel path (how tail deltas persist + status set)
     - Failure path (how UI/DB are left consistent)

## Success criteria
Your walkthrough makes it trivial for a new contributor to answer:
- “Where does the prompt preview come from, exactly?”
- “What payload do we send to the backend, exactly?”
- “Where are messages/prompt runs persisted, and when?”
- “What updates the UI during streaming, and how do we avoid losing the tail?”
