import { lazy, Suspense, useState, type ChangeEvent } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, Plus, Star, Trash2, ChevronDown, ChevronUp, ShieldCheck, Copy, Download, Pencil, Upload, Loader2 } from 'lucide-react';
import { api } from '@char-gen/shared';
import type { CreateTemplateRequest, Template, AssetDefinition } from '@char-gen/shared';
import { useAssistantScreenContext } from '../common/AssistantContext';
import { saveDownload } from '../../utils/download';

const TemplateWizard = lazy(() => import('./TemplateWizard'));

function TemplateWizardFallback() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3 text-sm text-muted-foreground shadow-lg">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading template editor...
      </div>
    </div>
  );
}

export default function Templates() {
  const [expandedTemplate, setExpandedTemplate] = useState<string | null>(null);
  const [showWizard, setShowWizard] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [editingTemplateData, setEditingTemplateData] = useState<CreateTemplateRequest | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [validationResults, setValidationResults] = useState<Record<string, { errors: string[]; warnings: string[] }>>({});
  const queryClient = useQueryClient();

  const { data: templates, isLoading, error } = useQuery({
    queryKey: ['templates'],
    queryFn: () => api.getTemplates(),
  });

  const deleteMutation = useMutation({
    mutationFn: (name: string) => api.deleteTemplate(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setFeedback({ type: 'success', message: 'Template deleted.' });
    },
    onError: (error: Error) => {
      setFeedback({ type: 'error', message: error.message });
    },
  });

  const duplicateMutation = useMutation({
    mutationFn: ({ name, newName }: { name: string; newName: string }) =>
      api.duplicateTemplate(name, { name: newName, version: '1.0' }),
    onSuccess: (template) => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setFeedback({ type: 'success', message: `Duplicated template as ${template.name}.` });
    },
    onError: (error: Error) => {
      setFeedback({ type: 'error', message: error.message });
    },
  });

  const importMutation = useMutation({
    mutationFn: (file: File) => api.importTemplate(file),
    onSuccess: (template) => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setFeedback({ type: 'success', message: `Imported template ${template.name}.` });
    },
    onError: (error: Error) => {
      setFeedback({ type: 'error', message: error.message });
    },
  });

  const toggleExpand = (name: string) => {
    setExpandedTemplate(expandedTemplate === name ? null : name);
  };

  const handleValidate = async (name: string) => {
    try {
      const result = await api.validateTemplate(name);
      setValidationResults((previous) => ({ ...previous, [name]: result }));
      setFeedback({
        type: result.errors.length > 0 ? 'error' : 'success',
        message:
          result.errors.length > 0 || result.warnings.length > 0
            ? `Validation finished for ${name}.`
            : `${name} is valid and ready to use.`,
      });
    } catch (error) {
      setFeedback({ type: 'error', message: error instanceof Error ? error.message : 'Validation failed' });
    }
  };

  const handleDuplicate = (name: string) => {
    const newName = prompt('Name for duplicated template:', `${name} Copy`);
    if (!newName?.trim()) {
      return;
    }
    duplicateMutation.mutate({ name, newName: newName.trim() });
  };

  const handleExport = async (name: string) => {
    try {
      const download = await api.exportTemplate(name);
      // Convert string content to Blob for download
      const blob = new Blob([download], { type: 'application/zip' });
      const downloadResponse = { blob, filename: `${name}.zip`, contentType: 'application/zip' } as const;
      const result = await saveDownload(
        downloadResponse,
        `${name.toLowerCase().replace(/[^a-z0-9]+/gi, '_')}.zip`
      );

      if (result.saved) {
        setFeedback({ type: 'success', message: `Exported ${name}.` });
      }
    } catch (error) {
      setFeedback({ type: 'error', message: error instanceof Error ? error.message : 'Export failed' });
    }
  };

  const handleEdit = async (template: Template) => {
    try {
      const response = await api.getTemplateBlueprintContents(template.name);
      setEditingTemplate(template);
      setEditingTemplateData({
        name: template.name,
        version: template.version,
        description: template.description,
        assets: template.assets,
        blueprint_contents: response.blueprint_contents,
      });
      setShowWizard(true);
    } catch (error) {
      setFeedback({ type: 'error', message: error instanceof Error ? error.message : 'Failed to load template editor' });
    }
  };

  const handleImportChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    importMutation.mutate(file);
    event.target.value = '';
  };

  const wizardInitialData: CreateTemplateRequest | undefined = editingTemplateData ?? undefined;

  useAssistantScreenContext({
    template_count: templates?.length ?? 0,
    expanded_template: expandedTemplate,
    editing_template: editingTemplate?.name ?? null,
    wizard_open: showWizard,
    validation_templates: Object.keys(validationResults),
    pending_action:
      deleteMutation.isPending
        ? 'delete'
        : duplicateMutation.isPending
          ? 'duplicate'
          : importMutation.isPending
            ? 'import'
            : null,
    feedback_message: feedback?.message ?? null,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading templates...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-destructive">
        Error loading templates: {error.message}
      </div>
    );
  }

  return (
    <>
      {showWizard && (
        <Suspense fallback={<TemplateWizardFallback />}>
          <TemplateWizard
            open={showWizard}
            onClose={() => {
              setShowWizard(false);
              setEditingTemplate(null);
              setEditingTemplateData(null);
            }}
            initialData={wizardInitialData}
            templateName={editingTemplate?.name}
          />
        </Suspense>
      )}

      <div className="space-y-6">
      {feedback && (
        <div className={`rounded-lg border p-4 text-sm ${feedback.type === 'error' ? 'border-destructive bg-destructive/10 text-destructive' : 'border-green-600/30 bg-green-600/10 text-green-700 dark:text-green-400'}`}>
          {feedback.message}
        </div>
      )}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Templates</h1>
          <p className="text-muted-foreground">
            Manage character generation templates
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-accent">
            <Upload className="h-4 w-4" />
            Import Template
            <input type="file" accept=".zip" className="hidden" onChange={handleImportChange} />
          </label>
          <button
            onClick={() => {
              setEditingTemplate(null);
              setShowWizard(true);
            }}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            Create Template
          </button>
        </div>
      </div>

      {/* Template List */}
      <div className="space-y-3">
        {templates?.map((template: Template) => (
          <div
            key={template.name}
            className="rounded-lg border border-border bg-card overflow-hidden"
          >
            {/* Header */}
            <button
              onClick={() => toggleExpand(template.name)}
              className="w-full flex items-center justify-between p-4 hover:bg-accent/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-muted-foreground" />
                <div className="text-left">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{template.name}</span>
                    {template.is_official && (
                      <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {template.description || `${template.assets.length} assets`}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">v{template.version}</span>
                {expandedTemplate === template.name ? (
                  <ChevronUp className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
            </button>

            {/* Expanded Content */}
            {expandedTemplate === template.name && (
              <div className="border-t border-border p-4 space-y-4">
                {/* Assets */}
                <div>
                  <h3 className="text-sm font-medium mb-2">Assets ({template.assets.length})</h3>
                  <div className="space-y-2">
                    {template.assets.map((asset: AssetDefinition) => (
                      <div
                        key={asset.name}
                        className="flex items-center justify-between text-sm p-2 rounded bg-muted/50"
                      >
                        <div className="flex items-center gap-2">
                          <span className={asset.required ? 'text-primary' : 'text-muted-foreground'}>
                            {asset.name}
                          </span>
                          {asset.depends_on.length > 0 && (
                            <span className="text-xs text-muted-foreground">
                              (depends: {asset.depends_on.join(', ')})
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {asset.required && (
                            <span className="text-xs px-2 py-0.5 rounded bg-primary/20 text-primary">
                              required
                            </span>
                          )}
                          {asset.blueprint_file && (
                            <span className="text-xs text-muted-foreground">
                              {asset.blueprint_file}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {validationResults[template.name] && (
                  <div className="rounded-lg border border-border bg-muted/30 p-3 text-sm">
                    {validationResults[template.name].errors.length === 0 && validationResults[template.name].warnings.length === 0 ? (
                      <p className="text-green-700 dark:text-green-400">No validation issues found.</p>
                    ) : (
                      <div className="space-y-2">
                        {validationResults[template.name].errors.length > 0 && (
                          <div>
                            <p className="font-medium text-destructive">Errors</p>
                            <ul className="list-disc pl-5 text-destructive">
                              {validationResults[template.name].errors.map((issue) => (
                                <li key={issue}>{issue}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {validationResults[template.name].warnings.length > 0 && (
                          <div>
                            <p className="font-medium text-yellow-700 dark:text-yellow-400">Warnings</p>
                            <ul className="list-disc pl-5 text-yellow-700 dark:text-yellow-400">
                              {validationResults[template.name].warnings.map((issue) => (
                                <li key={issue}>{issue}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex flex-wrap justify-end gap-3">
                    <button
                      onClick={() => handleValidate(template.name)}
                      className="inline-flex items-center gap-2 text-sm text-foreground hover:text-primary"
                    >
                      <ShieldCheck className="h-4 w-4" />
                      Validate
                    </button>
                    <button
                      onClick={() => handleDuplicate(template.name)}
                      disabled={duplicateMutation.isPending}
                      className="inline-flex items-center gap-2 text-sm text-foreground hover:text-primary disabled:opacity-50"
                    >
                      <Copy className="h-4 w-4" />
                      Duplicate
                    </button>
                    <button
                      onClick={() => handleExport(template.name)}
                      className="inline-flex items-center gap-2 text-sm text-foreground hover:text-primary"
                    >
                      <Download className="h-4 w-4" />
                      Export
                    </button>
                {!template.is_official && (
                    <button
                      onClick={() => handleEdit(template)}
                      className="inline-flex items-center gap-2 text-sm text-foreground hover:text-primary"
                    >
                      <Pencil className="h-4 w-4" />
                      Edit
                    </button>
                )}
                {!template.is_official && (
                    <button
                      onClick={() => {
                        if (confirm(`Delete template "${template.name}"?`)) {
                          deleteMutation.mutate(template.name);
                        }
                      }}
                      disabled={deleteMutation.isPending}
                      className="inline-flex items-center gap-2 text-sm text-destructive hover:text-destructive/80 disabled:opacity-50"
                    >
                      <Trash2 className="h-4 w-4" />
                      Delete Template
                    </button>
                )}
                  </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Empty State */}
      {templates?.length === 0 && (
        <div className="rounded-lg border border-border bg-card p-8 text-center">
          <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-semibold">No templates yet</h3>
          <p className="text-muted-foreground">
            Create your first template to customize character generation
          </p>
        </div>
      )}
      </div>
    </>
  );
}
