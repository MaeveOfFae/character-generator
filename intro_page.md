---
name: Intro Page
description: Generate a character intro page with Markdown.
invokable: true
always: false
version: 3.1
---

# Intro Page

Use this blueprint to produce a single Markdown snippet with self-contained styling. Keep the layout lean and replace every placeholder with character-specific text. No external assets;

Version note: version tracks the format spec for this blueprint (not a bundle version).

Rules:

- Replace every `{PLACEHOLDER}` token with concrete values; do not leave any `{PLACEHOLDER}` tokens in the final output.
- Hard ban: never emit any example or prior character names (e.g., seed/test names) when generating a new character.
- Safety: do not narrate user thoughts, actions, decisions, or consent; frame the user as an observer, not an actor.
- Respect the orchestrator content mode when present (SFW/NSFW/Platform-Safe); if SFW/Platform-Safe, avoid explicit sexual content.

---

```markdown
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
