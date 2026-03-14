import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import GuidedTourOverlay from './GuidedTourOverlay';

const mockUseGuidedTour = vi.fn();

vi.mock('./GuidedTourContext', () => ({
  useGuidedTour: () => mockUseGuidedTour(),
}));

describe('GuidedTourOverlay', () => {
  beforeEach(() => {
    mockUseGuidedTour.mockReset();
    HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  it('can rerender from no active tour into an active step without crashing and highlights the target', () => {
    mockUseGuidedTour.mockReturnValue({
      activeTourId: null,
      activeStepIndex: 0,
      closeTour: vi.fn(),
      goToCurrentStep: vi.fn(),
      goToNextStep: vi.fn(),
      goToPreviousStep: vi.fn(),
    });

    const view = render(
      <MemoryRouter initialEntries={['/generate']}>
        <div>
          <div data-tour-anchor="generation-submit">Generate target</div>
          <GuidedTourOverlay />
        </div>
      </MemoryRouter>
    );

    expect(screen.queryByText('Guided Tour')).not.toBeInTheDocument();

    mockUseGuidedTour.mockReturnValue({
      activeTourId: 'getting-started',
      activeStepIndex: 3,
      closeTour: vi.fn(),
      goToCurrentStep: vi.fn(),
      goToNextStep: vi.fn(),
      goToPreviousStep: vi.fn(),
    });

    view.rerender(
      <MemoryRouter initialEntries={['/generate']}>
        <div>
          <div data-tour-anchor="generation-submit">Generate target</div>
          <GuidedTourOverlay />
        </div>
      </MemoryRouter>
    );

    expect(screen.getByText('Guided Tour')).toBeInTheDocument();
    expect(screen.getByText('Highlighted target: Generate Character button')).toBeInTheDocument();
    expect(screen.getByText('Generate target')).toHaveAttribute('data-guided-tour-active', 'true');
  });
});