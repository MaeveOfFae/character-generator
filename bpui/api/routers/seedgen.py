"""Seed generator router."""

from fastapi import APIRouter, HTTPException, Request

from ..schemas.seedgen import SeedGenerationRequest, SeedGenerationResponse

router = APIRouter()


SURPRISE_SYSTEM_PROMPT = """You are a creative character concept generator.
Generate diverse, interesting character seeds for roleplay scenarios.
Output exactly 12 creative character concepts, one per line.
Make them varied in genre, tone, and theme.
Include specific details that spark imagination.
Skip numbering or commentary - just the seed lines."""


SURPRISE_USER_PROMPT = """Generate 12 unique character seeds.
Mix genres: fantasy, sci-fi, horror, noir, cyberpunk, romance, thriller, historical, etc.
Include power dynamics, personality quirks, conflicts, or unique hooks.
Be specific and evocative.

Examples (don't copy these):
- Clockwork assassin haunted by memories of their human life
- Fae debt collector who trades in secrets instead of gold
- Retired superhero running a dive bar in the bad part of town
- Moreau bartender with canine traits, secretly investigates missing persons cases

Now generate 12 new seeds:"""


@router.post("", response_model=SeedGenerationResponse)
async def generate_seeds(request: SeedGenerationRequest, http_request: Request):
    """Generate character seeds from genre lines or surprise mode."""
    try:
        from bpui.api.byok import build_request_config
        from bpui.core.prompting import build_seedgen_prompt
        from bpui.llm.factory import create_engine

        if not request.surprise_mode and not request.genre_lines.strip():
            raise HTTPException(status_code=400, detail="Genre lines are required unless surprise mode is enabled")

        if request.surprise_mode:
            system_prompt = SURPRISE_SYSTEM_PROMPT
            user_prompt = SURPRISE_USER_PROMPT
        else:
            system_prompt, user_prompt = build_seedgen_prompt(request.genre_lines)

        config = build_request_config(http_request)
        engine = create_engine(config)
        output = await engine.generate(system_prompt, user_prompt)

        seeds = [
            line.strip()
            for line in output.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]

        return SeedGenerationResponse(seeds=seeds)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))