import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { GitBranch, Loader2, RefreshCw, ArrowRight, Users } from 'lucide-react';
import { api, type LineageNode } from '@char-gen/shared';
import { useAssistantScreenContext } from '../common/AssistantContext';

function NodeCard({
  node,
  depth,
  onSelect,
  selected,
}: {
  node: LineageNode;
  depth: number;
  onSelect: (node: LineageNode) => void;
  selected: boolean;
}) {
  return (
    <button
      onClick={() => onSelect(node)}
      className={`w-full rounded-lg border p-3 text-left transition-colors ${selected ? 'border-primary bg-primary/10' : 'border-border bg-card hover:bg-accent/50'}`}
      style={{ marginLeft: `${depth * 20}px` }}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="font-medium">{node.character_name}</div>
          <div className="mt-1 text-xs text-muted-foreground">
            Generation {node.generation}
            {node.offspring_type ? ` • ${node.offspring_type}` : ''}
            {node.mode ? ` • ${node.mode}` : ''}
          </div>
        </div>
        <span className="rounded-full bg-muted px-2 py-1 text-xs text-muted-foreground">
          {node.child_ids.length} children
        </span>
      </div>
    </button>
  );
}

export default function Lineage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [generationFilter, setGenerationFilter] = useState<string>('all');
  const [maxDepth, setMaxDepth] = useState<number>(10);
  const [rootsOnly, setRootsOnly] = useState(false);
  const [leavesOnly, setLeavesOnly] = useState(false);

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['lineage'],
    queryFn: () => api.getLineage(),
  });

  const nodeMap = useMemo(() => new Map((data?.nodes ?? []).map((node) => [node.id, node])), [data?.nodes]);

  const selectedNode = selectedId ? nodeMap.get(selectedId) ?? null : data?.nodes[0] ?? null;

  const flatFilteredNodes = useMemo(() => {
    const nodes = data?.nodes ?? [];
    return nodes.filter((node) => {
      if (generationFilter !== 'all' && node.generation !== Number(generationFilter)) {
        return false;
      }
      if (rootsOnly && !node.is_root) {
        return false;
      }
      if (leavesOnly && !node.is_leaf) {
        return false;
      }
      return true;
    });
  }, [data?.nodes, generationFilter, rootsOnly, leavesOnly]);

  const renderedTree = useMemo(() => {
    if (!data) {
      return [] as Array<{ node: LineageNode; depth: number }>;
    }

    const rows: Array<{ node: LineageNode; depth: number }> = [];
    const allowedIds = new Set(flatFilteredNodes.map((node) => node.id));

    const walk = (nodeId: string, depth: number) => {
      const node = nodeMap.get(nodeId);
      if (!node || depth > maxDepth || !allowedIds.has(node.id)) {
        return;
      }

      rows.push({ node, depth });
      node.child_ids.forEach((childId) => walk(childId, depth + 1));
    };

    if (generationFilter !== 'all') {
      flatFilteredNodes
        .sort((left, right) => left.character_name.localeCompare(right.character_name))
        .forEach((node) => rows.push({ node, depth: 0 }));
      return rows;
    }

    data.roots.forEach((rootId) => walk(rootId, 0));
    return rows;
  }, [data, flatFilteredNodes, generationFilter, maxDepth, nodeMap]);

  useAssistantScreenContext({
    selected_character: selectedNode?.character_name ?? null,
    selected_generation: selectedNode?.generation ?? null,
    generation_filter: generationFilter,
    max_depth: maxDepth,
    roots_only: rootsOnly,
    leaves_only: leavesOnly,
    rendered_nodes: renderedTree.length,
    total_nodes: data?.nodes.length ?? 0,
    lineage_generations: data?.stats.generations ?? 0,
  });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-destructive">
        Error loading lineage: {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Lineage</h1>
          <p className="text-muted-foreground">
            Browse family trees across generated offspring and follow each branch back into draft review.
          </p>
        </div>
        <button
          onClick={() => void refetch()}
          className="inline-flex items-center gap-2 rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-accent"
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="text-2xl font-bold">{data?.stats.total_characters ?? 0}</div>
          <div className="text-sm text-muted-foreground">Characters</div>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="text-2xl font-bold">{data?.stats.root_characters ?? 0}</div>
          <div className="text-sm text-muted-foreground">Roots</div>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="text-2xl font-bold">{data?.stats.leaf_characters ?? 0}</div>
          <div className="text-sm text-muted-foreground">Leaves</div>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="text-2xl font-bold">{data?.stats.generations ?? 0}</div>
          <div className="text-sm text-muted-foreground">Generations</div>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card p-4">
        <div className="grid gap-4 md:grid-cols-[1fr_auto_auto_auto] md:items-end">
          <div>
            <label className="text-sm font-medium">Generation</label>
            <select
              value={generationFilter}
              onChange={(event) => setGenerationFilter(event.target.value)}
              className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="all">All generations</option>
              {Array.from({ length: (data?.max_generation ?? 0) + 1 }, (_, index) => (
                <option key={index} value={String(index)}>
                  Generation {index}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium">Max Depth</label>
            <input
              type="number"
              min={1}
              max={10}
              value={maxDepth}
              onChange={(event) => setMaxDepth(Number(event.target.value))}
              className="mt-1.5 w-28 rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </div>
          <label className="inline-flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={rootsOnly}
              onChange={(event) => {
                setRootsOnly(event.target.checked);
                if (event.target.checked) {
                  setLeavesOnly(false);
                }
              }}
            />
            Roots only
          </label>
          <label className="inline-flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={leavesOnly}
              onChange={(event) => {
                setLeavesOnly(event.target.checked);
                if (event.target.checked) {
                  setRootsOnly(false);
                }
              }}
            />
            Leaves only
          </label>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
        <section className="rounded-lg border border-border bg-card p-4">
          <div className="mb-4 flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Family Tree</h2>
          </div>

          {renderedTree.length === 0 ? (
            <div className="flex min-h-56 items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted-foreground">
              No lineage data matches the current filters.
            </div>
          ) : (
            <div className="space-y-3">
              {renderedTree.map(({ node, depth }) => (
                <NodeCard
                  key={`${node.id}-${depth}`}
                  node={node}
                  depth={depth}
                  selected={selectedNode?.id === node.id}
                  onSelect={(nextNode) => setSelectedId(nextNode.id)}
                />
              ))}
            </div>
          )}
        </section>

        <section className="rounded-lg border border-border bg-card p-4">
          <div className="mb-4 flex items-center gap-2">
            <Users className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Character Details</h2>
          </div>

          {!selectedNode ? (
            <div className="text-sm text-muted-foreground">Select a character to inspect lineage details.</div>
          ) : (
            <div className="space-y-5 text-sm">
              <div>
                <div className="text-xl font-semibold">{selectedNode.character_name}</div>
                <div className="mt-1 text-muted-foreground">
                  Generation {selectedNode.generation}
                  {selectedNode.offspring_type ? ` • ${selectedNode.offspring_type}` : ''}
                  {selectedNode.mode ? ` • ${selectedNode.mode}` : ''}
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg bg-muted/40 p-3">
                  <div className="text-xs uppercase tracking-wide text-muted-foreground">Ancestors</div>
                  <div className="mt-1 text-lg font-semibold">{selectedNode.num_ancestors}</div>
                </div>
                <div className="rounded-lg bg-muted/40 p-3">
                  <div className="text-xs uppercase tracking-wide text-muted-foreground">Descendants</div>
                  <div className="mt-1 text-lg font-semibold">{selectedNode.num_descendants}</div>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <div className="font-medium">Parents</div>
                  <div className="mt-1 text-muted-foreground">{selectedNode.parent_names.length > 0 ? selectedNode.parent_names.join(', ') : 'None'}</div>
                </div>
                <div>
                  <div className="font-medium">Children</div>
                  <div className="mt-1 text-muted-foreground">{selectedNode.child_names.length > 0 ? selectedNode.child_names.join(', ') : 'None'}</div>
                </div>
                <div>
                  <div className="font-medium">Siblings</div>
                  <div className="mt-1 text-muted-foreground">{selectedNode.sibling_names.length > 0 ? selectedNode.sibling_names.join(', ') : 'None'}</div>
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <Link
                  to={`/drafts/${encodeURIComponent(selectedNode.review_id)}`}
                  className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 font-medium text-primary-foreground hover:bg-primary/90"
                >
                  View Draft
                  <ArrowRight className="h-4 w-4" />
                </Link>
                {selectedNode.parent_ids.length >= 2 && (
                  <Link
                    to={`/similarity?character1=${encodeURIComponent(selectedNode.parent_ids[0])}&character2=${encodeURIComponent(selectedNode.parent_ids[1])}`}
                    className="inline-flex items-center gap-2 rounded-md border border-input px-4 py-2 font-medium hover:bg-accent"
                  >
                    Compare Parents
                  </Link>
                )}
                <Link
                  to="/offspring"
                  className="inline-flex items-center gap-2 rounded-md border border-input px-4 py-2 font-medium hover:bg-accent"
                >
                  Generate More Offspring
                </Link>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}