import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import ContextualHelpPanel from './ContextualHelpPanel';
import type { HelpTopic, PageHelpEntry } from '../../lib/help';

const entry: PageHelpEntry = {
  id: 'generate',
  match: '/generate',
  matchMode: 'exact',
  title: 'Generate help',
  summary: 'Generation guidance summary.',
  keyActions: ['Choose a template before refining the seed.'],
  pitfalls: ['Do not skip provider setup.'],
  actions: [{ label: 'Open Settings', to: '/settings' }],
  relatedTopicIds: ['api-key-setup'],
};

const topics: HelpTopic[] = [
  {
    id: 'api-key-setup',
    title: 'API key setup without guesswork',
    category: 'Getting Started',
    summary: 'Provider setup summary.',
    bullets: ['Choose the provider you really use.'],
    actions: [{ label: 'Open Settings', to: '/settings' }],
  },
];

describe('ContextualHelpPanel', () => {
  it('renders the help entry and related topics when open', () => {
    render(
      <MemoryRouter>
        <ContextualHelpPanel entry={entry} topics={topics} isOpen onClose={() => {}} />
      </MemoryRouter>
    );

    expect(screen.getByText('Generate help')).toBeInTheDocument();
    expect(screen.getByText('Generation guidance summary.')).toBeInTheDocument();
    expect(screen.getByText('Open Help Center')).toBeInTheDocument();
    expect(screen.getByText('API key setup without guesswork')).toBeInTheDocument();
  });
});