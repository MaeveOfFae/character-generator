---
name: Suno (Simplified)
description: Generate Suno V5 music prompt for character theme.
invokable: true
version: 1.0
---

# Blueprint Agent

Generate a complete Suno V5 song prompt using the full Control block structure.

**CRITICAL:** You MUST output the COMPLETE [Control] block with ALL metadata lines. Do NOT simplify to basic lyrics.

**Rules:**
- Include EVERY [Control] metadata line
- Use proper section headers: [Verse], [Chorus], [Pre-Chorus], [Bridge], [Intro], [Outro]
- NO {TITLE} or other placeholders unfilled
- Match song emotion to character's emotional signature
- Choose clear structure (e.g., VCVC, VCVCBC, IVCVCO)
- Output in single plaintext code block

----------

**SUNO V5 PROMPT TEMPLATE**

----------

```plaintext
[Control]
[Title: {TITLE}]
[Genre: {GENRE}]
[Style: {STYLE}]
[Mood: {MOOD}]
[Energy: {ENERGY}]
[Tempo: {TEMPO}]
[BPM: {BPM}]
[Texture: {TEXTURE}]
[Instrument: {INSTRUMENT 1}]
[Instrument: {INSTRUMENT 2}]
[Instrument: {INSTRUMENT 3}]
[Vocal Type: {Vocal Type}]
[Vocal Tone: {Vocal Tone}]
[Vocal Style: {Vocal Style}]
[Vocal Effect: {Vocal Effect}]
[Loop-Friendly]
[Crop/Fade]
[Remaster: {Remaster Style}]
[Note] {Brief description of song's emotional intent}

[Voice: Lead | Primary | Center Mix | Clean–Distorted Power]
[Voice: Choir | Background | Wide Reverb | Stereo Spread]

{Include song structure and lyrics here}

Choose structure like:
[Intro]
{Intro lyrics/instrumentation}

[Verse]
{Verse 1 lyrics}

[Chorus]
{Chorus lyrics}

[Verse]
{Verse 2 lyrics}

[Chorus]
{Chorus lyrics}

[Bridge]
{Bridge lyrics}

[Chorus]
{Final chorus}

[Outro]
{Outro}
```

**Lyric Guidelines:**
- Concrete imagery over abstraction
- Match emotional core from character sheet
- Repetition builds weight (not filler)
- Verses: restrained, specific
- Chorus: expansive, emotionally direct
- Bridge: destabilizing or revelatory
- Feel complete and intentional
