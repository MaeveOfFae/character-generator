import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Star, Download, Trash2, Edit3, Check, X, ShieldCheck } from 'lucide-react';
import { api } from '@char-gen/shared';
import ExportModal from '../common/ExportModal';
import ChatPanel from '../common/ChatPanel';
import { useAssistantScreenContext } from '../common/AssistantContext';

export default function Review() {
  const { id } = useParams<{ id: string }>();
  const [showExportModal, setShowExportModal] = useState(false);
  const [editingAsset, setEditingAsset] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: draft, isLoading, error } = useQuery({
    queryKey: ['draft', id],
    queryFn: () => api.getDraft(decodeURIComponent(id || '')),
    enabled: !!id,
  });

  const toggleFavorite = useMutation({
    mutationFn: () => api.updateMetadata(decodeURIComponent(id || ''), {
      favorite: !draft?.metadata.favorite,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['draft', id] });
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
    },
  });

  const deleteDraft = useMutation({
    mutationFn: () => api.deleteDraft(decodeURIComponent(id || '')),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
      window.location.href = '/drafts';
    },
  });

  const saveAsset = useMutation({
    mutationFn: ({ assetName, content }: { assetName: string; content: string }) =>
      api.updateAsset(decodeURIComponent(id || ''), assetName, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['draft', id] });
      setEditingAsset(null);
      setEditContent('');
    },
  });

  const validateDraft = useMutation({
    mutationFn: () => api.validateDraft(decodeURIComponent(id || '')),
    onSuccess: (result) => {
      setValidationMessage(result.success ? 'Validation passed' : 'Validation failed');
    },
    onError: (error: Error) => {
      setValidationMessage(error.message);
    },
  });

  useAssistantScreenContext({
    draft_id: decodeURIComponent(id || ''),
    character_name: draft?.metadata.character_name || '',
    mode: draft?.metadata.mode || '',
    template_name: draft?.metadata.template_name || '',
    asset_names: draft ? Object.keys(draft.assets) : [],
    editing_asset: editingAsset || '',
    favorite: draft?.metadata.favorite ?? false,
    has_lineage: Boolean(draft?.metadata.parent_drafts?.length),
  });

  const handleEditAsset = (assetName: string) => {
    if (draft) {
      setEditingAsset(assetName);
      setEditContent(draft.assets[assetName]);
    }
  };

  const handleSaveAsset = () => {
    if (editingAsset) {
      saveAsset.mutate({ assetName: editingAsset, content: editContent });
    }
  };

  const handleCancelEdit = () => {
    setEditingAsset(null);
    setEditContent('');
  };

  const handleAssetRefined = (assetName: string, newContent: string) => {
    saveAsset.mutate({ assetName, content: newContent });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading draft...</div>
      </div>
    );
  }

  if (error || !draft) {
    return (
      <div className="space-y-4">
        <Link
          to="/drafts"
          className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Drafts
        </Link>
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-destructive">
          Error loading draft
        </div>
      </div>
    );
  }

  const assetNames = Object.keys(draft.assets);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Link
            to="/drafts"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Drafts
          </Link>
          <h1 className="text-3xl font-bold">
            {draft.metadata.character_name || draft.metadata.seed}
          </h1>
          <p className="text-muted-foreground">{draft.metadata.seed}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => validateDraft.mutate()}
            className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm hover:bg-accent"
          >
            <ShieldCheck className="h-4 w-4" />
            Validate
          </button>
          <button
            onClick={() => toggleFavorite.mutate()}
            className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm hover:bg-accent"
          >
            <Star className={`h-4 w-4 ${draft.metadata.favorite ? 'fill-yellow-500 text-yellow-500' : ''}`} />
            {draft.metadata.favorite ? 'Favorited' : 'Favorite'}
          </button>
          <button
            onClick={() => setShowExportModal(true)}
            className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm hover:bg-accent"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
          <button
            onClick={() => {
              if (confirm('Delete this character? This cannot be undone.')) {
                deleteDraft.mutate();
              }
            }}
            className="inline-flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive hover:bg-destructive/20"
          >
            <Trash2 className="h-4 w-4" />
            Delete
          </button>
        </div>
      </div>

      {validationMessage && (
        <div className="rounded-lg border border-border bg-card p-4 text-sm">
          {validationMessage}. <Link to="/validation" className="text-primary hover:underline">Open Validation screen</Link>
        </div>
      )}

      {/* Metadata */}
      <div className="flex flex-wrap gap-2">
        {draft.metadata.mode && (
          <span className="rounded-full bg-primary/10 px-3 py-1 text-sm text-primary">
            {draft.metadata.mode}
          </span>
        )}
        {draft.metadata.template_name && (
          <span className="rounded-full bg-secondary px-3 py-1 text-sm">
            {draft.metadata.template_name}
          </span>
        )}
        {draft.metadata.genre && (
          <span className="rounded-full bg-muted px-3 py-1 text-sm">
            {draft.metadata.genre}
          </span>
        )}
        {draft.metadata.tags?.map((tag) => (
          <span key={tag} className="rounded-full bg-muted px-3 py-1 text-sm">
            {tag}
          </span>
        ))}
      </div>

      {/* Lineage Info */}
      {draft.metadata.parent_drafts && draft.metadata.parent_drafts.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="text-sm font-medium mb-2">Lineage</h3>
          <p className="text-sm text-muted-foreground">
            Offspring of: {draft.metadata.parent_drafts.join(' + ')}
          </p>
        </div>
      )}

      {/* Assets */}
      <div className="space-y-4">
        {assetNames.map((assetName) => (
          <div key={assetName} className="space-y-2">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold capitalize">
                {assetName.replace(/_/g, ' ')}
              </h2>
              {editingAsset !== assetName && (
                <button
                  onClick={() => handleEditAsset(assetName)}
                  className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-2 py-1 text-xs hover:bg-accent"
                >
                  <Edit3 className="h-3 w-3" />
                  Edit
                </button>
              )}
            </div>
            <div className="rounded-lg border border-border bg-card p-4">
              {editingAsset === assetName ? (
                <div className="space-y-3">
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-full min-h-[200px] rounded-md border border-input bg-background p-3 text-sm font-mono focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={handleSaveAsset}
                      disabled={saveAsset.isPending}
                      className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                    >
                      {saveAsset.isPending ? (
                        <span className="animate-spin">⏳</span>
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                      Save
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-3 py-1.5 text-sm hover:bg-accent"
                    >
                      <X className="h-4 w-4" />
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <pre className="whitespace-pre-wrap text-sm font-mono">
                  {draft.assets[assetName]}
                </pre>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Export Modal */}
      {showExportModal && (
        <ExportModal
          draftId={decodeURIComponent(id || '')}
          characterName={draft.metadata.character_name || draft.metadata.seed}
          onClose={() => setShowExportModal(false)}
        />
      )}

      {/* Chat Panel for Refinement */}
      <ChatPanel
        draftId={decodeURIComponent(id || '')}
        onAssetRefined={handleAssetRefined}
      />
    </div>
  );
}
