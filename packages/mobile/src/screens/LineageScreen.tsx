import { useMemo, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useQuery } from '@tanstack/react-query';
import type { LineageNode } from '@char-gen/shared';
import { api } from '../config/api';

function LineageRow({
  node,
  depth,
  selected,
  onSelect,
}: {
  node: LineageNode;
  depth: number;
  selected: boolean;
  onSelect: (node: LineageNode) => void;
}) {
  return (
    <TouchableOpacity
      onPress={() => onSelect(node)}
      style={[styles.nodeCard, selected && styles.nodeCardSelected, { marginLeft: depth * 16 }]}
    >
      <View style={styles.nodeHeader}>
        <View style={styles.nodeTextWrap}>
          <Text style={styles.nodeTitle}>{node.character_name}</Text>
          <Text style={styles.nodeMeta}>
            Generation {node.generation}
            {node.offspring_type ? ` • ${node.offspring_type}` : ''}
            {node.mode ? ` • ${node.mode}` : ''}
          </Text>
        </View>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{node.child_ids.length} children</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

export default function LineageScreen() {
  const navigation = useNavigation();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [generationFilter, setGenerationFilter] = useState<string>('all');
  const [maxDepth, setMaxDepth] = useState(6);
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

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#7c3aed" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>{error instanceof Error ? error.message : 'Failed to load lineage'}</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.headerRow}>
        <View style={styles.headerTextWrap}>
          <Text style={styles.title}>Lineage</Text>
          <Text style={styles.subtitle}>Browse character family trees and offspring branches.</Text>
        </View>
        <TouchableOpacity style={styles.refreshButton} onPress={() => void refetch()}>
          <Text style={styles.refreshButtonText}>{isFetching ? 'Refreshing...' : 'Refresh'}</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{data?.stats.total_characters ?? 0}</Text>
          <Text style={styles.statLabel}>Characters</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{data?.stats.root_characters ?? 0}</Text>
          <Text style={styles.statLabel}>Roots</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{data?.stats.leaf_characters ?? 0}</Text>
          <Text style={styles.statLabel}>Leaves</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{data?.stats.generations ?? 0}</Text>
          <Text style={styles.statLabel}>Generations</Text>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Filters</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterRow}>
          <TouchableOpacity
            style={[styles.chip, generationFilter === 'all' && styles.chipActive]}
            onPress={() => setGenerationFilter('all')}
          >
            <Text style={[styles.chipText, generationFilter === 'all' && styles.chipTextActive]}>All generations</Text>
          </TouchableOpacity>
          {Array.from({ length: (data?.max_generation ?? 0) + 1 }, (_, index) => (
            <TouchableOpacity
              key={index}
              style={[styles.chip, generationFilter === String(index) && styles.chipActive]}
              onPress={() => setGenerationFilter(String(index))}
            >
              <Text style={[styles.chipText, generationFilter === String(index) && styles.chipTextActive]}>
                Gen {index}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <View style={styles.toggleRow}>
          <TouchableOpacity
            style={[styles.toggleChip, rootsOnly && styles.chipActive]}
            onPress={() => {
              setRootsOnly(!rootsOnly);
              if (!rootsOnly) {
                setLeavesOnly(false);
              }
            }}
          >
            <Text style={[styles.chipText, rootsOnly && styles.chipTextActive]}>Roots only</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.toggleChip, leavesOnly && styles.chipActive]}
            onPress={() => {
              setLeavesOnly(!leavesOnly);
              if (!leavesOnly) {
                setRootsOnly(false);
              }
            }}
          >
            <Text style={[styles.chipText, leavesOnly && styles.chipTextActive]}>Leaves only</Text>
          </TouchableOpacity>
          <View style={styles.depthControl}>
            <TouchableOpacity style={styles.depthButton} onPress={() => setMaxDepth((current) => Math.max(1, current - 1))}>
              <Text style={styles.depthButtonText}>-</Text>
            </TouchableOpacity>
            <Text style={styles.depthValue}>Depth {maxDepth}</Text>
            <TouchableOpacity style={styles.depthButton} onPress={() => setMaxDepth((current) => Math.min(10, current + 1))}>
              <Text style={styles.depthButtonText}>+</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Family Tree</Text>
        {renderedTree.length === 0 ? (
          <Text style={styles.emptyText}>No lineage data matches the current filters.</Text>
        ) : (
          <View style={styles.treeList}>
            {renderedTree.map(({ node, depth }) => (
              <LineageRow
                key={`${node.id}-${depth}`}
                node={node}
                depth={depth}
                selected={selectedNode?.id === node.id}
                onSelect={(nextNode) => setSelectedId(nextNode.id)}
              />
            ))}
          </View>
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Character Details</Text>
        {!selectedNode ? (
          <Text style={styles.emptyText}>Select a character to inspect lineage details.</Text>
        ) : (
          <View style={styles.detailsWrap}>
            <Text style={styles.detailTitle}>{selectedNode.character_name}</Text>
            <Text style={styles.detailMeta}>
              Generation {selectedNode.generation}
              {selectedNode.offspring_type ? ` • ${selectedNode.offspring_type}` : ''}
              {selectedNode.mode ? ` • ${selectedNode.mode}` : ''}
            </Text>

            <View style={styles.summaryGrid}>
              <View style={styles.summaryCard}>
                <Text style={styles.summaryLabel}>Ancestors</Text>
                <Text style={styles.summaryValue}>{selectedNode.num_ancestors}</Text>
              </View>
              <View style={styles.summaryCard}>
                <Text style={styles.summaryLabel}>Descendants</Text>
                <Text style={styles.summaryValue}>{selectedNode.num_descendants}</Text>
              </View>
            </View>

            <View style={styles.infoBlock}>
              <Text style={styles.infoLabel}>Parents</Text>
              <Text style={styles.infoValue}>{selectedNode.parent_names.length > 0 ? selectedNode.parent_names.join(', ') : 'None'}</Text>
            </View>
            <View style={styles.infoBlock}>
              <Text style={styles.infoLabel}>Children</Text>
              <Text style={styles.infoValue}>{selectedNode.child_names.length > 0 ? selectedNode.child_names.join(', ') : 'None'}</Text>
            </View>
            <View style={styles.infoBlock}>
              <Text style={styles.infoLabel}>Siblings</Text>
              <Text style={styles.infoValue}>{selectedNode.sibling_names.length > 0 ? selectedNode.sibling_names.join(', ') : 'None'}</Text>
            </View>

            <View style={styles.actionRow}>
              <TouchableOpacity
                style={styles.primaryAction}
                onPress={() =>
                  (navigation as any).navigate('Drafts', {
                    screen: 'DraftDetail',
                    params: { draftId: selectedNode.review_id },
                  })
                }
              >
                <Text style={styles.primaryActionText}>View Draft</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.secondaryAction} onPress={() => (navigation as any).navigate('Offspring')}>
                <Text style={styles.secondaryActionText}>Generate Offspring</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f0f',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f0f0f',
    padding: 16,
  },
  content: {
    padding: 16,
    gap: 16,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  headerTextWrap: {
    flex: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  subtitle: {
    color: '#9ca3af',
    fontSize: 14,
  },
  refreshButton: {
    alignSelf: 'flex-start',
    backgroundColor: '#27272a',
    borderWidth: 1,
    borderColor: '#3f3f46',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  refreshButtonText: {
    color: '#d1d5db',
    fontSize: 13,
    fontWeight: '500',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  statCard: {
    minWidth: '47%',
    flexGrow: 1,
    backgroundColor: '#1f1f1f',
    borderWidth: 1,
    borderColor: '#2f2f2f',
    borderRadius: 12,
    padding: 14,
  },
  statValue: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 4,
  },
  statLabel: {
    color: '#9ca3af',
    fontSize: 12,
  },
  card: {
    backgroundColor: '#1f1f1f',
    borderWidth: 1,
    borderColor: '#2f2f2f',
    borderRadius: 12,
    padding: 16,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  filterRow: {
    gap: 8,
    paddingBottom: 8,
  },
  toggleRow: {
    marginTop: 8,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    alignItems: 'center',
  },
  chip: {
    backgroundColor: '#27272a',
    borderWidth: 1,
    borderColor: '#3f3f46',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  toggleChip: {
    backgroundColor: '#27272a',
    borderWidth: 1,
    borderColor: '#3f3f46',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  chipActive: {
    backgroundColor: '#7c3aed',
    borderColor: '#7c3aed',
  },
  chipText: {
    color: '#d1d5db',
    fontSize: 13,
    fontWeight: '500',
  },
  chipTextActive: {
    color: '#fff',
  },
  depthControl: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginLeft: 'auto',
  },
  depthButton: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: '#27272a',
    borderWidth: 1,
    borderColor: '#3f3f46',
    alignItems: 'center',
    justifyContent: 'center',
  },
  depthButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  depthValue: {
    color: '#d1d5db',
    fontSize: 13,
    fontWeight: '500',
  },
  treeList: {
    gap: 10,
  },
  nodeCard: {
    backgroundColor: '#111111',
    borderWidth: 1,
    borderColor: '#2f2f2f',
    borderRadius: 10,
    padding: 12,
  },
  nodeCardSelected: {
    borderColor: '#7c3aed',
    backgroundColor: '#2a1a4a',
  },
  nodeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
    alignItems: 'flex-start',
  },
  nodeTextWrap: {
    flex: 1,
  },
  nodeTitle: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
  nodeMeta: {
    color: '#9ca3af',
    fontSize: 12,
    marginTop: 4,
  },
  badge: {
    backgroundColor: '#27272a',
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  badgeText: {
    color: '#9ca3af',
    fontSize: 11,
    fontWeight: '500',
  },
  detailsWrap: {
    gap: 12,
  },
  detailTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
  },
  detailMeta: {
    color: '#9ca3af',
    fontSize: 13,
  },
  summaryGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  summaryCard: {
    flex: 1,
    backgroundColor: '#111111',
    borderWidth: 1,
    borderColor: '#2f2f2f',
    borderRadius: 10,
    padding: 12,
  },
  summaryLabel: {
    color: '#9ca3af',
    fontSize: 12,
    textTransform: 'uppercase',
  },
  summaryValue: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
    marginTop: 4,
  },
  infoBlock: {
    gap: 4,
  },
  infoLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  infoValue: {
    color: '#9ca3af',
    fontSize: 13,
    lineHeight: 20,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 4,
  },
  primaryAction: {
    flex: 1,
    backgroundColor: '#7c3aed',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  primaryActionText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  secondaryAction: {
    flex: 1,
    backgroundColor: '#27272a',
    borderWidth: 1,
    borderColor: '#3f3f46',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  secondaryActionText: {
    color: '#d1d5db',
    fontSize: 14,
    fontWeight: '500',
  },
  emptyText: {
    color: '#9ca3af',
    fontSize: 13,
    lineHeight: 20,
  },
  errorText: {
    color: '#fca5a5',
    fontSize: 14,
    textAlign: 'center',
  },
});