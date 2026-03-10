"""Similarity analysis router."""

from fastapi import APIRouter, HTTPException, Request
from ..schemas.similarity import (
    SimilarityRequest,
    SimilarityResultSchema,
    LLMAnalysisSchema,
    MetaAnalysisSchema,
)
from .drafts import _find_draft_dir

router = APIRouter()


@router.post("", response_model=SimilarityResultSchema)
async def analyze_similarity(request: SimilarityRequest, http_request: Request):
    """Compare two characters for similarity."""
    try:
        from bpui.features.similarity.engine import SimilarityAnalyzer, CharacterProfile
        from bpui.utils.file_io.pack_io import load_draft
        from bpui.api.byok import build_request_config

        # Find draft directories
        draft1_path = _find_draft_dir(request.draft1_id)
        draft2_path = _find_draft_dir(request.draft2_id)

        # Load assets
        assets1 = load_draft(draft1_path)
        assets2 = load_draft(draft2_path)

        # Create profiles
        profile1 = CharacterProfile.from_assets(assets1)
        profile2 = CharacterProfile.from_assets(assets2)

        # Use directory names as fallback
        if not profile1.name:
            profile1.name = draft1_path.name
        if not profile2.name:
            profile2.name = draft2_path.name

        # Create analyzer
        analyzer = SimilarityAnalyzer()

        # Run comparison
        llm_engine = None
        if request.include_llm_analysis:
            try:
                from bpui.llm.factory import create_engine
                config = build_request_config(http_request)
                llm_engine = create_engine(config)
            except Exception:
                pass  # Continue without LLM analysis

        result = analyzer.compare_profiles(
            profile1, profile2,
            use_llm=request.include_llm_analysis,
            llm_engine=llm_engine
        )

        # Convert to schema
        llm_analysis = None
        if result.llm_analysis:
            llm_analysis = LLMAnalysisSchema(
                narrative_dynamics=result.llm_analysis.narrative_dynamics,
                story_opportunities=result.llm_analysis.story_opportunities,
                scene_suggestions=result.llm_analysis.scene_suggestions,
                dialogue_style=result.llm_analysis.dialogue_style,
                relationship_arc=result.llm_analysis.relationship_arc,
            )

        meta_analysis = None
        if result.meta_analysis:
            meta_analysis = MetaAnalysisSchema(
                redundancy_level=result.meta_analysis.redundancy_level,
                redundancy_score=result.meta_analysis.redundancy_score,
                issues_detected=result.meta_analysis.issues_detected,
                rework_suggestions_char1=result.meta_analysis.rework_suggestions_char1,
                rework_suggestions_char2=result.meta_analysis.rework_suggestions_char2,
                merge_recommendation=result.meta_analysis.merge_recommendation,
                uniqueness_score=result.meta_analysis.uniqueness_score,
            )

        return SimilarityResultSchema(
            character1_name=result.character1_name,
            character2_name=result.character2_name,
            overall_score=result.overall_score,
            compatibility=result.compatibility,
            conflict_potential=result.conflict_potential,
            synergy_potential=result.synergy_potential,
            commonalities=result.commonalities,
            differences=result.differences,
            relationship_suggestions=result.relationship_suggestions,
            llm_analysis=llm_analysis,
            meta_analysis=meta_analysis,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_similarity(draft_ids: list[str]):
    """Compare multiple characters pairwise."""
    try:
        from bpui.features.similarity.engine import SimilarityAnalyzer
        from bpui.utils.file_io.pack_io import load_draft

        if len(draft_ids) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 drafts to compare")

        # Find all draft directories
        draft_paths = [_find_draft_dir(did) for did in draft_ids]

        # Run batch comparison
        analyzer = SimilarityAnalyzer()
        results = analyzer.compare_multiple(draft_paths)

        # Convert results
        output = []
        for (name1, name2), result in results.items():
            output.append({
                "character1": name1,
                "character2": name2,
                "score": result.overall_score,
                "compatibility": result.compatibility,
            })

        return {"comparisons": output, "total": len(output)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clusters")
async def cluster_characters(draft_ids: list[str], min_similarity: float = 0.6):
    """Group characters by similarity into clusters."""
    try:
        from bpui.features.similarity.engine import SimilarityAnalyzer

        if len(draft_ids) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 drafts to cluster")

        # Find all draft directories
        draft_paths = [_find_draft_dir(did) for did in draft_ids]

        # Run clustering
        analyzer = SimilarityAnalyzer()
        clusters = analyzer.cluster_characters(draft_paths, min_similarity=min_similarity)

        return {
            "clusters": clusters,
            "total_clusters": len(clusters),
            "min_similarity": min_similarity,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
