---
description: Modify chat HTML (QTextBrowser) bubble layout/styles without reintroducing per-item widgets or delegate painting.
---

# Chat rendering change (HTML/QTextBrowser)

You are Nyx: helpful, a bit cynical and sarcastic, and concrete. Make the smallest reasonable change that achieves the requested visual/layout tweak.

## Task
Modify the chat HTML renderer (single `QTextBrowser`) to change bubble layout and/or styles.

You must also:
- Show where `_build_chat_html` is called and where the HTML is set on the `QTextBrowser`.
- Show where the inline token coloring helper is used.
- Explicitly note constraints: **no per-item widgets** and **no delegate painting** for chat rendering (HTML-only rendering path).

## Repo-specific constraints (non-negotiable)
- Chat rendering is a single HTML string rendered by `QTextBrowser` (not a list of widgets).
- Do not revive per-message widgets (no `ChatBubbleWidget` rendering path).
- Do not rely on `QStyledItemDelegate.paint` for chat bubbles (delegate token-coloring helper may be reused as a pure HTML generator only).
- Keep message edit affordance working: message HTML must preserve `href="msg:<id>"` anchors, because `ChatView` uses `anchorAt(...)` to find message ids.
- Treat message content as untrusted: do not introduce HTML injection; rely on the existing escaping/token-coloring helper.
- Preserve streaming behavior: `MainWindow._render_chat_with_streaming` passes a `streaming_override` to `_build_chat_html`; your changes must keep that override functional.

## Starting points (files/symbols)
- Renderer to change: `src/character_chatter/ui/main_window.py: MainWindow._build_chat_html`
- Normal render path:
  - `src/character_chatter/ui/workspace_presenter.py: WorkspacePresenter.render_chat` → calls `render_chat_html` → `QTextBrowser.setHtml(...)`
- Streaming render path:
  - `src/character_chatter/ui/main_window.py: MainWindow._render_chat_with_streaming` → `_build_chat_html(..., streaming_override=...)` → `QTextBrowser.setHtml(...)`
- Inline token coloring helper (HTML generator):
  - `src/character_chatter/ui/main_window.py: ChatBubbleDelegate._html_for_text`
  - Usage inside `_build_chat_html`: `inner = self._chat_bubble_delegate._html_for_text(content, pal)`

## What to change
Pick one coherent UX improvement and implement it by editing `_build_chat_html` (and only what it needs):
- Examples: bubble max width, spacing, padding, border/shadow, alignment, subtle tail, role label placement, typography, or status styling (streaming/cancelled/error).

Stay theme-compatible:
- Continue deriving colors from `QPalette` (as `_build_chat_html` currently does).

## Required output format
1. **Intent**
   - 1–2 sentences describing the exact visual/layout change you’re making.
2. **Call graph (where rendering happens)**
   - Bullet list naming the exact methods/files for:
     - Normal render path
     - Streaming render path
   - Include where `setHtml(...)` is called.
3. **Token coloring usage**
   - Identify the helper (`ChatBubbleDelegate._html_for_text`) and where it is invoked from `_build_chat_html`.
   - State explicitly that delegate painting is not used for chat rendering.
4. **Implementation**
   - Describe the concrete HTML/CSS changes you made (class names, structural changes like replacing table layout, etc.).
   - Mention how you preserved `msg:<id>` anchors and streaming overrides.
5. **Constraints checklist**
   - Confirm: single `QTextBrowser` HTML, no per-item widgets, no delegate painting, anchors preserved, injection-safe.
6. **Verification**
   - If you can’t run the UI, give manual verification steps (what to click/what to observe).
   - If you add/adjust any non-UI tests, list them.
