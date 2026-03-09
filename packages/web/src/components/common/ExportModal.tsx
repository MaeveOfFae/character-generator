import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { X, Download, FileText, FileJson, FileCode } from 'lucide-react';
import { api, type ExportPresetSummary } from '@char-gen/shared';

type ExportPresetOption = ExportPresetSummary & {
  format?: 'text' | 'json' | 'combined';
  description?: string;
};

interface ExportModalProps {
  draftId: string;
  characterName: string;
  onClose: () => void;
}

export default function ExportModal({ draftId, characterName, onClose }: ExportModalProps) {
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  const { data: presets, isLoading } = useQuery({
    queryKey: ['export-presets'],
    queryFn: () => api.getExportPresets(),
  });

  const handleExport = async () => {
    if (!selectedPreset) return;

    setIsExporting(true);
    try {
      const blob = await api.exportDraft({
        draft_id: draftId,
        preset: selectedPreset,
        include_metadata: includeMetadata,
      });

      // Create download link
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${characterName.replace(/[^a-z0-9]/gi, '_')}_export.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      onClose();
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setIsExporting(false);
    }
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'json':
        return <FileJson className="h-4 w-4" />;
      case 'combined':
        return <FileCode className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-card border border-border rounded-lg shadow-lg w-full max-w-md mx-4 max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="text-lg font-semibold">Export Character</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4 overflow-auto">
          {/* Character Name */}
          <div>
            <label className="text-sm font-medium">Character</label>
            <p className="text-muted-foreground">{characterName}</p>
          </div>

          {/* Preset Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Export Preset</label>
            {isLoading ? (
              <p className="text-sm text-muted-foreground">Loading presets...</p>
            ) : presets && presets.length > 0 ? (
              <div className="space-y-2">
                {presets.map((preset: ExportPresetOption) => {
                  const presetValue = preset.path || preset.name;

                  return (
                  <button
                    key={presetValue}
                    onClick={() => setSelectedPreset(presetValue)}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-colors ${
                      selectedPreset === presetValue
                        ? 'border-primary bg-primary/10'
                        : 'border-border hover:bg-accent'
                    }`}
                  >
                    {getFormatIcon(preset.format ?? 'text')}
                    <div className="text-left">
                      <div className="font-medium">{preset.name}</div>
                      {preset.description && (
                        <p className="text-xs text-muted-foreground">{preset.description}</p>
                      )}
                    </div>
                  </button>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No presets available</p>
            )}
          </div>

          {/* Options */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={includeMetadata}
                onChange={(e) => setIncludeMetadata(e.target.checked)}
                className="rounded border-input"
              />
              Include metadata (creation date, model, tags)
            </label>
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
            onClick={handleExport}
            disabled={!selectedPreset || isExporting}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            {isExporting ? 'Exporting...' : 'Export'}
          </button>
        </div>
      </div>
    </div>
  );
}
