import { GitBranch, Check, AlertCircle } from 'lucide-react';
import { type AssetDefinition } from '@char-gen/shared';
import { cn } from '../../../utils/cn';

interface DependenciesStepProps {
  assets: AssetDefinition[];
  onChange: (assets: AssetDefinition[]) => void;
}

export default function DependenciesStep({ assets, onChange }: DependenciesStepProps) {
  const handleToggleDependency = (assetName: string, depName: string) => {
    onChange(
      assets.map(asset => {
        if (asset.name === assetName) {
          const currentDeps = asset.depends_on || [];
          const newDeps = currentDeps.includes(depName)
            ? currentDeps.filter(d => d !== depName)
            : [...currentDeps, depName];

          return { ...asset, depends_on: newDeps };
        }
        return asset;
      })
    );
  };

  const validateDependencies = (): Record<string, string> => {
    const errorMap: Record<string, string> = {};
    const assetSet = new Set(assets.map(a => a.name));

    for (const asset of assets) {
      const deps = asset.depends_on || [];

      // Check for missing dependencies
      for (const dep of deps) {
        if (!assetSet.has(dep)) {
          errorMap[asset.name] = `Missing dependency: ${dep}`;
        }
      }

      // Check for circular dependencies (simple check)
      if (deps.includes(asset.name)) {
        errorMap[asset.name] = 'Cannot depend on itself';
      }

      // Check for circular dependencies (transitive)
      for (const dep of deps) {
        const depAsset = assets.find(a => a.name === dep);
        if (depAsset && depAsset.depends_on?.includes(asset.name)) {
          errorMap[asset.name] = 'Circular dependency detected';
        }
      }
    }

    return errorMap;
  };

  const depErrors = validateDependencies();

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-semibold">
          3
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold">Dependencies</h3>
          <p className="text-sm text-muted-foreground">
            Configure which assets depend on others. Assets will be generated in dependency order.
          </p>
        </div>
      </div>

      {/* Dependency Matrix */}
      <div className="pl-11 space-y-4">
        {Object.keys(depErrors).length > 0 && (
          <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
            <div className="flex items-start gap-2 text-destructive mb-2">
              <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
              <h4 className="font-semibold">Dependency Issues Detected</h4>
            </div>
            <ul className="text-sm space-y-1">
              {Object.entries(depErrors).map(([assetName, error]) => (
                <li key={assetName} className="text-destructive/80">
                  <span className="font-medium">{assetName}:</span> {error}
                </li>
              ))}
            </ul>
          </div>
        )}

        {assets.length === 0 ? (
          <div className="rounded-lg border border-border bg-muted/30 p-6 text-center text-sm text-muted-foreground">
            <GitBranch className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>Add assets in the previous step to configure dependencies.</p>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm font-medium">
              Select dependencies for each asset (optional):
            </p>

            {assets.map((asset) => {
              const availableDeps = assets.filter(a => a.name !== asset.name);
              const assetDeps = asset.depends_on || [];
              const hasError = depErrors[asset.name];

              return (
                <div
                  key={asset.name}
                  className={cn(
                    'rounded-lg border p-4',
                    hasError ? 'border-destructive bg-destructive/5' : 'border-border bg-card'
                  )}
                >
                  <div className="flex items-center gap-2 mb-3">
                    <GitBranch className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium capitalize">
                      {asset.name.replace(/_/g, ' ')}
                    </span>
                    {asset.required && (
                      <span className="text-xs px-2 py-0.5 rounded bg-primary/20 text-primary">
                        Required
                      </span>
                    )}
                  </div>

                  {availableDeps.length === 0 ? (
                    <p className="text-xs text-muted-foreground italic">
                      No other assets available as dependencies
                    </p>
                  ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                      {availableDeps.map((dep) => (
                        <label
                          key={dep.name}
                          className="flex items-center gap-2 px-3 py-2 rounded border border-border hover:bg-accent/50 cursor-pointer transition-colors"
                        >
                          <input
                            type="checkbox"
                            checked={assetDeps.includes(dep.name)}
                            onChange={() => handleToggleDependency(asset.name, dep.name)}
                            className="rounded border-input"
                          />
                          <span className="text-xs truncate">{dep.name.replace(/_/g, ' ')}</span>
                        </label>
                      ))}
                    </div>
                  )}

                  {assetDeps.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border">
                      <p className="text-xs text-muted-foreground mb-2">
                        Selected dependencies will be generated before this asset:
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {assetDeps.map((depName) => {
                          return (
                            <span
                              key={depName}
                              className="text-xs px-2 py-1 rounded bg-secondary flex items-center gap-1"
                            >
                              <Check className="h-3 w-3" />
                              {depName.replace(/_/g, ' ')}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {hasError && (
                    <p className="text-xs text-destructive mt-2">
                      {depErrors[asset.name]}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Info Box */}
        <div className="rounded-lg bg-muted/50 p-4">
          <h4 className="font-medium text-sm mb-2">How Dependencies Work</h4>
          <ul className="text-xs text-muted-foreground space-y-1.5">
            <li>• Assets are generated in the order defined by dependencies</li>
            <li>• An asset depends on another asset when it needs the other's content</li>
            <li>• Required assets cannot depend on optional assets</li>
            <li>• Circular dependencies are not allowed</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
