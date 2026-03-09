import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronRight, ChevronDown, FileText, Search, X, FolderOpen, FileJson, BookOpen, Lightbulb, Package, Check } from 'lucide-react';
import { api, type Blueprint } from '@char-gen/shared';
import ReactMarkdown from 'react-markdown';
import { cn } from '../../utils/cn';

interface BlueprintBrowserDialogProps {
  open: boolean;
  onClose: () => void;
  onSelect: (blueprint: Blueprint) => void;
  existingAssets?: string[];
}

interface TreeNode {
  id: string;
  name: string;
  type: 'category' | 'blueprint';
  children?: TreeNode[];
  blueprint?: Blueprint;
  expanded?: boolean;
}

const categoryIcons = {
  core: <BookOpen className="h-4 w-4" />,
  system: <FileJson className="h-4 w-4" />,
  template: <Package className="h-4 w-4" />,
  example: <Lightbulb className="h-4 w-4" />,
};

export default function BlueprintBrowserDialog({
  open,
  onClose,
  onSelect,
  existingAssets = [],
}: BlueprintBrowserDialogProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBlueprint, setSelectedBlueprint] = useState<Blueprint | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(['core', 'system', 'template', 'example']));
  const [treeData, setTreeData] = useState<TreeNode[]>([]);

  const { data: blueprints, isLoading } = useQuery({
    queryKey: ['blueprints'],
    queryFn: () => api.getBlueprints(),
    enabled: open,
  });

  // Build tree structure from blueprints
  useEffect(() => {
    if (!blueprints) return;

    const categories = [
      { id: 'core', name: '📋 Core Blueprints', blueprints: blueprints.core || [] },
      { id: 'system', name: '🔧 System Blueprints', blueprints: blueprints.system || [] },
      { id: 'template', name: '📦 Template Blueprints', blueprints: Object.values(blueprints.templates || {}).flat() },
      { id: 'example', name: '💡 Example Blueprints', blueprints: blueprints.examples || [] },
    ];

    const nodes: TreeNode[] = categories.map(cat => ({
      id: cat.id,
      name: cat.name,
      type: 'category',
      children: cat.blueprints.map((bp: Blueprint) => ({
        id: `${cat.id}/${bp.path}`,
        name: bp.name,
        type: 'blueprint',
        blueprint: bp,
      })),
    }));

    setTreeData(nodes);
  }, [blueprints]);

  const toggleExpand = (nodeId: string) => {
    setExpandedNodes(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  const handleSelect = (blueprint: Blueprint) => {
    setSelectedBlueprint(blueprint);
  };

  const handleConfirm = () => {
    if (selectedBlueprint) {
      onSelect(selectedBlueprint);
      onClose();
      setSelectedBlueprint(null);
      setSearchQuery('');
    }
  };

  const isExistingAsset = (blueprint: Blueprint) => {
    return existingAssets.some(assetName => assetName === blueprint.name);
  };

  const filterTree = (nodes: TreeNode[]): TreeNode[] => {
    if (!searchQuery) return nodes;

    const query = searchQuery.toLowerCase();
    return nodes.reduce((acc: TreeNode[], node) => {
      if (node.type === 'blueprint' && node.blueprint) {
        if (node.name.toLowerCase().includes(query) ||
            node.blueprint.description.toLowerCase().includes(query)) {
          acc.push(node);
        }
      } else if (node.type === 'category' && node.children) {
        const filteredChildren = filterTree(node.children);
        if (filteredChildren.length > 0) {
          acc.push({ ...node, children: filteredChildren });
        }
      }
      return acc;
    }, []);
  };

  const filteredTree = filterTree(treeData);

  const renderNode = (node: TreeNode, depth: number = 0) => {
    const isExpanded = expandedNodes.has(node.id);

    if (node.type === 'blueprint' && node.blueprint) {
      const isSelected = selectedBlueprint?.path === node.blueprint.path;
      const isExisting = isExistingAsset(node.blueprint);

      return (
        <div
          key={node.id}
          onClick={() => handleSelect(node.blueprint!)}
          onDoubleClick={() => {
            if (!isExisting) {
              handleSelect(node.blueprint!);
              handleConfirm();
            }
          }}
          className={cn(
            'flex items-center gap-2 px-2 py-1.5 rounded text-sm cursor-pointer hover:bg-accent/50 transition-colors',
            isSelected && 'bg-primary/20 text-primary',
            isExisting && 'opacity-50 cursor-not-allowed'
          )}
          style={{ paddingLeft: `${(depth + 1) * 1.5}rem` }}
          title={isExisting ? 'This blueprint is already in use' : node.blueprint.description}
        >
          {isExisting ? (
            <X className="h-3 w-3 text-muted-foreground" />
          ) : isSelected ? (
            <Check className="h-3 w-3 text-primary" />
          ) : (
            <FileText className="h-3 w-3 text-muted-foreground" />
          )}
          <span className={cn('truncate', isExisting && 'line-through')}>{node.name}</span>
        </div>
      );
    }

    return (
      <div key={node.id}>
        <div
          onClick={() => toggleExpand(node.id)}
          className="flex items-center gap-2 px-2 py-1.5 rounded text-sm cursor-pointer hover:bg-accent/50 transition-colors font-medium"
          style={{ paddingLeft: `${depth * 1.5 + 0.5}rem` }}
        >
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
          {categoryIcons[node.id as keyof typeof categoryIcons]}
          <span>{node.name}</span>
        </div>
        {isExpanded && node.children && (
          <div>{node.children.map(child => renderNode(child, depth + 1))}</div>
        )}
      </div>
    );
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-card border border-border rounded-lg shadow-xl w-full max-w-5xl mx-4 max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-3">
            <FolderOpen className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Browse Blueprints</h2>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-border">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search blueprints by name or description..."
              className="w-full pl-10 pr-4 py-2 rounded-md border border-input bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Tree */}
          <div className="w-1/2 border-r border-border overflow-y-auto p-4">
            {isLoading ? (
              <div className="flex items-center justify-center h-32 text-sm text-muted-foreground">
                Loading blueprints...
              </div>
            ) : filteredTree.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-sm text-muted-foreground">
                <Search className="h-8 w-8 mb-2" />
                <p>No blueprints found</p>
              </div>
            ) : (
              <div className="space-y-1">
                {filteredTree.map(node => renderNode(node))}
              </div>
            )}
          </div>

          {/* Preview */}
          <div className="w-1/2 overflow-y-auto p-4 bg-muted/30">
            {selectedBlueprint ? (
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold">{selectedBlueprint.name}</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    {selectedBlueprint.category} / {selectedBlueprint.path}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-secondary">
                    v{selectedBlueprint.version}
                  </span>
                  {selectedBlueprint.invokable && (
                    <span className="text-xs px-2 py-1 rounded bg-primary/20 text-primary">
                      Invokable
                    </span>
                  )}
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Description</label>
                  <p className="text-sm text-muted-foreground">
                    {selectedBlueprint.description || 'No description'}
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Preview</label>
                  <div className="rounded-md border border-border bg-card p-4 max-h-[300px] overflow-y-auto">
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown>{selectedBlueprint.content || '*No content*'}</ReactMarkdown>
                    </div>
                  </div>
                </div>

                {isExistingAsset(selectedBlueprint) && (
                  <div className="rounded-md border border-yellow-500 bg-yellow-500/10 p-3 text-sm text-yellow-500">
                    This blueprint is already in use. Please select a different one.
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-sm text-muted-foreground">
                <FileText className="h-12 w-12 mb-2 opacity-50" />
                <p>Select a blueprint to preview</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center p-4 border-t border-border">
          <p className="text-xs text-muted-foreground">
            Double-click to select quickly
          </p>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium rounded-md border border-input hover:bg-accent"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={!selectedBlueprint || isExistingAsset(selectedBlueprint)}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              <Check className="h-4 w-4" />
              Select Blueprint
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
