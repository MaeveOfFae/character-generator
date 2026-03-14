import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { configManager } from '@/lib/config/manager';
import { GETTING_STARTED_GUIDE_ID, GETTING_STARTED_TOUR_ID } from '@/lib/help';
import { GuidedTourProvider, useGuidedTour } from './GuidedTourContext';

function Probe() {
  const location = useLocation();
  const {
    activeTourId,
    activeStepIndex,
    helpState,
    goToNextStep,
    restartTour,
    startTour,
  } = useGuidedTour();

  return (
    <div>
      <div data-testid="pathname">{location.pathname}</div>
      <div data-testid="active-tour">{activeTourId ?? 'none'}</div>
      <div data-testid="active-step">{String(activeStepIndex)}</div>
      <div data-testid="first-run-completed">{String(helpState.first_run_completed)}</div>
      <div data-testid="completed-guides">{helpState.completed_guides.join(',')}</div>
      <div data-testid="completed-tours">{helpState.completed_tours.join(',')}</div>
      <button type="button" onClick={() => startTour(GETTING_STARTED_TOUR_ID)}>
        Start Getting Started
      </button>
      <button type="button" onClick={() => goToNextStep()}>
        Next Step
      </button>
      <button type="button" onClick={() => restartTour(GETTING_STARTED_TOUR_ID)}>
        Restart Getting Started
      </button>
    </div>
  );
}

function renderProvider(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <GuidedTourProvider>
        <Probe />
      </GuidedTourProvider>
    </MemoryRouter>
  );
}

describe('GuidedTourContext', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    configManager.clearAll();
  });

  it('persists active tour progress to session storage and restores it on remount', async () => {
    const view = renderProvider('/');

    fireEvent.click(screen.getByRole('button', { name: 'Start Getting Started' }));
    fireEvent.click(screen.getByRole('button', { name: 'Next Step' }));

    await waitFor(() => {
      expect(screen.getByTestId('pathname')).toHaveTextContent('/settings');
    });

    expect(screen.getByTestId('active-tour')).toHaveTextContent(GETTING_STARTED_TOUR_ID);
    expect(screen.getByTestId('active-step')).toHaveTextContent('1');
    expect(sessionStorage.getItem('eidolon.web.activeTour')).toBe(
      JSON.stringify({ activeTourId: GETTING_STARTED_TOUR_ID, activeStepIndex: 1 })
    );

    view.unmount();

    renderProvider('/settings');

    expect(screen.getByTestId('active-tour')).toHaveTextContent(GETTING_STARTED_TOUR_ID);
    expect(screen.getByTestId('active-step')).toHaveTextContent('1');
    expect(screen.getByTestId('pathname')).toHaveTextContent('/settings');
  });

  it('restarting getting started clears completion state and returns to the first step', async () => {
    configManager.updateHelpState({
      first_run_completed: true,
      completed_guides: [GETTING_STARTED_GUIDE_ID],
      completed_tours: [GETTING_STARTED_TOUR_ID],
    });

    renderProvider('/settings');

    expect(screen.getByTestId('first-run-completed')).toHaveTextContent('true');
    expect(screen.getByTestId('completed-guides')).toHaveTextContent(GETTING_STARTED_GUIDE_ID);
    expect(screen.getByTestId('completed-tours')).toHaveTextContent(GETTING_STARTED_TOUR_ID);

    fireEvent.click(screen.getByRole('button', { name: 'Restart Getting Started' }));

    await waitFor(() => {
      expect(screen.getByTestId('pathname')).toHaveTextContent('/');
    });

    expect(screen.getByTestId('active-tour')).toHaveTextContent(GETTING_STARTED_TOUR_ID);
    expect(screen.getByTestId('active-step')).toHaveTextContent('0');
    expect(screen.getByTestId('first-run-completed')).toHaveTextContent('false');
    expect(screen.getByTestId('completed-guides')).toHaveTextContent('');
    expect(screen.getByTestId('completed-tours')).toHaveTextContent('');
  });
});