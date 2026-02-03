# Character Generator (Blueprint Pack)

This folder is a set of prompt blueprints for compiling a single **SEED** into a consistent suite of character assets for roleplay tooling (RPBotGenerator/Chub-style setups), plus optional A1111 and Suno prompts.

## Quick Start

### Option 1: Terminal UI (Recommended)

Install and launch the interactive TUI:

```bash
# Using the provided launcher (recommended - auto-creates venv)
./run_bpui.sh

# Or install manually in the existing venv
source .venv/bin/activate
pip install litellm  # optional, for 100+ providers
bpui
```

**New in TUI**: Provider-specific API key management - store keys for OpenAI, Anthropic, DeepSeek, Google, etc. directly in Settings. The system automatically selects the right key based on your model choice.

See [bpui/README.md](bpui/README.md) for full TUI documentation.

### Option 2: Direct LLM invocation

1. Pick a SEED (see examples below)
2. Invoke the orchestrator (`blueprints/rpbotgenerator.md`) with the SEED
3. Parse the 7-codeblock output
4. Export using `tools/export_character.sh`

## Files (what each blueprint produces)

All blueprints are in the `blueprints/` folder:

- `blueprints/rpbotgenerator.md`: Orchestrator spec that coordinates all outputs from one SEED.
- `blueprints/system_prompt.md`: Character system prompt (≤300 tokens, paragraph-only).
- `blueprints/post_history.md`: Post-history behavior layer (≤300 tokens, paragraph-only).
- `blueprints/character_sheet.md`: Structured character sheet (blueprint fields + lists).
- `blueprints/intro_scene.md`: Second-person intro scene (ends with an open loop to {{user}}).
- `blueprints/intro_page.md`: Markdown intro page (platform-agnostic; no HTML/CSS).
- `blueprints/a1111.md`: Modular A1111 image prompt layout.
- `blueprints/a1111_sdxl_comfyui.md`: SDXL-first alternate image prompt layout (AUTOMATIC1111 + ComfyUI).
- `blueprints/suno.md`: Suno V5 song prompt layout.
- `blueprints/chub_rules.md`: Reference notes about Chub AI character fields and macros.

## Minimal workflow

1) Pick a SEED that implies:
   - a power dynamic,
   - an emotional temperature,
   - a tension axis.
   - why {{user}} matters (relationship/connection), without narrating {{user}} actions

2) Invoke the orchestrator (`blueprints/rpbotgenerator.md`) with the SEED.

3) Paste each generated asset into the relevant destination (system prompt, post history, greeting/scene, intro page markdown, etc.).

## Seed generation (seed lists)

- Use `seed-gen` as a seed-list prompt blueprint, then save the resulting seed lists into `seed output/` (no headings/numbering; seeds only).
- If you want wilder/high-concept seeds, tag for it explicitly (e.g., `high-concept`, `surreal`, `absurd`). Otherwise `seed-gen` defaults to grounded, human-scale premises.
- Seeds may reference `{{user}}` only as a relationship/connection anchor (role, leverage, dependency, obligation); do not assert `{{user}}` actions, choices, dialogue, thoughts, emotions, sensations, or consent.
- Moreau support: use tags like `moreau` / `anthro` / `scalie` / `draconic` and optionally `morphosis` / `morpho` / `beastcore` to generate lore-aware seeds (see `main_Moreau Virus_Morphosis combo book_world_info.json`).

## Content mode (SFW/NSFW/Platform-Safe)

The orchestrator supports an optional content mode. If you care about output boundaries, include the mode in your request and keep it consistent across all assets.

## Adjustment Note

If the seed is thin or a constraint must be bent, the orchestrator may emit a first “Adjustment Note” codeblock with one line describing the adjustment. All assets remain clean in their own codeblocks/files.

## Export helper

- `tools/export_character.sh` can export from files: `./tools/export_character.sh "character_name" "source_dir" [llm_model]`

### Export contract (expected filenames)

When exporting from files, `source_dir/` is expected to contain:

- `system_prompt.txt`
- `post_history.txt`
- `character_sheet.txt`
- `intro_scene.txt`
- `intro_page.md`
- `a1111_prompt.txt`
- `suno_prompt.txt`

Optional alternate image prompt:

- `a1111_sdxl_prompt.txt`

## SEED examples

- “Strict museum curator who hates being noticed, but can’t stop watching {{user}}”
- “Street medic with a savior complex, protective toward {{user}}, terrified of abandonment”
- “Corporate fixer: polite menace, offers {{user}} a deal they can’t afford to accept”

## Genre quickstart

## Genre Quickstart — Expanded & Complete

This document defines **genre as operational physics**, not vibes.  
Each genre specifies defaults for pacing, power, sensory focus, dialogue, and common failure modes.  
Global rules at the end prevent tone drift and narrative amnesia.

---

## Core Genre Presets

### Romance / Slice-of-Life

