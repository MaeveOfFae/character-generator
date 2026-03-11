/**
 * Data Manager Component
 * Import/Export drafts and configuration
 */

import { useEffect, useRef, useState } from 'react';
import {
  Download,
  Upload,
  Database,
  Settings,
  Trash2,
  FileJson,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';
import { DraftStorage } from '../../lib/storage/draft-db.js';
import { configManager } from '../../lib/config/manager.js';

interface DataStats {
  drafts: number;
  apiKeys: number;
  configExists: boolean;
}

export default function DataManager() {
  const exportInputRef = useRef<HTMLInputElement | null>(null);
  const importInputRef = useRef<HTMLInputElement | null>(null);

  const [stats, setStats] = useState<DataStats | null>(null);
  const [notice, setNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [isClearing, setIsClearing] = useState(false);
  const [showConfirmClear, setShowConfirmClear] = useState(false);

  useEffect(() => {
    void loadStats();
  }, []);

  async function loadStats() {
    try {
      const [drafts, config] = await Promise.all([
        DraftStorage.getAllDrafts(),
        Promise.resolve(configManager.getConfig()),
      ]);

      const apiKeys = Object.keys(configManager.getApiKeys());

      setStats({
        drafts: drafts.length,
        apiKeys: apiKeys.length,
        configExists: !!config,
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  }

  async function handleExportDrafts() {
    try {
      const data = await DraftStorage.exportAll();
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `character-generator-drafts-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      URL.revokeObjectURL(url);

      setNotice({ type: 'success', message: 'Drafts exported successfully' });
    } catch (error) {
      setNotice({ type: 'error', message: error instanceof Error ? error.message : 'Export failed' });
    }
  }

  async function handleExportConfig() {
    try {
      const data = configManager.exportConfig();
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `character-generator-config-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      URL.revokeObjectURL(url);

      setNotice({ type: 'success', message: 'Configuration exported successfully' });
    } catch (error) {
      setNotice({ type: 'error', message: error instanceof Error ? error.message : 'Export failed' });
    }
  }

  async function handleExportApiKeys() {
    try {
      const data = configManager.exportApiKeys();
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `character-generator-api-keys-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      URL.revokeObjectURL(url);

      setNotice({ type: 'success', message: 'API keys exported successfully. Warning: API keys are sensitive - handle with care.' });
    } catch (error) {
      setNotice({ type: 'error', message: error instanceof Error ? error.message : 'Export failed' });
    }
  }

  async function handleImportDrafts(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      await DraftStorage.import(text);
      await loadStats();

      setNotice({ type: 'success', message: `Imported drafts from ${file.name}` });
    } catch (error) {
      setNotice({ type: 'error', message: error instanceof Error ? error.message : 'Import failed' });
    }

    event.target.value = '';
  }

  async function handleImportConfig(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      configManager.importConfig(text);
      await loadStats();

      setNotice({ type: 'success', message: `Configuration imported from ${file.name}` });
    } catch (error) {
      setNotice({ type: 'error', message: error instanceof Error ? error.message : 'Import failed' });
    }

    event.target.value = '';
  }

  async function handleClearAll() {
    setIsClearing(true);

    try {
      await Promise.all([
        DraftStorage.clearAll(),
        Promise.resolve(configManager.clearAll()),
      ]);

      await loadStats();
      setNotice({ type: 'success', message: 'All data cleared successfully' });
      setShowConfirmClear(false);
    } catch (error) {
      setNotice({ type: 'error', message: error instanceof Error ? error.message : 'Clear failed' });
    }

    setIsClearing(false);
  }

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Data Management</h1>
        <p className="text-muted-foreground">
          Export your drafts and configuration for backup, or import from a previous export.
        </p>
      </div>

      {notice && (
        <div className={`rounded-md border px-4 py-3 flex items-start gap-3 ${
          notice.type === 'success' ? 'border-green-500/50 bg-green-500/10 text-green-700 dark:text-green-400' : 'border-destructive/50 bg-destructive/10 text-destructive'
        }`}>
          {notice.type === 'success' ? (
            <CheckCircle2 className="h-5 w-5 shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
          )}
          <span className="text-sm">{notice.message}</span>
          <button
            onClick={() => setNotice(null)}
            className="ml-auto opacity-50 hover:opacity-100"
          >
            ×
          </button>
        </div>
      )}

      {/* Stats */}
      {stats && (
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Drafts</h3>
            </div>
            <p className="text-2xl font-bold mt-2">{stats.drafts}</p>
            <p className="text-xs text-muted-foreground mt-1">Stored locally</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2">
              <FileJson className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">API Keys</h3>
            </div>
            <p className="text-2xl font-bold mt-2">{stats.apiKeys}</p>
            <p className="text-xs text-muted-foreground mt-1">Configured providers</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Config</h3>
            </div>
            <p className="text-2xl font-bold mt-2">{stats.configExists ? 'Set' : 'Default'}</p>
            <p className="text-xs text-muted-foreground mt-1">Customization status</p>
          </div>
        </div>
      )}

      {/* Export Section */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border p-4">
          <h2 className="text-lg font-semibold">Export Data</h2>
          <p className="text-sm text-muted-foreground">
            Download your data as JSON files for backup or transfer to another device.
          </p>
        </div>
        <div className="space-y-3 p-4">
          <div className="flex items-center justify-between rounded-md border border-border p-4">
            <div className="flex items-center gap-3">
              <Database className="h-5 w-5 text-muted-foreground" />
              <div>
                <h3 className="font-medium">Export All Drafts</h3>
                <p className="text-xs text-muted-foreground">
                  Download all your generated characters
                </p>
              </div>
            </div>
            <button
              onClick={handleExportDrafts}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              <Download className="h-4 w-4" />
              Export
            </button>
          </div>

          <div className="flex items-center justify-between rounded-md border border-border p-4">
            <div className="flex items-center gap-3">
              <Settings className="h-5 w-5 text-muted-foreground" />
              <div>
                <h3 className="font-medium">Export Configuration</h3>
                <p className="text-xs text-muted-foreground">
                  Download your theme and generation settings
                </p>
              </div>
            </div>
            <button
              onClick={handleExportConfig}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              <Download className="h-4 w-4" />
              Export
            </button>
          </div>

          <div className="flex items-center justify-between rounded-md border border-border p-4">
            <div className="flex items-center gap-3">
              <FileJson className="h-5 w-5 text-muted-foreground" />
              <div>
                <h3 className="font-medium">Export API Keys</h3>
                <p className="text-xs text-muted-foreground">
                  Warning: Contains sensitive information
                </p>
              </div>
            </div>
            <button
              onClick={handleExportApiKeys}
              className="inline-flex items-center gap-2 rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-accent"
            >
              <Download className="h-4 w-4" />
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Import Section */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border p-4">
          <h2 className="text-lg font-semibold">Import Data</h2>
          <p className="text-sm text-muted-foreground">
            Restore your data from a previously exported JSON file.
          </p>
        </div>
        <div className="space-y-3 p-4">
          <div className="flex items-center justify-between rounded-md border border-border p-4">
            <div className="flex items-center gap-3">
              <Upload className="h-5 w-5 text-muted-foreground" />
              <div>
                <h3 className="font-medium">Import Drafts</h3>
                <p className="text-xs text-muted-foreground">
                  Merge drafts from a backup file
                </p>
              </div>
            </div>
            <button
              onClick={() => importInputRef.current?.click()}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              <Upload className="h-4 w-4" />
              Import
            </button>
            <input
              ref={importInputRef}
              type="file"
              accept="application/json"
              onChange={handleImportDrafts}
              className="hidden"
            />
          </div>

          <div className="flex items-center justify-between rounded-md border border-border p-4">
            <div className="flex items-center gap-3">
              <Upload className="h-5 w-5 text-muted-foreground" />
              <div>
                <h3 className="font-medium">Import Configuration</h3>
                <p className="text-xs text-muted-foreground">
                  Restore theme and generation settings
                </p>
              </div>
            </div>
            <button
              onClick={() => exportInputRef.current?.click()}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              <Upload className="h-4 w-4" />
              Import
            </button>
            <input
              ref={exportInputRef}
              type="file"
              accept="application/json"
              onChange={handleImportConfig}
              className="hidden"
            />
          </div>
        </div>
      </div>

      {/* Clear Section */}
      <div className="rounded-lg border border-destructive/50 bg-destructive/5">
        <div className="border-b border-destructive/50 p-4">
          <h2 className="text-lg font-semibold text-destructive">Danger Zone</h2>
          <p className="text-sm text-muted-foreground">
            Permanently delete all stored data. This action cannot be undone.
          </p>
        </div>
        <div className="p-4">
          {!showConfirmClear ? (
            <button
              onClick={() => setShowConfirmClear(true)}
              disabled={isClearing}
              className="inline-flex items-center gap-2 rounded-md border border-destructive px-4 py-2 text-sm font-medium text-destructive hover:bg-destructive/10 disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" />
              Clear All Data
            </button>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-destructive">
                Are you sure? This will permanently delete:
              </p>
              <ul className="space-y-1 text-sm text-destructive ml-4 list-disc">
                <li>All {stats?.drafts || 0} drafts</li>
                <li>All {stats?.apiKeys || 0} API keys</li>
                <li>All configuration settings</li>
              </ul>
              <div className="flex gap-3">
                <button
                  onClick={handleClearAll}
                  disabled={isClearing}
                  className="inline-flex items-center gap-2 rounded-md bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground hover:bg-destructive/90 disabled:opacity-50"
                >
                  {isClearing ? (
                    <>
                      <span className="h-4 w-4 animate-spin border-2 border-current border-t-transparent rounded-full" />
                      Clearing...
                    </>
                  ) : (
                    <>
                      <Trash2 className="h-4 w-4" />
                      Yes, Clear Everything
                    </>
                  )}
                </button>
                <button
                  onClick={() => setShowConfirmClear(false)}
                  disabled={isClearing}
                  className="inline-flex items-center gap-2 rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-accent disabled:opacity-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
