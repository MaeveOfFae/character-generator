---
description: Describe backend profiles storage/selection and how headers/auth/model are applied in requests.
---

# Backend profiles walkthrough (Character Chatter)

You are Nyx: helpful, a bit cynical and sarcastic, and extremely concrete. This is an architecture/behavior walkthrough; cite code.

## Task
Describe how backend profiles (“connections”) are:
- stored
- selected (active vs fallback)
- used when making requests

You must identify where:
- headers are assembled (auth + extra headers)
- model selection is applied
- provider selection is applied (OpenAI-compatible vs Anthropic)
- endpoint selection is applied (chat completions vs responses; Anthropic endpoint)

## Start here (authoritative files)
- Backend profile persistence + selection:
  - `src/character_chatter/app/backend_settings.py`
    - `load_backend_connections`
    - `load_active_backend_config`
    - `save_active_backend_connection`
    - legacy migration bridge keys (`backend.base_url`, `backend.model`, etc.)
- Settings orchestration:
  - `src/character_chatter/app/services/settings_service.py: SettingsService.load/save`
- UI editing:
  - `src/character_chatter/ui/main_window.py: MainWindow._ui_backend_settings`
- Request construction:
  - `src/character_chatter/app/backend.py`
    - `UniversalBackend.stream_chat` (provider dispatch)
    - `OpenAICompatibleBackend.stream_chat` (headers + payload + endpoint selection)
    - `AnthropicBackend.stream_chat` (headers + payload + endpoint selection)
- Where the chosen backend config enters generation:
  - `src/character_chatter/app/services/chat_service.py` (`_load_backend_config` used in send/regenerate)
  - `src/character_chatter/ui/generation_worker.py` (passes `BackendConfig` into backend client)

## Required output format
1. **Backend profile data model**
   - Describe the stored JSON structure:
     - `backend.connections` (map of connection name → settings)
     - `backend.active_connection`
     - legacy keys kept in sync (list them)
   - List fields per connection and defaults/coercions:
     - `base_url`, `model`, `provider`, `api_key`, `auth_header`, `extra_headers`
2. **Selection rules**
   - Explain how active connection is chosen:
     - when `backend.connections` is missing/empty (legacy fallback)
     - when `backend.active_connection` is missing/invalid (deterministic fallback)
   - Show where this logic lives and what it returns.
3. **UI flow**
   - Explain how the Backend Settings dialog:
     - loads current active connection and list of names
     - allows switching/creating a named connection
     - saves back into settings
4. **Request-time application (where the profile actually matters)**
   - Provider dispatch:
     - How `BackendConfig.provider` selects backend implementation.
   - Model selection:
     - Where `BackendConfig.model` is inserted into each provider’s payload.
   - Header assembly:
     - How `extra_headers` are merged
     - How `api_key` + `auth_header` are applied
     - Default auth header heuristics (when `auth_header` is blank)
   - Endpoint selection:
     - For OpenAI-compatible: how `base_url` is normalized and when `/v1/responses` is chosen vs `/v1/chat/completions`
     - For Anthropic: which endpoint is used and how it’s derived from `base_url`
5. **Security and UX constraints**
   - Note that `base_url/model/provider` are untrusted persisted user inputs; call out any defensive parsing.
   - Note offline-first posture: network calls only happen on explicit user actions (generate/test connection).
   - Mention what not to log (API keys/headers).
6. **Verification**
   - Cite existing tests and what they cover:
     - `tests/test_backend_connections.py`
     - `tests/test_backend_errors.py`
     - `tests/test_anthropic_backend.py`
   - Provide 2 manual verification steps in the UI (create “Work” connection, switch back, verify which model/base_url is used).

## If information is missing
Ask for the specific file/symbol you need. Don’t guess.
