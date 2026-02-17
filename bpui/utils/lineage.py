"""Character lineage tracking and visualization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Set
from bpui.utils.metadata.metadata import DraftMetadata


@dataclass
class LineageNode:
    """Node in the character lineage tree."""

    draft_path: Path
    character_name: str
    metadata: DraftMetadata
    parents: List[LineageNode]
    children: List[LineageNode]

    def __post_init__(self):
        """Initialize parent and children lists if not provided."""
        if not hasattr(self, 'parents'):
            self.parents = []
        if not hasattr(self, 'children'):
            self.children = []

    @property
    def is_root(self) -> bool:
        """Check if this is a root node (no parents)."""
        return len(self.parents) == 0

    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf node (no children)."""
        return len(self.children) == 0

    @property
    def generation(self) -> int:
        """Calculate generation number (0 for roots, max(parent_gen)+1 otherwise)."""
        if self.is_root:
            return 0
        return max(p.generation for p in self.parents) + 1

    @property
    def offspring_type(self) -> Optional[str]:
        """Get offspring type from metadata."""
        return self.metadata.offspring_type

    def get_all_ancestors(self) -> List[LineageNode]:
        """Get all ancestors (parents, grandparents, etc.)."""
        ancestors = []
        visited = set()

        def traverse(node: LineageNode):
            for parent in node.parents:
                if id(parent) not in visited:
                    visited.add(id(parent))
                    ancestors.append(parent)
                    traverse(parent)

        traverse(self)
        return ancestors

    def get_all_descendants(self) -> List[LineageNode]:
        """Get all descendants (children, grandchildren, etc.)."""
        descendants = []
        visited = set()

        def traverse(node: LineageNode):
            for child in node.children:
                if id(child) not in visited:
                    visited.add(id(child))
                    descendants.append(child)
                    traverse(child)

        traverse(self)
        return descendants

    def get_siblings(self) -> List[LineageNode]:
        """Get siblings (characters with same parents)."""
        if self.is_root:
            return []

        # Get all children of our parents
        siblings = set()
        for parent in self.parents:
            for child in parent.children:
                if child is not self:
                    siblings.add(id(child))

        return [child for parent in self.parents for child in parent.children
                if id(child) in siblings and child is not self]


