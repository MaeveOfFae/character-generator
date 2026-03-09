import { Eye, Copy, Check, AlertTriangle } from 'lucide-react';
import { type CreateTemplateRequest } from '@char-gen/shared';

interface ReviewStepProps {
  templateData: CreateTemplateRequest;
}

export default function ReviewStep({ templateData }: ReviewStepProps) {
  const generateTOML = (): string => {
    const lines: string[] = [];

    lines.push(`[template]`);
    lines.push(`name = "${templateData.name}"`);
    lines.push(`version = "${templateData.version}"`);
    if (templateData.description) {
      lines.push(`description = """${templateData.description}"""`);
    }
    lines.push('');

    // Assets section
    templateData.assets.forEach((asset) => {
      lines.push(`[[template.assets]]`);
      lines.push(`name = "${asset.name}"`);
      lines.push(`required = ${asset.required}`);
      if (asset.description) {
        lines.push(`description = """${asset.description}"""`);
      }
      if (asset.blueprint_file) {
        lines.push(`blueprint_file = "${asset.blueprint_file}"`);
      }
      if (asset.depends_on && asset.depends_on.length > 0) {
        lines.push(`depends_on = [${asset.depends_on.map(d => `"${d}"`).join(', ')}]`);
      }
      lines.push('');
    });

    return lines.join('\n');
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(generateTOML());
      // Could show a toast notification here
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const hasWarnings = () => {
    const warnings: string[] = [];

    if (templateData.assets.length === 0) {
      warnings.push('No assets defined');
    }

    const requiredCount = templateData.assets.filter(a => a.required).length;
    if (requiredCount === 0) {
      warnings.push('No required assets defined');
    }

    return warnings;
  };

  const warnings = hasWarnings();

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-semibold">
          4
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold">Review & Create</h3>
          <p className="text-sm text-muted-foreground">
            Review your template configuration before creating
          </p>
        </div>
        <Eye className="h-5 w-5 text-muted-foreground flex-shrink-0" />
      </div>

      {/* Review Content */}
      <div className="pl-11 space-y-6">
        {/* Warnings */}
        {warnings.length > 0 && (
          <div className="rounded-lg border border-yellow-500 bg-yellow-500/10 p-4">
            <div className="flex items-start gap-2 text-yellow-500 mb-2">
              <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
              <h4 className="font-semibold">Warnings</h4>
            </div>
            <ul className="text-sm space-y-1">
              {warnings.map((warning, index) => (
                <li key={index} className="text-yellow-500/80">{warning}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground mb-1">Template Name</p>
            <p className="font-medium">{templateData.name || '-'}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground mb-1">Version</p>
            <p className="font-medium">{templateData.version || '-'}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-xs text-muted-foreground mb-1">Assets</p>
            <p className="font-medium">{templateData.assets.length}</p>
          </div>
        </div>

        {/* Assets Summary */}
        <div>
          <h4 className="font-medium text-sm mb-3">Assets Summary</h4>
          {templateData.assets.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border p-4 text-center text-sm text-muted-foreground">
              No assets configured
            </div>
          ) : (
            <div className="rounded-lg border border-border overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium">Name</th>
                    <th className="text-left px-4 py-2 font-medium">Type</th>
                    <th className="text-left px-4 py-2 font-medium">Dependencies</th>
                  </tr>
                </thead>
                <tbody>
                  {templateData.assets.map((asset) => (
                    <tr key={asset.name} className="border-t border-border">
                      <td className="px-4 py-2">{asset.name.replace(/_/g, ' ')}</td>
                      <td className="px-4 py-2">
                        <span className={asset.required ? 'text-primary' : 'text-muted-foreground'}>
                          {asset.required ? 'Required' : 'Optional'}
                        </span>
                      </td>
                      <td className="px-4 py-2">
                        {asset.depends_on && asset.depends_on.length > 0 ? (
                          <span className="text-xs">
                            {asset.depends_on.map((d, i, arr) => (
                              <span key={d}>
                                {d.replace(/_/g, ' ')}
                                {i < arr.length - 1 && ', '}
                              </span>
                            ))}
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">None</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* TOML Preview */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-sm">Generated Configuration (TOML)</h4>
            <button
              onClick={copyToClipboard}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-input bg-background text-xs hover:bg-accent"
            >
              <Copy className="h-3.5 w-3.5" />
              Copy
            </button>
          </div>
          <div className="rounded-lg border border-border bg-muted/30 p-4 max-h-[300px] overflow-y-auto">
            <pre className="text-xs font-mono whitespace-pre-wrap">
              {generateTOML()}
            </pre>
          </div>
        </div>

        {/* Confirmation */}
        <div className="rounded-lg bg-primary/5 border border-primary/20 p-4">
          <div className="flex items-start gap-3">
            <Check className="h-5 w-5 text-primary flex-shrink-0" />
            <div>
              <h4 className="font-medium text-sm mb-1">Ready to Create Template</h4>
              <p className="text-xs text-muted-foreground">
                Click the "Create Template" button below to finalize your template.
                The template will be saved and available for character generation.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
