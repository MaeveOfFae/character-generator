import { Info } from 'lucide-react';

interface BasicInfoStepProps {
  name: string;
  version: string;
  description: string;
  onChange: (field: 'name' | 'version' | 'description', value: string) => void;
  errors: Record<string, string>;
}

export default function BasicInfoStep({ name, version, description, onChange, errors }: BasicInfoStepProps) {
  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-semibold">
          1
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold">Basic Information</h3>
          <p className="text-sm text-muted-foreground">
            Define the basic metadata for your template
          </p>
        </div>
        <Info className="h-5 w-5 text-muted-foreground flex-shrink-0" />
      </div>

      {/* Form Fields */}
      <div className="space-y-4 pl-11">
        {/* Template Name */}
        <div>
          <label className="block text-sm font-medium mb-1.5">
            Template Name *
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => onChange('name', e.target.value)}
            placeholder="e.g., fantasy_character, sci_fi_npc"
            className={`
              w-full rounded-md border px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2
              ${errors.name ? 'border-destructive focus-visible:ring-destructive' : 'border-input focus-visible:ring-ring'}
            `}
          />
          {errors.name && (
            <p className="text-xs text-destructive mt-1">{errors.name}</p>
          )}
          <p className="text-xs text-muted-foreground mt-1">
            Use lowercase with underscores (snake_case)
          </p>
        </div>

        {/* Version */}
        <div>
          <label className="block text-sm font-medium mb-1.5">
            Version *
          </label>
          <input
            type="text"
            value={version}
            onChange={(e) => onChange('version', e.target.value)}
            placeholder="e.g., 1.0"
            className={`
              w-full rounded-md border px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2
              ${errors.version ? 'border-destructive focus-visible:ring-destructive' : 'border-input focus-visible:ring-ring'}
            `}
          />
          {errors.version && (
            <p className="text-xs text-destructive mt-1">{errors.version}</p>
          )}
          <p className="text-xs text-muted-foreground mt-1">
            Semantic versioning (major.minor)
          </p>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium mb-1.5">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => onChange('description', e.target.value)}
            placeholder="Describe what this template is for and what kind of characters it generates"
            rows={4}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
      </div>
    </div>
  );
}
