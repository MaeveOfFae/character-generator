import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { FolderOpen, Star, Clock } from 'lucide-react';
import { api } from '@/lib/api';
import DraftComparisonPlaceholder from './DraftComparisonPlaceholder';
import LibraryCollectionsPlaceholder from './LibraryCollectionsPlaceholder';
import ReviewChecklistPlaceholder from './ReviewChecklistPlaceholder';
import VersionHistoryPlaceholder from './VersionHistoryPlaceholder';

export default function Drafts() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading drafts...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-destructive">
        Error loading drafts: {error.message}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Drafts</h1>
        <p className="text-muted-foreground">
          Browse and manage your saved characters
        </p>
      </div>

      {/* Stats */}
      {data?.stats && (
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="text-2xl font-bold">{data.stats.total_drafts}</div>
            <div className="text-sm text-muted-foreground">Total Drafts</div>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="text-2xl font-bold">{data.stats.favorites}</div>
            <div className="text-sm text-muted-foreground">Favorites</div>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="text-2xl font-bold">
              {Object.keys(data.stats.by_genre).length}
            </div>
            <div className="text-sm text-muted-foreground">Genres</div>
          </div>
        </div>
      )}

      <section className="rounded-lg border border-dashed border-border bg-card/50 p-5">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Planned Draft Workflows</h2>
            <p className="text-sm text-muted-foreground">
              Disabled cards for comparison, review, collections, and version history live here until the full flows are wired.
            </p>
          </div>
          <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
            Planned
          </span>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <LibraryCollectionsPlaceholder
            collectionName={data?.drafts.length ? 'all drafts' : 'empty library'}
          />
          <DraftComparisonPlaceholder
            leftDraftId={data?.drafts[0]?.review_id}
            rightDraftId={data?.drafts[1]?.review_id}
          />
          <ReviewChecklistPlaceholder draftId={data?.drafts[0]?.review_id} />
          <VersionHistoryPlaceholder draftId={data?.drafts[0]?.review_id} />
        </div>
      </section>

      {/* Draft List */}
      <div className="space-y-2">
        {data?.drafts.length === 0 ? (
          <div className="rounded-lg border border-border bg-card p-8 text-center">
            <FolderOpen className="mx-auto h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 text-lg font-semibold">No drafts yet</h3>
            <p className="text-muted-foreground">
              Generate your first character to get started
            </p>
            <div className="mt-6 text-left">
              <LibraryCollectionsPlaceholder collectionName="first-run library" />
            </div>
            <Link
              to="/generate"
              className="mt-4 inline-block rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
            >
              Generate Character
            </Link>
          </div>
        ) : (
          data?.drafts.map((draft) => (
            <Link
              key={draft.review_id}
              to={`/drafts/${encodeURIComponent(draft.review_id)}`}
              className="flex items-center gap-4 rounded-lg border border-border bg-card p-4 transition-colors hover:bg-accent"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium truncate">
                    {draft.character_name || draft.seed}
                  </h3>
                  {draft.favorite && <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />}
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>{draft.template_name || 'Default Template'}</span>
                  <span>{draft.mode}</span>
                  {draft.created && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(draft.created).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {draft.tags?.slice(0, 2).map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-muted px-2 py-0.5 text-xs"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
