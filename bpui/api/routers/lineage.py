"""Lineage router."""

from fastapi import APIRouter, HTTPException

from ..schemas.lineage import LineageNodeSchema, LineageResponse, LineageStatsSchema
from .drafts import _get_drafts_dir

router = APIRouter()


@router.get("", response_model=LineageResponse)
async def get_lineage():
    """Get the full character lineage graph."""
    try:
        from bpui.utils.lineage import LineageTree

        drafts_dir = _get_drafts_dir()
        if not drafts_dir.exists():
            return LineageResponse()

        tree = LineageTree(drafts_dir)
        nodes = []

        for node in tree.nodes.values():
            summary = tree.get_family_summary(node)
            review_id = node.draft_path.name

            nodes.append(
                LineageNodeSchema(
                    id=node.draft_path.name,
                    review_id=review_id,
                    draft_name=node.draft_path.name,
                    character_name=node.character_name,
                    generation=node.generation,
                    is_root=node.is_root,
                    is_leaf=node.is_leaf,
                    offspring_type=node.offspring_type,
                    mode=node.metadata.mode,
                    model=node.metadata.model,
                    created=node.metadata.created,
                    parent_ids=[parent.draft_path.name for parent in node.parents],
                    child_ids=[child.draft_path.name for child in node.children],
                    parent_names=summary["parent_names"],
                    child_names=summary["children_names"],
                    sibling_names=summary["sibling_names"],
                    num_ancestors=summary["num_ancestors"],
                    num_descendants=summary["num_descendants"],
                )
            )

        return LineageResponse(
            nodes=nodes,
            roots=[node.draft_path.name for node in tree.get_roots()],
            max_generation=tree.get_max_generation(),
            stats=LineageStatsSchema(
                total_characters=len(tree.nodes),
                root_characters=len(tree.roots),
                leaf_characters=len(tree.get_leaves()),
                generations=tree.get_max_generation() + 1 if tree.nodes else 0,
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))