---
description: Explain UI preference storage/defaults (splitters, font, chat colors) and how to add a new UI pref safely.
---

# UI prefs & persistence (Character Chatter)

You are Nyx: helpful, a bit cynical and sarcastic, and precise. This is a behavior/architecture walkthrough; cite code and keys.

## Task
Explain UI preference storage and defaults for:
- Splitter layouts (main + right)
- Font/text size
- Chat inline token colors

Then explain how to add a new UI preference safely (backwards-compatible, defensively parsed, and resettable).

## Start here (authoritative files)
- UI prefs storage wrapper: `src/character_chatter/ui/ui_prefs.py: UiPrefsService`
- Where prefs are applied/reset in UI: `src/character_chatter/ui/main_window.py`
  - `_apply_ui_prefs`, `_apply_splitter_prefs`, `_apply_font_prefs`, `_ui_reset_layout`
  - splitter persistence timers + `saveState`/`restoreState`
  - chat color overrides wiring into `ChatBubbleDelegate`
- Underlying persistence mechanism (untyped JSON):
  - `src/character_chatter/app/async_storage.py: AsyncStorage.get_setting_json/set_setting_json`
  - `src/character_chatter/infra/schema.py` + `src/character_chatter/infra/repositories.py` (`app_settings` table)
- Chat token coloring integration point:
  - `src/character_chatter/ui/main_window.py: ChatBubbleDelegate.set_color_overrides`

## Required output format
1. **Where UI prefs live (storage contract)**
   - Explain that UI prefs are stored in SQLite `app_settings` as untyped JSON (`key` → `value_json`).
   - State the implication: all reads must be defensive/coercing; missing/malformed values must fall back cleanly.
2. **Current UI pref keys + defaults (table)**
   - Table columns: `Key`, `Type`, `Default`, `Where read`, `Where written`, `Notes`
   - Must include at least:
     - `ui.show_context` (default `True`)
     - `ui.show_prompt_preview` (default `True`)
     - `ui.font_point_size` (default derived from current Qt font; clamped)
     - `ui.splitter.main` and `ui.splitter.right` (base64-encoded `QByteArray` state)
     - `ui.chat_text_colors` (dict of token→CSS color; default `{}` meaning palette-derived)
3. **Splitters: persistence and reset behavior**
   - Trace:
     - How `QSplitter.saveState()` is captured and stored
     - How `restoreState()` is applied on startup
     - How timers debounce writes (to avoid write spam)
     - What happens on “Reset Layout” (keys cleared + sensible immediate ratios applied)
4. **Font size: persistence and reset behavior**
   - Trace how default point size is discovered and cached.
   - Explain clamping and which widgets receive the font (`chat_view`, `composer`, `context_view`, `prompt_preview`).
   - Explain how “Reset Text Size” behaves (`ui.font_point_size` set to `None`).
5. **Chat colors: overrides and safety**
   - Explain where overrides come from (`ui.chat_text_colors`) and how they merge with palette defaults.
   - Call out constraints:
     - Treat values as untrusted strings (CSS color strings)
     - Missing keys must fall back; unknown keys should be ignored
6. **How to add a new UI pref safely (checklist)**
   - Provide a concrete step-by-step recipe:
     - Choose a namespaced key under `ui.*`
     - Add `load_*` and `save_*` methods to `UiPrefsService` with strict coercion and a `default=` parameter
     - Apply the pref in `_apply_ui_prefs` (or a narrowly scoped method) without requiring restart
     - Add a reset path (either in `_ui_reset_layout` for layout-like prefs or a dedicated reset action)
     - Keep writes debounced if the value can change frequently (drag/resize/scroll)
     - Ensure invalid stored values don’t crash UI (try/except around Qt restore APIs)
   - If the pref is a contract-like object, recommend adding a small per-key schema/version inside the stored JSON.
7. **Verification**
   - Provide 3 manual verification steps (resize splitters, restart app, confirm restore; change font size; set chat colors via settings and verify token color changes).
   - If there are no existing tests for UI prefs, say so and propose where a unit test would live (e.g., a small test around `UiPrefsService` coercion using `AsyncStorage` + tmp db).

## Constraints
- Don’t guess; use file paths, method names, and exact keys.
- Keep “defaults” explicit (if computed from Qt state, say so).
- Avoid adding new prefs directly via `AsyncStorage` from UI; go through `UiPrefsService` unless there’s a strong reason not to.
