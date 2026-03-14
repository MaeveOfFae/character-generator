import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import Review from './Review';
import { getGuidedTour, REVIEW_EXPORT_TOUR_ID } from '@/lib/help';

const mockUseQuery = vi.fn();
const mockUseMutation = vi.fn();
const mockUseQueryClient = vi.fn();
const mockUseGuidedTour = vi.fn();

vi.mock('@tanstack/react-query', () => ({
  useQuery: () => mockUseQuery(),
  useMutation: () => mockUseMutation(),
  useQueryClient: () => mockUseQueryClient(),
}));

vi.mock('../common/ExportModal', () => ({
  default: ({ onClose }: { onClose: () => void }) => (
    <div data-testid="export-modal">
      <span>Export Modal</span>
      <button type="button" onClick={onClose}>Close Export Modal</button>
    </div>
  ),
}));

vi.mock('../common/ChatPanel', () => ({
  default: () => null,
}));

vi.mock('../common/InlineHelpTip', () => ({
  default: () => null,
}));

vi.mock('../common/useAssistantContext', () => ({
  useAssistantScreenContext: () => undefined,
}));

vi.mock('../common/GuidedTourContext', () => ({
  useGuidedTour: () => mockUseGuidedTour(),
}));

const draftResponse = {
  metadata: {
    seed: 'test-seed',
    favorite: false,
    mode: 'NSFW',
    template_name: 'Official V2/V3',
    tags: [],
    parent_drafts: [],
  },
  assets: {
    system_prompt: 'hello',
  },
};

function createMutationResult() {
  return {
    mutate: vi.fn(),
    isPending: false,
  };
}

function renderReview() {
  return render(
    <MemoryRouter initialEntries={['/drafts/review-1']}>
      <Routes>
        <Route path="/drafts/:id" element={<Review />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('Review export modal behavior', () => {
  beforeEach(() => {
    mockUseQuery.mockReset();
    mockUseMutation.mockReset();
    mockUseQueryClient.mockReset();
    mockUseGuidedTour.mockReset();

    mockUseQuery.mockReturnValue({
      data: draftResponse,
      isLoading: false,
      error: null,
    });

    mockUseMutation.mockImplementation(() => createMutationResult());
    mockUseQueryClient.mockReturnValue({
      invalidateQueries: vi.fn(),
    });
  });

  it('closes the export modal when leaving a tour-managed export step', async () => {
    const exportPresetStepIndex = getGuidedTour(REVIEW_EXPORT_TOUR_ID)?.steps.findIndex(
      (step) => step.targetId === 'export-preset-selection'
    );

    if (exportPresetStepIndex === undefined || exportPresetStepIndex < 0) {
      throw new Error('Review export tour is missing the export preset step');
    }

    mockUseGuidedTour.mockReturnValue({
      activeTourId: REVIEW_EXPORT_TOUR_ID,
      activeStepIndex: exportPresetStepIndex,
      isTourCompleted: vi.fn(() => false),
      restartTour: vi.fn(),
      startTour: vi.fn(),
    });

    const view = renderReview();

    expect(await screen.findByTestId('export-modal')).toBeInTheDocument();

    mockUseGuidedTour.mockReturnValue({
      activeTourId: null,
      activeStepIndex: 0,
      isTourCompleted: vi.fn(() => false),
      restartTour: vi.fn(),
      startTour: vi.fn(),
    });

    view.rerender(
      <MemoryRouter initialEntries={['/drafts/review-1']}>
        <Routes>
          <Route path="/drafts/:id" element={<Review />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.queryByTestId('export-modal')).not.toBeInTheDocument();
    });
  });

  it('keeps a manually opened export modal visible when no tour is active', async () => {
    mockUseGuidedTour.mockReturnValue({
      activeTourId: null,
      activeStepIndex: 0,
      isTourCompleted: vi.fn(() => false),
      restartTour: vi.fn(),
      startTour: vi.fn(),
    });

    const view = renderReview();

    fireEvent.click(screen.getByRole('button', { name: 'Export' }));
    expect(await screen.findByTestId('export-modal')).toBeInTheDocument();

    view.rerender(
      <MemoryRouter initialEntries={['/drafts/review-1']}>
        <Routes>
          <Route path="/drafts/:id" element={<Review />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('export-modal')).toBeInTheDocument();
  });
});