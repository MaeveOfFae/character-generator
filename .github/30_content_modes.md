# Content Mode (SFW / NSFW / Platform-Safe)

- If the user specifies a mode (e.g., "Mode: SFW"), that mode controls ALL assets.
- If no mode is specified:
  - Infer from the seed when obvious.
  - Otherwise default to NSFW.

Mode rules:

- SFW / Platform-Safe: avoid explicit sexual content, keep tension/subtext allowed.
- NSFW: allow explicit content only when it arises from the seed AND still never assigns consent or actions to {{user}}.

If any guideline conflicts with content mode, content mode wins.
