import { useState } from 'react';
import { DndContext, DragEndEvent, closestCenter } from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
  arrayMove,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, Plus, Trash2, FileText, Star } from 'lucide-react';
import { type AssetDefinition } from '@char-gen/shared';
import AssetDesignerDialog from '../AssetDesignerDialog';
import { cn } from '../../../utils/cn';

interface AssetSelectionStepProps {
  assets: AssetDefinition[];
  onChange: (assets: AssetDefinition[]) => void;
  blueprintContents: Record<string, string>;
  onBlueprintContentsChange: (blueprintContents: Record<string, string>) => void;
}

function getBlueprintContentKey(asset: Pick<AssetDefinition, 'name' | 'blueprint_file'>): string {
  return asset.blueprint_file ?? `${asset.name}.md`;
}

function SortableAsset({ asset, onEdit, onRemove }: {
  asset: AssetDefinition;
  onEdit: (asset: AssetDefinition) => void;
  onRemove: () => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: asset.name });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'flex items-center gap-3 p-3 rounded-lg border bg-card group',
        isDragging ? 'border-primary/50 shadow-lg' : 'border-border',
        asset.required ? 'border-l-4 border-l-primary' : ''
      )}
    >
      {/* Drag Handle */}
      <button
        {...attributes}
        {...listeners}
        className="text-muted-foreground hover:text-foreground cursor-grab active:cursor-grabbing"
      >
        <GripVertical className="h-4 w-4" />
      </button>

      {/* Asset Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={cn('font-medium', asset.required ? 'text-primary' : '')}>
            {asset.name.replace(/_/g, ' ')}
          </span>
          {asset.required && <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />}
        </div>
        {asset.description && (
          <p className="text-xs text-muted-foreground truncate">{asset.description}</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={() => onEdit(asset)}
          className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
          title="Edit asset"
        >
          <FileText className="h-4 w-4" />
        </button>
        <button
          onClick={onRemove}
          className="p-1.5 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
          title="Remove asset"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

export default function AssetSelectionStep({
  assets,
  onChange,
  blueprintContents,
  onBlueprintContentsChange,
}: AssetSelectionStepProps) {
  const [editingAsset, setEditingAsset] = useState<AssetDefinition | undefined>();
  const [showAssetDesigner, setShowAssetDesigner] = useState(false);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = assets.findIndex(a => a.name === active.id);
      const newIndex = assets.findIndex(a => a.name === over.id);

      onChange(arrayMove(assets, oldIndex, newIndex));
    }
  };

  const handleAddAsset = () => {
    setShowAssetDesigner(true);
  };

  const handleSaveAsset = (newAsset: AssetDefinition, blueprintContent: string) => {
    const previousName = editingAsset?.name;
    const previousKey = editingAsset ? getBlueprintContentKey(editingAsset) : undefined;
    const nextKey = getBlueprintContentKey(newAsset);
    const existingIndex = previousName
      ? assets.findIndex(a => a.name === previousName)
      : assets.findIndex(a => a.name === newAsset.name);

    if (existingIndex >= 0) {
      const updated = [...assets];
      updated[existingIndex] = newAsset;
      onChange(updated);
    } else {
      onChange([...assets, newAsset]);
    }

    const nextBlueprintContents = { ...blueprintContents };
    if (previousKey) {
      delete nextBlueprintContents[previousKey];
    }
    if (previousName && previousName !== newAsset.name) {
      delete nextBlueprintContents[previousName];
    }
    if (blueprintContent.trim()) {
      nextBlueprintContents[nextKey] = blueprintContent;
    }
    onBlueprintContentsChange(nextBlueprintContents);

    setShowAssetDesigner(false);
    setEditingAsset(undefined);
  };

  const handleEditAsset = (asset: AssetDefinition) => {
    setEditingAsset(asset);
    setShowAssetDesigner(true);
  };

  const handleRemoveAsset = (assetName: string) => {
    const asset = assets.find((candidate) => candidate.name === assetName);
    onChange(assets.filter(a => a.name !== assetName));
    const nextBlueprintContents = { ...blueprintContents };
    if (asset) {
      delete nextBlueprintContents[getBlueprintContentKey(asset)];
    }
    delete nextBlueprintContents[assetName];
    onBlueprintContentsChange(nextBlueprintContents);
  };

  return (
    <>
      <AssetDesignerDialog
        open={showAssetDesigner}
        onClose={() => {
          setShowAssetDesigner(false);
          setEditingAsset(undefined);
        }}
        onSave={handleSaveAsset}
        asset={editingAsset}
        blueprintContent={editingAsset ? blueprintContents[getBlueprintContentKey(editingAsset)] ?? blueprintContents[editingAsset.name] ?? '' : ''}
        existingAssets={assets.map(a => a.name)}
      />

      <div className="space-y-6">
        {/* Step Header */}
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-semibold">
            2
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold">Asset Selection</h3>
            <p className="text-sm text-muted-foreground">
              Define the assets that make up your template. Drag to reorder.
            </p>
          </div>
        </div>

        {/* Asset List */}
        <div className="pl-11">
          {assets.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border p-8 text-center">
              <FileText className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
              <p className="text-sm text-muted-foreground mb-4">
                No assets added yet. Add your first asset to get started.
              </p>
              <button
                onClick={handleAddAsset}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
              >
                <Plus className="h-4 w-4" />
                Add Asset
              </button>
            </div>
          ) : (
            <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
              <div className="space-y-2">
                <SortableContext
                  items={assets.map(a => a.name)}
                  strategy={verticalListSortingStrategy}
                >
                  {assets.map((asset) => (
                    <SortableAsset
                      key={asset.name}
                      asset={asset}
                      onEdit={handleEditAsset}
                      onRemove={() => handleRemoveAsset(asset.name)}
                    />
                  ))}
                </SortableContext>
              </div>
            </DndContext>
          )}

          {assets.length > 0 && (
            <button
              onClick={handleAddAsset}
              className="mt-4 w-full inline-flex items-center justify-center gap-2 rounded-md border border-dashed border-input px-4 py-3 text-sm hover:bg-accent/50"
            >
              <Plus className="h-4 w-4" />
              Add Another Asset
            </button>
          )}
        </div>

        {/* Legend */}
        <div className="pl-11">
          <div className="flex gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
              Required
            </div>
            <div className="flex items-center gap-1.5">
              <GripVertical className="h-3 w-3" />
              Drag to reorder
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
