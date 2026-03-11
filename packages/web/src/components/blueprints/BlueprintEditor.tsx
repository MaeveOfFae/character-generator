import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Save, FileText, Eye, Edit3, X } from 'lucide-react';
import type { Blueprint } from '@char-gen/shared';
import { api } from '@/lib/api';
import ReactMarkdown from 'react-markdown';

interface BlueprintFormData {
  name: string;
  description: string;
  invokable: boolean;
  versionMajor: number;
  versionMinor: number;
}

export default function BlueprintEditor() {
  const params = useParams();
  const blueprintPathParam = params['*'];
  const [blueprint, setBlueprint] = useState<Blueprint | null>(null);
  const [formData, setFormData] = useState<BlueprintFormData>({
    name: '',
    description: '',
    invokable: true,
    versionMajor: 1,
    versionMinor: 0,
  });
  const [content, setContent] = useState('');
  const [showPreview, setShowPreview] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modified, setModified] = useState(false);

  // Load blueprint on mount
  useEffect(() => {
    const loadBlueprint = async () => {
      if (!blueprintPathParam) return;

      try {
        const path = decodeURIComponent(blueprintPathParam);
        const data = await api.getBlueprint(path);
        setBlueprint(data);

        // Parse version from "X.Y" format
        const [major = 1, minor = 0] = data.version.split('.').map(Number);
        setFormData({
          name: data.name,
          description: data.description,
          invokable: data.invokable,
          versionMajor: major,
          versionMinor: minor,
        });

        // Split content into frontmatter and body
        const blueprintContent = data.content;
        const frontmatterEnd = blueprintContent.indexOf('---', blueprintContent.indexOf('---') + 3);
        if (frontmatterEnd > 0) {
          setContent(blueprintContent.slice(frontmatterEnd + 3).trim());
        } else {
          setContent(blueprintContent);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load blueprint');
      }
    };

    loadBlueprint();
  }, [blueprintPathParam]);

  // Track modifications
  useEffect(() => {
    if (blueprint) {
      const hasChanges =
        formData.name !== blueprint.name ||
        formData.description !== blueprint.description ||
        formData.invokable !== blueprint.invokable ||
        `${formData.versionMajor}.${formData.versionMinor}` !== blueprint.version ||
        content !== blueprint.content;
      setModified(hasChanges);
    }
  }, [formData, content, blueprint]);

  const handleSave = async () => {
    if (!blueprintPathParam || !blueprint) return;

    setIsSaving(true);
    setError(null);

    try {
      // Combine frontmatter and content
      const fullContent = `---
name: ${formData.name}
description: ${formData.description}
invokable: ${formData.invokable}
version: ${formData.versionMajor}.${formData.versionMinor}
---
${content.trim()}`;

      const updated = await api.updateBlueprint(blueprint.path, fullContent);
      setBlueprint(updated);
      setModified(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save blueprint');
    } finally {
      setIsSaving(false);
    }
  };

  const generateYAMLPreview = () => {
    return `---
name: ${formData.name}
description: ${formData.description}
invokable: ${formData.invokable}
version: ${formData.versionMajor}.${formData.versionMinor}
---`;
  };

  if (error) {
    return (
      <div className="rounded-lg border border-destructive bg-destructive/10 p-6">
        <div className="flex items-center gap-2 text-destructive mb-4">
          <X className="h-5 w-5" />
          <h3 className="font-semibold">Error</h3>
        </div>
        <p className="text-sm text-destructive/80 mb-4">{error}</p>
        <Link
          to="/blueprints"
          className="inline-flex items-center gap-2 text-sm text-destructive hover:text-destructive/80"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Blueprints
        </Link>
      </div>
    );
  }

  if (!blueprint) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading blueprint...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link
            to="/blueprints"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
          <span className="text-muted-foreground">/</span>
          <div>
            <h1 className="text-2xl font-bold">{formData.name}</h1>
            <p className="text-sm text-muted-foreground">
              {blueprint.category}
            </p>
            <p className="text-sm text-muted-foreground">
              {blueprint.path}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm hover:bg-accent"
          >
            {showPreview ? <Edit3 className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            {showPreview ? 'Edit' : 'Preview'}
          </button>
          <button
            onClick={handleSave}
            disabled={!modified || isSaving}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            <Save className="h-4 w-4" />
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {/* Modified Warning */}
      {modified && (
        <div className="rounded-lg border border-yellow-500 bg-yellow-500/10 px-4 py-2 text-sm text-yellow-500">
          You have unsaved changes
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Frontmatter Editor */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Frontmatter
          </h2>

          <div className="rounded-lg border border-border bg-card p-4 space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium mb-1.5">Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="blueprint_name"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium mb-1.5">Description *</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Brief description of this blueprint"
              />
            </div>

            {/* Version */}
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium mb-1.5">Version (Major)</label>
                <input
                  type="number"
                  min="0"
                  value={formData.versionMajor}
                  onChange={(e) => setFormData({ ...formData, versionMajor: parseInt(e.target.value) || 0 })}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium mb-1.5">Version (Minor)</label>
                <input
                  type="number"
                  min="0"
                  value={formData.versionMinor}
                  onChange={(e) => setFormData({ ...formData, versionMinor: parseInt(e.target.value) || 0 })}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>
            </div>

            {/* Invokable */}
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={formData.invokable}
                onChange={(e) => setFormData({ ...formData, invokable: e.target.checked })}
                className="rounded border-input"
              />
              Invokable (can be used as a tool)
            </label>

            {/* YAML Preview */}
            <div>
              <label className="block text-sm font-medium mb-1.5">YAML Preview</label>
              <pre className="rounded-md bg-muted p-3 text-xs font-mono overflow-x-auto">
                {generateYAMLPreview()}
              </pre>
            </div>
          </div>
        </div>

        {/* Markdown Content Editor/Preview */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Content
          </h2>

          {showPreview ? (
            <div className="rounded-lg border border-border bg-card p-4">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown>{content || '*No content yet*'}</ReactMarkdown>
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-border bg-card">
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="w-full min-h-[500px] rounded-md border-0 bg-transparent p-4 text-sm font-mono focus-visible:outline-none"
                placeholder="Enter markdown content here..."
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
