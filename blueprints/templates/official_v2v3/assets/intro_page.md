---
name: Intro Page
description: Generate a character intro page with Markdown.
invokable: true
always: false
version: 3.1
---

# Intro Page

Use this blueprint to produce a single Markdown snippet. Keep the layout lean and replace every placeholder with character-specific text.

Version note: version tracks the format spec for this blueprint (not a bundle version).

**CRITICAL: ALL PLACEHOLDERS MUST BE REPLACED**

Rules:

- **Replace every `{PLACEHOLDER}` token with concrete values; do not leave any `{PLACEHOLDER}` tokens in the final output.**
- The output must be a complete, ready-to-use Markdown document with NO placeholders remaining.
- Hard ban: never emit any example or prior character names (e.g., seed/test names) when generating a new character.
- Safety: do not narrate user thoughts, actions, decisions, or consent; frame the user as an observer, not an actor.
- Respect the orchestrator content mode when present (SFW/NSFW/Platform-Safe); if SFW/Platform-Safe, avoid explicit sexual content.
- Output ONLY the finished intro page inside a single markdown code block.
- No commentary or explanations.

---

INTRO PAGE TEMPLATE

---

Follow this structure exactly:

```
# {CHARACTER NAME}

---

## {SHORT DESCRIPTION}

{DETAILED SHORT DESCRIPTION FROM CHARACTER'S PERSPECTIVE}

---

## Appearance

{DETAILED APPEARANCE DESCRIPTION FROM CHARACTER'S PERSPECTIVE}

---

## Personality

{DETAILED PERSONALITY DESCRIPTION FROM CHARACTER'S PERSPECTIVE}

---

## Background

{DETAILED BACKGROUND STORY THIRD-PERSON NARRATIVE}

---

## Goals and Motivations

{DETAILED GOALS AND MOTIVATIONS FROM CHARACTER'S PERSPECTIVE}

---

## Relationships

{DETAILED RELATIONSHIPS WITH OTHER CHARACTERS FROM CHARACTER'S PERSPECTIVE}
```

Replace all `{PLACEHOLDER}` tokens with actual content. Output the result inside a single markdown codeblock.
