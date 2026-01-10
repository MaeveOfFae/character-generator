# Chub Packaging Helper (Metadata + Greetings)

Goal: prepare Chub-facing fields and ensure greeting/alternates follow Chub formatting.

1) Ask me for:
   - intended rating: SFW or NSFW
   - 5–10 tags you want (or let me propose them)
   - whether you want alternate greetings (count)

2) Enforce Chub metadata rules:
   - ensure at least 3 accurate tags (otherwise character is hidden in search)
   - rating accurate (SFW vs NSFW)
   - avoid NSFW avatar recommendation if you ask for avatar notes

3) Greetings:
   - produce one "Initial message"
   - if alternate greetings requested:
     - each alternate MUST start with ```"<START>"```

4) Macro hygiene:
   - use {{user}} and {{char}} correctly
   - optionally include time/date macros only if requested
