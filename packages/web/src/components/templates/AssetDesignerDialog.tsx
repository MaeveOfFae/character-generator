import { useState, useEffect } from 'react';
import { X, Check, FolderOpen, Edit3, Plus } from 'lucide-react';
import { type AssetDefinition, type Blueprint } from '@char-gen/shared';
import BlueprintBrowserDialog from '../blueprints/BlueprintBrowserDialog';
import { cn } from '../../utils/cn';

interface AssetDesignerDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (asset: AssetDefinition, blueprintContent: string) => void;
  asset?: AssetDefinition;
  blueprintContent?: string;
  existingAssets?: string[];
}

export default function AssetDesignerDialog({
  open,
  onClose,
  onSave,
  asset,
  blueprintContent,
  existingAssets = [],
}: AssetDesignerDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [required, setRequired] = useState(true);
  const [blueprintSource, setBlueprintSource] = useState<'browse' | 'custom' | 'new'>('browse');
  const [customBlueprint, setCustomBlueprint] = useState('');
  const [selectedBlueprint, setSelectedBlueprint] = useState<Blueprint | null>(null);
  const [showBlueprintBrowser, setShowBlueprintBrowser] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dependsOn, setDependsOn] = useState<string[]>([]);
  const [blueprintContentValue, setBlueprintContentValue] = useState('');

  // Initialize with existing asset data
  useEffect(() => {
    if (asset) {
      setName(asset.name);
      setDescription(asset.description);
      setRequired(asset.required);
      setDependsOn(asset.depends_on || []);
      setBlueprintContentValue(blueprintContent || '');
      if (asset.blueprint_file) {
        setCustomBlueprint(asset.blueprint_file);
        setBlueprintSource('custom');
      }
    } else {
      // Reset for new asset
      setName('');
      setDescription('');
      setRequired(true);
      setBlueprintSource('browse');
      setCustomBlueprint('');
      setSelectedBlueprint(null);
      setDependsOn([]);
      setBlueprintContentValue('');
    }
  }, [asset, blueprintContent, open]);

  const validateName = (value: string): string | null => {
    if (!value.trim()) return 'Asset name is required';
    if (!/^[a-z_][a-z0-9_]*$/i.test(value)) {
      return 'Name must start with letter or underscore and contain only letters, numbers, and underscores';
    }
    if (existingAssets.includes(value) && (!asset || asset.name !== value)) {
      return 'An asset with this name already exists';
    }
    return null;
  };

  const getBlueprintPath = (): string | undefined => {
    switch (blueprintSource) {
      case 'browse':
        return selectedBlueprint?.path;
      case 'custom':
        return customBlueprint || undefined;
      case 'new':
        return undefined;
    }
  };

  const handleSave = () => {
    const nameError = validateName(name);
    if (nameError) {
      setError(nameError);
      return;
    }

    setError(null);

    const newAsset: AssetDefinition = {
      name: name.trim(),
      description: description.trim(),
      required,
      depends_on: dependsOn,
      blueprint_file: getBlueprintPath(),
    };

    onSave(newAsset, blueprintContentValue);

    // Reset form for next use
    if (!asset) {
      setName('');
      setDescription('');
      setRequired(true);
      setBlueprintSource('browse');
      setCustomBlueprint('');
      setSelectedBlueprint(null);
      setDependsOn([]);
      setBlueprintContentValue('');
    }
  };

  const handleBlueprintSelected = (blueprint: Blueprint) => {
    setSelectedBlueprint(blueprint);
    setBlueprintContentValue(blueprint.content || '');
    setShowBlueprintBrowser(false);
  };

  const toggleDependency = (dep: string) => {
    setDependsOn(prev =>
      prev.includes(dep)
        ? prev.filter(d => d !== dep)
        : [...prev, dep]
    );
  };

  if (!open) return null;

  return (
    <>
      <BlueprintBrowserDialog
        open={showBlueprintBrowser}
        onClose={() => setShowBlueprintBrowser(false)}
        onSelect={handleBlueprintSelected}
        existingAssets={[]}
      />

      <div className="fixed inset-0 z-50 flex items-center justify-center">
        {/* Backdrop */}
        <div className="absolute inset-0 bg-black/50" onClick={onClose} />

        {/* Modal */}
        <div className="relative bg-card border border-border rounded-lg shadow-lg w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border">
            <h2 className="text-lg font-semibold">
              {asset ? 'Edit Asset' : 'Add Asset'}
            </h2>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Error Message */}
            {error && (
              <div className="rounded-lg border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            {/* Asset Name */}
            <div>
              <label className="block text-sm font-medium mb-1.5">
                Asset Name *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  setError(null);
                }}
                placeholder="e.g., character_background"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Use lowercase with underscores (snake_case)
              </p>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium mb-1.5">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description of this asset"
                rows={2}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>

            {/* Required */}
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={required}
                onChange={(e) => setRequired(e.target.checked)}
                className="rounded border-input"
              />
              This asset is required for the template
            </label>

            {/* Blueprint Source */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Blueprint Source
              </label>
              <div className="space-y-2">
                {/* Browse Option */}
                <button
                  onClick={() => setBlueprintSource('browse')}
                  className={cn(
                    'w-full flex items-center gap-3 p-3 rounded-lg border transition-colors text-left',
                    blueprintSource === 'browse'
                      ? 'border-primary bg-primary/10'
                      : 'border-border hover:bg-accent'
                  )}
                >
                  <FolderOpen className="h-5 w-5" />
                  <div className="flex-1">
                    <div className="font-medium">Browse Blueprints</div>
                    <div className="text-xs text-muted-foreground">
                      {selectedBlueprint ? `Selected: ${selectedBlueprint.name}` : 'Select from available blueprints'}
                    </div>
                  </div>
                  {blueprintSource === 'browse' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowBlueprintBrowser(true);
                      }}
                      className="rounded bg-primary text-primary-foreground px-3 py-1 text-xs hover:bg-primary/90"
                    >
                      Browse
                    </button>
                  )}
                </button>

                {/* Custom Option */}
                <button
                  onClick={() => setBlueprintSource('custom')}
                  className={cn(
                    'w-full flex items-center gap-3 p-3 rounded-lg border transition-colors text-left',
                    blueprintSource === 'custom'
                      ? 'border-primary bg-primary/10'
                      : 'border-border hover:bg-accent'
                  )}
                >
                  <Edit3 className="h-5 w-5" />
                  <div className="flex-1">
                    <div className="font-medium">Custom Blueprint</div>
                    <div className="text-xs text-muted-foreground">
                      Enter blueprint filename manually
                    </div>
                  </div>
                </button>

                {blueprintSource === 'custom' && (
                  <input
                    type="text"
                    value={customBlueprint}
                    onChange={(e) => setCustomBlueprint(e.target.value)}
                    placeholder="e.g., assets/character_sheet.md"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring mt-2"
                  />
                )}

                {/* New Option */}
                <button
                  onClick={() => setBlueprintSource('new')}
                  className={cn(
                    'w-full flex items-center gap-3 p-3 rounded-lg border transition-colors text-left opacity-75',
                    blueprintSource === 'new'
                      ? 'border-primary bg-primary/10'
                      : 'border-border hover:bg-accent'
                  )}
                >
                  <Plus className="h-5 w-5" />
                  <div className="flex-1">
                    <div className="font-medium">Create New Blueprint</div>
                    <div className="text-xs text-muted-foreground">
                      Create a new blueprint from scratch (coming soon)
                    </div>
                  </div>
                </button>
              </div>
            </div>

            {/* Dependencies */}
            {existingAssets.length > 0 && (
              <div>
                <label className="block text-sm font-medium mb-2">
                  Dependencies (assets that must be generated first)
                </label>
                <div className="space-y-1">
                  {existingAssets
                    .filter(a => a !== asset?.name && a !== name)
                    .map((assetName) => (
                      <label key={assetName} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={dependsOn.includes(assetName)}
                          onChange={() => toggleDependency(assetName)}
                          className="rounded border-input"
                        />
                        <span className="capitalize">{assetName.replace(/_/g, ' ')}</span>
                      </label>
                    ))}
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-1.5">
                Blueprint Content
              </label>
              <textarea
                value={blueprintContentValue}
                onChange={(e) => setBlueprintContentValue(e.target.value)}
                placeholder="Paste or edit the blueprint content that should be saved with this template asset"
                rows={12}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              <p className="text-xs text-muted-foreground mt-1">
                This content is saved into the template's assets directory and used by the template editor flow.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-2 p-4 border-t border-border">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium rounded-md border border-input hover:bg-accent"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!name.trim()}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              <Check className="h-4 w-4" />
              {asset ? 'Update' : 'Add'} Asset
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