- **Pacing:** Slow ramps; micro-beats over plot turns. Routine and silence count as progress.
- **Power default:** Balanced or gently asymmetric; boundaries remain visible, even when unspoken.
- **Sensory:** Warm palettes; touch, fabric, domestic soundscapes (dishes, footsteps, breath).
- **Dialogue:** Indirect; emotionally dense subtext over explicit statements.
- **Failure mode:** Rushing intimacy; dissolving boundaries “because it’s cute.”

---

### Thriller / Noir

- **Pacing:** Constant forward pressure; every scene alters leverage.
- **Power default:** Asymmetric and unstable; someone always knows more.
- **Sensory:** Cold light, confined spaces, sharp edges, ticking clocks.
- **Dialogue:** Clipped, evasive; questions answered with half-truths.
- **Failure mode:** Over-explaining motives; softening consequences.

---

### Horror

- **Pacing:** Escalation through repetition + variation; delay the reveal.
- **Power default:** Biased *against* {{user}} unless explicitly subverted.
- **Sensory:** Sound, texture, bodily awareness; visuals arrive late.
- **Agency:** Vulnerability is the hook; survival ≠ control.
- **Failure mode:** Lore dumps; spectacle replacing dread.

---

### Fantasy

- **Pacing:** Episodic beats anchored to place, ritual, and consequence.
- **Power default:** Rule-bound; magic always costs something tangible.
- **Worldbuilding:** Concrete, tactile detail over mythic summaries.
- **Sensory:** Magic alters weight, smell, temperature, or sound.
- **Failure mode:** Abstract lore; soft magic solving problems cleanly.

---

### Sci-Fi / Cyberpunk

- **Pacing:** Brisk but fragmented; scenes feel transactional.
- **Power default:** Systems exert more pressure than individuals.
- **Tech:** Texture, interface friction, failure states—never lectures.
- **Aesthetic:** Neon vs shadow; noise vs silence; owned vs rented space.
- **Failure mode:** Tech fetishism; jargon replacing stakes.

---

### Comedy / Lighthearted

- **Pacing:** Rhythm-driven; timing matters more than volume.
- **Power default:** Flexible, but never consequence-free.
- **Structure:** Missteps create connection; escalation through callbacks.
- **Character:** Core flaw remains intact—humor exposes it.
- **Failure mode:** Joke density dissolving tension or character truth.

---

## Missing but Required Categories

### Drama (Stakes-First, Non-Genre)

- **Purpose:** Backbone for scenes driven by interpersonal pressure.
- **Pacing:** Tension via unresolved wants; scenes end emotionally incomplete.
- **Power default:** Relational leverage (history, obligation, guilt).
- **Dialogue:** What’s not said does the work.
- **Failure mode:** Melodrama; characters explaining feelings instead of acting.

---

### Mystery / Investigation

- **Purpose:** Control of knowledge, not danger.
- **Pacing:** Question → partial answer → better question.
- **Power default:** Whoever controls information controls the scene.
- **Structure:** Clues change interpretation, not just plot direction.
- **Failure mode:** Arbitrary withholding; reveals without prior affordance.

---

### Intimacy / Erotic Tension (Non-Explicit)

- **Purpose:** Charge management across multiple genres.
- **Pacing:** Proximity beats > action beats.
- **Power default:** Fluctuating; desire creates vulnerability.
- **Sensory:** Breath, heat, timing, interruption.
- **Failure mode:** Collapsing tension into payoff too early.

---

## Cross-Genre Structural Systems

### Conflict Resolution Modes

Every scene should resolve via **one primary mode**:

- **Deferral:** Nothing solved; pressure increases.
- **Exchange:** Something is traded (information, trust, access).
- **Loss:** Someone gives something up.
- **Revelation:** Context shifts; meaning changes.
- **Failure mode:** Tidy endings that reset stakes.

---

### Emotional Aftermath Handling

- **Rule:** Every high-intensity beat leaves residue.
- **Tools:** Behavioral callbacks (avoidance, awkwardness, guilt, relief).
- **Prohibition:** No emotional amnesia between scenes.
- **Failure mode:** Resetting characters to baseline.

---

### Stakes Without Plot

- **Applicable to:** Slice-of-life, romance, drama-heavy scenes.
- **Stakes types:** Social, emotional, reputational, temporal.
- **Rule:** If nothing can be lost, compress or cut the scene.
- **Failure mode:** Pleasant but inert moments.

---

### Tone Drift Safeguard (Global)

- **Rule:** Humor, warmth, or competence may *relieve* tension, never erase it.
- **Check:** What cost still exists after this beat?
- **Failure mode:** Vibes overpowering narrative logic.

---

## Optional Cross-Genre Switches

Use these to hybridize without losing coherence:

- **Escalation curve:** Slow burn / sawtooth / spike-and-release
- **Power bias:** Toward {{user}} / against {{user}} / oscillating
- **Boundary visibility:** Explicit / implicit / contested
- **Sensory lead:** Sound / touch / light / spatial constraint

---

## Design Principle (Non-Negotiable)

Genre is not flavor.  
It defines:

- how power flows,
- how information moves,
- how tension resolves,
- and how consequences linger.

If a scene violates its genre’s power or pacing rules, it will feel wrong regardless of prose quality.
