import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { X, Download, FileText, FileJson, FileCode, CheckCircle2 } from 'lucide-react';
import type { ExportPresetSummary } from '@char-gen/shared';
import { api } from '@/lib/api';
import { saveDownload } from '../../utils/download';
import ExportPreviewPlaceholder from './ExportPreviewPlaceholder';
import PublishingPlaceholder from './PublishingPlaceholder';

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
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const { data: presets, isLoading, error } = useQuery({
    queryKey: ['export-presets'],
    queryFn: () => api.getExportPresets(),
  });

  const handleExport = async () => {
    if (!selectedPreset) return;

    setIsExporting(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const download = await api.exportDraft({
        draft_id: draftId,
        preset: selectedPreset,
        include_metadata: includeMetadata,
      });

      const result = await saveDownload(
        download,
        `${characterName.replace(/[^a-z0-9]/gi, '_')}_export.zip`
      );

      if (result.saved) {
        switch (result.method) {
          case 'share':
            setSuccessMessage('Share sheet opened. Choose Save to Files, Downloads, or another app to keep the export.');
            break;
          case 'new-tab':
            setSuccessMessage('Export opened in a new tab. Use the browser menu in that tab to save or share the file.');
            break;
          case 'download':
            setSuccessMessage('Export sent to the browser download flow. Check your browser download tray or downloads page.');
            break;
          case 'tauri':
            setSuccessMessage('Save dialog opened. Choose the filename and destination there.');
            break;
          default:
            setSuccessMessage('Export prepared successfully.');
            break;
        }
      } else if (result.method === 'cancelled') {
        setErrorMessage('Export was cancelled before the browser could save or share the file.');
      }
    } catch (err) {
      console.error('Export failed:', err);
      setErrorMessage(err instanceof Error ? err.message : 'Export failed');
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
            ) : error ? (
              <p className="text-sm text-destructive">Failed to load presets: {error.message}</p>
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

          <div className="rounded-md border border-border/60 bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
            Browser exports usually do not show a filename dialog. On phones, this may open a share sheet or a new tab instead of a traditional download prompt.
          </div>

          <section className="rounded-lg border border-dashed border-border bg-card/50 p-4">
            <div className="mb-3 flex items-start justify-between gap-4">
              <div>
                <h3 className="text-sm font-semibold">Planned Export Extras</h3>
                <p className="text-xs text-muted-foreground">
                  Preview and publishing hooks stay visible here until those flows are implemented.
                </p>
              </div>
              <span className="rounded-full bg-muted px-2 py-1 text-[11px] font-medium text-muted-foreground">
                Planned
              </span>
            </div>

            <div className="space-y-3">
              <ExportPreviewPlaceholder draftId={draftId} presetName={selectedPreset || undefined} />
              <PublishingPlaceholder draftId={draftId} />
            </div>
          </section>

          {errorMessage && (
            <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {errorMessage}
            </div>
          )}

          {successMessage && (
            <div className="rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-700 dark:text-emerald-300">
              <div className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{successMessage}</span>
              </div>
            </div>
          )}
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
