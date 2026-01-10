---
name: Intro Page
description: Generate a character intro page with inline CSS.
invokable: true
always: false
version: 3.1
---

# Intro Page

Use this blueprint to produce a single HTML snippet with self-contained styling. Keep the layout lean and replace every placeholder with character-specific text. No external assets or external CSS; an embedded `<style>` tag is allowed when needed for maintainability (some platforms may strip it).

Version note: version tracks the format spec for this blueprint (not a bundle version).

Rules:

- Replace every `{PLACEHOLDER}` token with concrete values; do not leave any `{PLACEHOLDER}` tokens in the final output. (Do not remove normal HTML/CSS syntax braces.)
- Hard ban: never emit any example or prior character names (e.g., seed/test names) when generating a new character.
- Safety: do not narrate user thoughts, actions, decisions, or consent; frame the user as an observer, not an actor.
- Respect the orchestrator content mode when present (SFW/NSFW/Platform-Safe); if SFW/Platform-Safe, avoid explicit sexual content.

----------

BLUEPRINT

----------

```html
<div class="char-sheet {CLASS_NAME}" aria-label="{ARIA_LABEL}" style="--ink:{COLOR_INK};--flare:{COLOR_FLARE};--heat:{COLOR_HEAT};--glow:{COLOR_GLOW};--veil:{COLOR_VEIL};--muted:{COLOR_MUTED};--paper:{COLOR_PAPER};--grain:{COLOR_GRAIN};--edge:{COLOR_EDGE};--round:16px;--pad:14px;font-family:'Space Grotesk','Manrope','Archivo',system-ui,sans-serif;color:{COLOR_TEXT};max-width:1200px;margin:0 auto;padding:18px;border-radius:18px;border:1px solid var(--edge);background:radial-gradient(circle at 12% 6%,rgba(255,79,122,.12),transparent 36%),radial-gradient(circle at 82% 10%,rgba(99,224,255,.18),transparent 42%),linear-gradient(145deg,#0b0810,#0e0912 46%,#08060c);box-shadow:0 20px 68px rgba(0,0,0,.78),0 0 46px rgba(255,79,122,.32),0 0 32px rgba(99,224,255,.16);position:relative;overflow:hidden;isolation:isolate;"><style>.char-sheet *,.char-sheet *::before,.char-sheet *::after{box-sizing:border-box;} .char-sheet::before{content:"";position:absolute;inset:-18%;background:radial-gradient(circle at 32% 22%,rgba(255,79,122,.24),transparent 50%),radial-gradient(circle at 78% 12%,rgba(99,224,255,.18),transparent 46%),linear-gradient(115deg,rgba(255,255,255,.08),rgba(255,255,255,.02),rgba(255,255,255,.04));mix-blend-mode:screen;opacity:.42;pointer-events:none;} .char-grid{position:relative;z-index:1;display:grid;gap:16px;align-items:start;} .panel{position:relative;overflow:hidden;padding:var(--pad);border-radius:var(--round);border:1px solid var(--edge);background:linear-gradient(160deg,rgba(255,79,122,.16),rgba(15,10,19,.96)),radial-gradient(circle at 14% 12%,rgba(255,79,122,.18),transparent 34%),radial-gradient(circle at 86% 0%,rgba(99,224,255,.16),transparent 38%);box-shadow:0 22px 70px rgba(0,0,0,.8),0 0 28px rgba(255,79,122,.26),0 0 24px rgba(99,224,255,.18);} .panel::after{content:"";position:absolute;inset:-12%;background:radial-gradient(circle at 24% 18%,rgba(255,79,122,.1),transparent 42%),radial-gradient(circle at 70% 64%,rgba(99,224,255,.08),transparent 44%);mix-blend-mode:screen;opacity:.38;pointer-events:none;animation:floatGlow 9s ease-in-out infinite alternate;} .header{display:grid;gap:10px;} .eyebrow{letter-spacing:.24em;text-transform:uppercase;font-size:.72rem;color:var(--muted);} .title{font-size:clamp(1.9rem,4vw,2.8rem);letter-spacing:.22em;text-transform:uppercase;margin:0;color:#fff;display:flex;flex-wrap:wrap;gap:10px;align-items:center;} .title span.badge{padding:6px 10px;border-radius:999px;border:1px solid rgba(255,255,255,.2);background:linear-gradient(135deg,rgba(255,79,122,.22),rgba(99,224,255,.14));font-size:.8rem;letter-spacing:.1em;} .subtitle{margin:0;color:#ffeef8;font-style:italic;letter-spacing:.12em;text-transform:uppercase;} .swatches{display:flex;flex-wrap:wrap;gap:8px;} .swatch{display:inline-flex;align-items:center;gap:8px;padding:10px 12px;border-radius:12px;border:1px solid rgba(255,255,255,.14);background:linear-gradient(135deg,rgba(255,255,255,.08),rgba(255,255,255,.02));font-size:.9rem;letter-spacing:.06em;text-transform:uppercase;} .swatch::before{content:"";width:18px;height:18px;border-radius:6px;background:var(--swatch);box-shadow:0 0 12px rgba(255,255,255,.16);} .flex-split{display:grid;grid-template-columns:2fr 1fr;gap:14px;} @media(max-width:920px){.flex-split{grid-template-columns:1fr;}} .pulse-grid{column-count:3;column-gap:12px;} @media(max-width:1080px){.pulse-grid{column-count:2;}} @media(max-width:760px){.pulse-grid{column-count:1;}} .card{position:relative;display:flex;flex-direction:column;gap:8px;padding:12px;border-radius:12px;border:1px solid rgba(255,255,255,.16);background:linear-gradient(150deg,rgba(255,255,255,.08),rgba(255,255,255,.02));box-shadow:0 12px 30px rgba(0,0,0,.6);break-inside:avoid;page-break-inside:avoid;column-break-inside:avoid;width:100%;margin:0 0 12px;} .card h3{margin:0 0 6px;letter-spacing:.1em;text-transform:uppercase;font-size:.96rem;color:var(--flare);} .list{list-style:none!important;margin:0!important;padding:0!important;display:grid;gap:8px;} .char-sheet ul.list>li{all:unset;display:flex!important;align-items:flex-start;gap:8px!important;width:100%!important;padding:9px 10px!important;border-radius:10px!important;border:1px solid rgba(255,255,255,.12)!important;background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015))!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.08)!important;line-height:1.5!important;color:inherit!important;} .char-sheet ul.list>li strong{all:unset;font-weight:700!important;color:#fff!important;display:inline-block;} .statline{display:flex;align-items:center;gap:8px;letter-spacing:.08em;text-transform:uppercase;font-size:.85rem;color:var(--muted);} .statdot{width:8px;height:8px;border-radius:50%;background:var(--flare);box-shadow:0 0 10px rgba(255,79,122,.6);} .scene-block{display:grid;gap:8px;} .scene-title{font-size:.92rem;letter-spacing:.12em;text-transform:uppercase;color:#fff;margin:0;} .scene-copy{margin:0;color:var(--muted);line-height:1.55;} .chips{display:flex;flex-wrap:wrap;gap:8px;} .chip{padding:8px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.14);background:linear-gradient(135deg,rgba(255,79,122,.2),rgba(99,224,255,.08));letter-spacing:.08em;font-size:.82rem;text-transform:uppercase;color:#fff;} .voice{display:grid;gap:6px;} .quote{margin:0;padding:10px;border-radius:10px;border:1px solid rgba(255,255,255,.16);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.02));font-weight:700;color:#fff;letter-spacing:.02em;} .micro{column-count:2;column-gap:10px;} @media(max-width:920px){.micro{column-count:1;}} .micro .card{background:linear-gradient(150deg,rgba(99,224,255,.08),rgba(12,9,18,.96));border-color:rgba(99,224,255,.4);} .cta{display:flex;gap:10px;flex-wrap:wrap;} .cta a{display:inline-flex;align-items:center;gap:8px;padding:10px 12px;border-radius:999px;border:1px solid rgba(255,255,255,.2);text-decoration:none;letter-spacing:.1em;text-transform:uppercase;font-weight:800;color:#fff;background:linear-gradient(135deg,rgba(255,79,122,.26),rgba(99,224,255,.12));box-shadow:0 0 18px rgba(255,79,122,.26),0 12px 26px rgba(0,0,0,.8);} .cta a.ghost{background:linear-gradient(135deg,rgba(255,255,255,.08),rgba(255,255,255,.02));border-color:rgba(255,255,255,.26);} @keyframes floatGlow{0%{transform:translateY(0);}100%{transform:translateY(6px);}}</style>
  <div class="char-grid">
    <section class="panel hero">
      <div class="header">
        <div class="eyebrow">{EYEBROW}</div>
        <h1 class="title">{TITLE_MAIN} <span class="badge">{BADGE}</span></h1>
        <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
          <a href="{LINK_PRIMARY_URL}" style="display:inline-flex;align-items:center;gap:8px;padding:8px 10px;border-radius:999px;border:1px solid rgba(255,255,255,.2);text-decoration:none;letter-spacing:.1em;text-transform:uppercase;font-weight:800;color:#fff;background:linear-gradient(135deg,rgba(255,79,122,.26),rgba(99,224,255,.12));box-shadow:0 0 18px rgba(255,79,122,.26),0 12px 26px rgba(0,0,0,.8);">{LINK_PRIMARY_TEXT}</a>
          <audio controls preload="none" style="height:32px;border-radius:12px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18);box-shadow:0 0 12px rgba(0,0,0,.35);">
            <source src="{AUDIO_SRC}" type="audio/mpeg">
          </audio>
        </div>
        <p class="subtitle">{SUBTITLE}</p>
        <div class="swatches">
          <span class="swatch" style="--swatch:{SWATCH_1_COLOR};">{SWATCH_1_LABEL}</span>
          <span class="swatch" style="--swatch:{SWATCH_2_COLOR};">{SWATCH_2_LABEL}</span>
          <span class="swatch" style="--swatch:{SWATCH_3_COLOR};">{SWATCH_3_LABEL}</span>
          <span class="swatch" style="--swatch:{SWATCH_4_COLOR};">{SWATCH_4_LABEL}</span>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="flex-split">
        <div class="pulse-grid">
          <div class="card">
            <h3>Hooks</h3>
            <ul class="list" style="list-style:none;margin:0;padding:0;display:grid;gap:8px;">
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{HOOK_1}</li>
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{HOOK_2}</li>
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{HOOK_3}</li>
            </ul>
          </div>
          <div class="card">
            <h3>Public Persona</h3>
            <p class="scene-copy">{PUBLIC_PERSONA}</p>
          </div>
          <div class="card">
            <h3>Hidden Truth</h3>
            <p class="scene-copy">{HIDDEN_TRUTH}</p>
          </div>
          <div class="card">
            <h3>Vitals</h3>
            <ul class="list" style="list-style:none;margin:0;padding:0;display:grid;gap:8px;">
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;"><strong>Name:</strong> {VITAL_NAME}</li>
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;"><strong>Age:</strong> {VITAL_AGE}</li>
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;"><strong>Role:</strong> {VITAL_ROLE}</li>
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;"><strong>Heritage:</strong> {VITAL_HERITAGE}</li>
            </ul>
          </div>
        </div>
        <div class="card" style="background:linear-gradient(170deg,rgba(255,79,122,.28),rgba(10,8,14,.94));border-color:rgba(255,79,122,.56);">
          <h3>Scene Bait</h3>
          <div class="scene-block">
            <p class="scene-title">{SCENE_TITLE}</p>
            <p class="scene-copy">{SCENE_SNIPPET}</p>
            <div class="chips">
              <span class="chip">{SCENE_CHIP_1}</span>
              <span class="chip">{SCENE_CHIP_2}</span>
              <span class="chip">{SCENE_CHIP_3}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="pulse-grid">
        <div class="card">
          <h3>Behavior</h3>
          <ul class="list" style="list-style:none;margin:0;padding:0;display:grid;gap:8px;">
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{BEHAVIOR_1}</li>
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{BEHAVIOR_2}</li>
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{BEHAVIOR_3}</li>
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{BEHAVIOR_4}</li>
          </ul>
        </div>
        <div class="card">
          <h3>Preferences</h3>
          <p class="scene-copy"><strong>Loves:</strong> {PREF_LOVES}</p>
          <p class="scene-copy"><strong>Hates:</strong> {PREF_HATES}</p>
          <p class="scene-copy"><strong>Dynamic:</strong> {PREF_DYNAMIC}</p>
        </div>
        <div class="card">
          <h3>Drives</h3>
          <p class="scene-copy"><strong>Motivations:</strong> {DRIVES_MOTIVATIONS}</p>
          <p class="scene-copy"><strong>Fears:</strong> {DRIVES_FEARS}</p>
        </div>
        <div class="card">
          <h3>Fault Lines</h3>
          <ul class="list" style="list-style:none;margin:0;padding:0;display:grid;gap:8px;">
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{FAULT_1}</li>
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{FAULT_2}</li>
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{FAULT_3}</li>
          </ul>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="flex-split">
        <div class="voice">
          <h3 class="scene-title">Voice & Lines</h3>
          <div class="quote">{QUOTE_1}</div>
          <div class="quote">{QUOTE_2}</div>
          <div class="quote">{QUOTE_3}</div>
          <p class="scene-copy">{VOICE_TONE}</p>
        </div>
        <div class="micro">
          <div class="card">
            <h3>Dynamic</h3>
            <ul class="list" style="list-style:none;margin:0;padding:0;display:grid;gap:8px;">
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{DYNAMIC_1}</li>
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{DYNAMIC_2}</li>
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{DYNAMIC_3}</li>
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{DYNAMIC_4}</li>
            </ul>
          </div>
          <div class="card">
            <h3>World Notes</h3>
            <ul class="list" style="list-style:none;margin:0;padding:0;display:grid;gap:8px;">
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{WORLD_NOTE_1}</li>
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{WORLD_NOTE_2}</li>
              <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{WORLD_NOTE_3}</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="pulse-grid">
        <div class="card">
          <h3>Guidelines</h3>
          <ul class="list" style="list-style:none;margin:0;padding:0;display:grid;gap:8px;">
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">Never narrate or invent user thoughts, actions, decisions, or consent; keep the user offstage or as a distant observer.</li>
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">Never emit any example or seed character names when producing a different character.</li>
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{GUIDELINE_3}</li>
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{GUIDELINE_4}</li>
          </ul>
        </div>
        <div class="card">
          <h3>Triggers</h3>
          <ul class="list" style="list-style:none;margin:0;padding:0;display:grid;gap:8px;">
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{TRIGGER_1}</li>
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{TRIGGER_2}</li>
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{TRIGGER_3}</li>
          </ul>
        </div>
        <div class="card">
          <h3>Appearance Pulse</h3>
          <ul class="list" style="list-style:none;margin:0;padding:0;display:grid;gap:8px;">
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{APPEARANCE_1}</li>
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{APPEARANCE_2}</li>
            <li style="display:flex;gap:8px;padding:9px 10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:inset 0 1px 0 rgba(255,255,255,.08);line-height:1.5;color:inherit;">{APPEARANCE_3}</li>
          </ul>
        </div>
      </div>
    </section>

    <section class="panel" style="background:linear-gradient(150deg,rgba(99,224,255,.12),rgba(10,8,14,.94));border-color:rgba(99,224,255,.4);">
      <div class="header">
        <div class="eyebrow">{OUTBOUND_EYEBROW}</div>
        <h2 class="title">{OUTBOUND_TITLE}</h2>
      </div>
      <div class="cta">
        <a href="{CTA_LINK_1_URL}" rel="noreferrer noopener" target="_blank">{CTA_LINK_1_TEXT}</a>
        <a href="{CTA_LINK_2_URL}" rel="noreferrer noopener" target="_blank">{CTA_LINK_2_TEXT}</a>
        <a class="ghost" href="{CTA_LINK_3_URL}" rel="noreferrer noopener" target="_blank">{CTA_LINK_3_TEXT}</a>
      </div>
    </section>
  </div>
</div>
```
