export interface CheckpointSessionPlaceholderProps {
  reviewId?: string;
  resumeFromAsset?: string;
}

export function CheckpointSessionPlaceholder({
  reviewId,
  resumeFromAsset,
}: CheckpointSessionPlaceholderProps) {
  return (
    <section className="rounded-lg border border-dashed border-border bg-card/60 p-4 text-sm text-muted-foreground">
      <h3 className="font-semibold text-foreground">Checkpoint Session Placeholder</h3>
      <p className="mt-2">
        Planned integration point for pause, resume, and restart from approved assets.
      </p>
      <p className="mt-2">
        Review: {reviewId ?? 'pending'} · Resume from: {resumeFromAsset ?? 'first incomplete asset'}
      </p>
    </section>
  );
}

export default CheckpointSessionPlaceholder;