class LineageTree:
    """Character lineage tree builder and query interface."""

    def __init__(self, drafts_dir: Path):
        """Initialize lineage tree from drafts directory.

        Args:
            drafts_dir: Path to drafts directory
        """
        self.drafts_dir = drafts_dir
        self.nodes: Dict[str, LineageNode] = {}  # draft_name -> node
        self.roots: List[LineageNode] = []
        self._build_tree()

    def _build_tree(self):
        """Build the lineage tree from draft metadata."""
        # First pass: create all nodes
        for draft_path in self.drafts_dir.iterdir():
            if not draft_path.is_dir() or draft_path.name.startswith('.'):
                continue

            metadata = DraftMetadata.load(draft_path)
            if not metadata:
                continue

            node = LineageNode(
                draft_path=draft_path,
                character_name=metadata.character_name or draft_path.name,
                metadata=metadata,
                parents=[],
                children=[]
            )
            self.nodes[draft_path.name] = node

        # Second pass: link parents and children
        for draft_name, node in self.nodes.items():
            if node.metadata.parent_drafts:
                for parent_rel_path in node.metadata.parent_drafts:
                    # Parent paths are relative, resolve them
                    parent_name = Path(parent_rel_path).name
                    if parent_name in self.nodes:
                        parent_node = self.nodes[parent_name]
                        node.parents.append(parent_node)
                        parent_node.children.append(node)

        # Third pass: identify roots
        self.roots = [node for node in self.nodes.values() if node.is_root]

    def get_node(self, draft_name: str) -> Optional[LineageNode]:
        """Get node by draft directory name."""
        return self.nodes.get(draft_name)

    def get_roots(self) -> List[LineageNode]:
        """Get all root nodes (characters with no parents)."""
        return self.roots.copy()

    def get_leaves(self) -> List[LineageNode]:
        """Get all leaf nodes (characters with no children)."""
        return [node for node in self.nodes.values() if node.is_leaf]

    def get_generation(self, gen: int) -> List[LineageNode]:
        """Get all nodes at a specific generation level."""
        return [node for node in self.nodes.values() if node.generation == gen]

    def get_max_generation(self) -> int:
        """Get maximum generation number in tree."""
        if not self.nodes:
            return 0
        return max(node.generation for node in self.nodes.values())

    def find_common_ancestors(self, node1: LineageNode, node2: LineageNode) -> List[LineageNode]:
        """Find common ancestors of two nodes."""
        ancestors1 = set(id(n) for n in node1.get_all_ancestors())
        ancestors2 = node2.get_all_ancestors()
        return [n for n in ancestors2 if id(n) in ancestors1]

    def get_lineage_path(self, node: LineageNode) -> List[List[LineageNode]]:
        """Get all paths from roots to this node.

        Returns:
            List of paths, where each path is a list of nodes from root to target
        """
        paths = []

        def build_paths(current: LineageNode, path: List[LineageNode]):
            path = path + [current]
            if current.is_root:
                paths.append(list(reversed(path)))
            else:
                for parent in current.parents:
                    build_paths(parent, path)

        build_paths(node, [])
        return paths

    def render_tree_ascii(self, max_depth: Optional[int] = None) -> str:
        """Render the lineage tree as ASCII art.

        Args:
            max_depth: Maximum depth to render (None for unlimited)

        Returns:
            ASCII art representation of the tree
        """
        lines = []

        if not self.roots:
            return "No characters found."

        def render_node(node: LineageNode, prefix: str = "", is_last: bool = True, depth: int = 0):
            if max_depth is not None and depth > max_depth:
                return

            # Node symbol
            connector = "└── " if is_last else "├── "

            # Node info
            info = f"{node.character_name}"
            if node.offspring_type:
                info += f" ({node.offspring_type})"
            if node.metadata.mode:
                info += f" [{node.metadata.mode}]"

            lines.append(prefix + connector + info)

            # Render children
            if node.children:
                extension = "    " if is_last else "│   "
                for i, child in enumerate(node.children):
                    is_last_child = (i == len(node.children) - 1)
                    render_node(child, prefix + extension, is_last_child, depth + 1)

        # Render each root
        for i, root in enumerate(self.roots):
            if i > 0:
                lines.append("")  # Blank line between trees
            render_node(root, "", True, 0)

        return "\n".join(lines)

    def render_tree_markdown(self) -> str:
        """Render the lineage tree as Markdown.

        Returns:
            Markdown representation with indented lists
        """
        lines = []

        if not self.roots:
            return "No characters found."

        lines.append("# Character Lineage")
        lines.append("")

        def render_node(node: LineageNode, indent: int = 0):
            bullet = "  " * indent + "- "
            info = f"**{node.character_name}**"

            details = []
            if node.offspring_type:
                details.append(f"type: {node.offspring_type}")
            if node.metadata.mode:
                details.append(f"mode: {node.metadata.mode}")
            if node.metadata.model:
                details.append(f"model: {node.metadata.model}")
            if node.children:
                details.append(f"{len(node.children)} offspring")

            if details:
                info += f" ({', '.join(details)})"

            lines.append(bullet + info)

            # Render children
            for child in node.children:
                render_node(child, indent + 1)

        # Render each root
        for i, root in enumerate(self.roots):
            if i > 0:
                lines.append("")
            lines.append(f"## Family Tree {i+1}")
            lines.append("")
            render_node(root)
            lines.append("")

        # Statistics
        lines.append("## Statistics")
        lines.append("")
        lines.append(f"- Total characters: {len(self.nodes)}")
        lines.append(f"- Root characters: {len(self.roots)}")
        lines.append(f"- Generations: {self.get_max_generation() + 1}")
        lines.append(f"- Leaf characters: {len(self.get_leaves())}")

        return "\n".join(lines)

    def get_family_summary(self, node: LineageNode) -> Dict[str, any]:
        """Get summary of a character's family relationships.

        Returns:
            Dict with family statistics and relationships
        """
        return {
            "character_name": node.character_name,
            "generation": node.generation,
            "is_root": node.is_root,
            "is_leaf": node.is_leaf,
            "offspring_type": node.offspring_type,
            "num_parents": len(node.parents),
            "num_children": len(node.children),
            "num_siblings": len(node.get_siblings()),
            "num_ancestors": len(node.get_all_ancestors()),
            "num_descendants": len(node.get_all_descendants()),
            "parent_names": [p.character_name for p in node.parents],
            "children_names": [c.character_name for c in node.children],
            "sibling_names": [s.character_name for s in node.get_siblings()],
        }


def render_lineage_for_character(drafts_dir: Path, character_name: str) -> str:
    """Quick helper to render lineage for a specific character.

    Args:
        drafts_dir: Path to drafts directory
        character_name: Character name or draft directory name

    Returns:
        ASCII art of character's lineage
    """
    tree = LineageTree(drafts_dir)

    # Find node by name
    node = None
    for n in tree.nodes.values():
        if n.character_name == character_name or n.draft_path.name == character_name:
            node = n
            break

    if not node:
        return f"Character '{character_name}' not found."

    # Get family summary
    summary = tree.get_family_summary(node)

    lines = [
        f"Character: {summary['character_name']}",
        f"Generation: {summary['generation']}",
        f"Offspring Type: {summary['offspring_type'] or 'N/A'}",
        "",
        f"Parents: {', '.join(summary['parent_names']) or 'None (root)'}",
        f"Children: {', '.join(summary['children_names']) or 'None (leaf)'}",
        f"Siblings: {', '.join(summary['sibling_names']) or 'None'}",
        "",
        f"Ancestors: {summary['num_ancestors']}",
        f"Descendants: {summary['num_descendants']}",
        "",
        "Full Lineage Paths:",
    ]

    # Show all paths from roots to this character
    paths = tree.get_lineage_path(node)
    for i, path in enumerate(paths, 1):
        path_str = " → ".join(n.character_name for n in path)
        lines.append(f"  Path {i}: {path_str}")

    return "\n".join(lines)
