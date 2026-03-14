import { useEffect, useState } from 'react';
import { CheckCircle2, ChevronLeft, ChevronRight, Compass, MapPinned, ScanSearch, X } from 'lucide-react';
import { getGuidedTour, isGuidedTourStepActive } from '@/lib/help';
import { useGuidedTour } from './GuidedTourContext';
import { useLocation } from 'react-router-dom';

const ACTIVE_TOUR_TARGET_SELECTOR = '[data-guided-tour-active="true"]';

export default function GuidedTourOverlay() {
  const location = useLocation();
  const {
    activeTourId,
    activeStepIndex,
    closeTour,
    goToCurrentStep,
    goToNextStep,
    goToPreviousStep,
  } = useGuidedTour();
  const [targetFound, setTargetFound] = useState(false);

  const activeTour = activeTourId ? getGuidedTour(activeTourId) : null;
  const activeStep = activeTour?.steps[activeStepIndex] ?? null;

  useEffect(() => {
    const previousTarget = document.querySelector<HTMLElement>(ACTIVE_TOUR_TARGET_SELECTOR);
    previousTarget?.removeAttribute('data-guided-tour-active');

    if (!activeStep) {
      setTargetFound(false);
      return;
    }

    const isExpectedPage = isGuidedTourStepActive(location.pathname, activeStep);

    if (!isExpectedPage || !activeStep.targetId) {
      setTargetFound(false);
      return;
    }

    const target = document.querySelector<HTMLElement>(`[data-tour-anchor="${activeStep.targetId}"]`);
    if (!target) {
      setTargetFound(false);
      return;
    }

    target.setAttribute('data-guided-tour-active', 'true');
    target.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
    setTargetFound(true);

    return () => {
      target.removeAttribute('data-guided-tour-active');
    };
  }, [activeStep, location.pathname]);

  if (!activeTour || !activeStep) {
    return null;
  }

  const isExpectedPage = isGuidedTourStepActive(location.pathname, activeStep);
  const isLastStep = activeStepIndex === activeTour.steps.length - 1;

  return (
    <>
      <div className="fixed inset-0 z-[70] bg-black/55" onClick={closeTour} />
      <section className="fixed inset-x-3 bottom-3 z-[80] max-h-[calc(100dvh-1.5rem)] overflow-hidden rounded-3xl border border-border/60 bg-card/95 shadow-2xl shadow-black/40 backdrop-blur-md sm:inset-x-auto sm:right-4 sm:w-[28rem]">
        <div className="flex items-start justify-between gap-4 border-b border-border/50 px-5 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">Guided Tour</p>
            <h2 className="mt-1 text-lg font-semibold text-foreground">{activeTour.title}</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Step {activeStepIndex + 1} of {activeTour.steps.length}
            </p>
          </div>
          <button
            type="button"
            onClick={closeTour}
            className="rounded-lg border border-border/60 bg-background/50 p-2 text-muted-foreground transition-colors hover:border-primary/40 hover:text-primary"
            aria-label="Close guided tour"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="max-h-[calc(100dvh-12rem)] overflow-y-auto px-5 py-4">
          <div className="rounded-2xl border border-primary/20 bg-primary/5 p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-primary">
              <Compass className="h-4 w-4" />
              {activeStep.routeLabel}
            </div>
            <h3 className="mt-2 text-xl font-semibold text-foreground">{activeStep.title}</h3>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{activeStep.description}</p>
          </div>

          <div className="mt-4 rounded-2xl border border-border/50 bg-background/40 p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-foreground">
              <MapPinned className="h-4 w-4 text-primary" />
              {isExpectedPage ? 'You are on the expected page.' : `This step expects ${activeStep.routeLabel}.`}
            </div>
            {!isExpectedPage && (
              <button
                type="button"
                onClick={goToCurrentStep}
                className="mt-3 inline-flex items-center gap-2 rounded-lg border border-border/60 bg-card/70 px-3 py-2 text-sm font-medium text-foreground transition-colors hover:border-primary/40 hover:text-primary"
              >
                Return to this step
                <ChevronRight className="h-4 w-4" />
              </button>
            )}
          </div>

          {activeStep.targetLabel && isExpectedPage && (
            <div className="mt-4 rounded-2xl border border-border/50 bg-background/40 p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                <ScanSearch className="h-4 w-4 text-primary" />
                {targetFound ? `Highlighted target: ${activeStep.targetLabel}` : `Looking for ${activeStep.targetLabel}`}
              </div>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {targetFound
                  ? 'The active control or section has been outlined on the page so you can orient yourself without hunting for it.'
                  : 'If the highlighted target is not visible yet, stay on this page and give the layout a moment to settle.'}
              </p>
            </div>
          )}

          <div className="mt-4 space-y-3">
            {activeStep.bullets.map((bullet) => (
              <div key={bullet} className="flex items-start gap-3 rounded-xl border border-border/50 bg-background/40 p-4 text-sm text-muted-foreground">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                <p className="leading-6">{bullet}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-border/50 px-5 py-4">
          <button
            type="button"
            onClick={goToPreviousStep}
            disabled={activeStepIndex === 0}
            className="inline-flex items-center gap-2 rounded-lg border border-border/60 bg-background/50 px-3 py-2 text-sm font-medium text-foreground transition-colors hover:border-primary/40 hover:text-primary disabled:cursor-not-allowed disabled:opacity-50"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </button>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={closeTour}
              className="inline-flex items-center gap-2 rounded-lg border border-border/60 bg-background/50 px-3 py-2 text-sm font-medium text-foreground transition-colors hover:border-primary/40 hover:text-primary"
            >
              Leave tour
            </button>
            <button
              type="button"
              onClick={goToNextStep}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              {isLastStep ? 'Finish tour' : 'Next step'}
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </section>
    </>
  );
}