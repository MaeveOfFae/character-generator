import { fireEvent, render, screen } from '@testing-library/react';
import InlineHelpTip from './InlineHelpTip';

const mockUseGuidedTour = vi.fn();

vi.mock('./GuidedTourContext', () => ({
  useGuidedTour: () => mockUseGuidedTour(),
}));

describe('InlineHelpTip', () => {
  beforeEach(() => {
    mockUseGuidedTour.mockReset();
  });

  it('renders when inline tips are enabled and the tip is not dismissed', () => {
    const dismissTip = vi.fn();
    mockUseGuidedTour.mockReturnValue({
      dismissTip,
      helpState: {
        show_inline_tips: true,
        dismissed_tips: [],
      },
    });

    render(
      <InlineHelpTip
        tipId="sample-tip"
        title="Helpful title"
        description="Helpful description"
        actionLabel="Do thing"
        onAction={vi.fn()}
      />
    );

    expect(screen.getByText('Helpful title')).toBeInTheDocument();
    expect(screen.getByText('Helpful description')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Dismiss help tip' }));
    expect(dismissTip).toHaveBeenCalledWith('sample-tip');
  });

  it('does not render when inline tips are disabled or already dismissed', () => {
    mockUseGuidedTour.mockReturnValue({
      dismissTip: vi.fn(),
      helpState: {
        show_inline_tips: false,
        dismissed_tips: ['sample-tip'],
      },
    });

    const view = render(
      <InlineHelpTip
        tipId="sample-tip"
        title="Helpful title"
        description="Helpful description"
      />
    );

    expect(view.container).toBeEmptyDOMElement();
  });
});