
from collections import deque
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from bpui.features.templates.templates import AssetDefinition

def topological_sort(assets: List["AssetDefinition"]) -> List[str]:
    """Topologically sort a list of AssetDefinitions based on dependencies.

    Args:
        assets: List of AssetDefinition objects.

    Returns:
        A list of asset names in topological order.

    Raises:
        ValueError: If a circular dependency is detected.
    """
    in_degree = {asset.name: 0 for asset in assets}
    adj = {asset.name: [] for asset in assets}
    asset_map = {asset.name: asset for asset in assets}

    for asset in assets:
        for dep in asset.depends_on:
            if dep in asset_map: # Make sure dependency is part of the template
                in_degree[asset.name] += 1
                adj[dep].append(asset.name)

    queue = deque([name for name, degree in in_degree.items() if degree == 0])
    sorted_order = []

    while queue:
        u = queue.popleft()
        sorted_order.append(u)

        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    if len(sorted_order) != len(assets):
        # Find what's left to identify the cycle
        remaining = set(asset_map.keys()) - set(sorted_order)
        raise ValueError(f"Circular dependency detected in template. Assets involved: {', '.join(remaining)}")

    return sorted_order
