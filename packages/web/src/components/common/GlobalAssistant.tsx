import { useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Loader2, MessageCircle, Send, X } from 'lucide-react';
import { api, type ChatMessage } from '@char-gen/shared';
import { useAssistantContext } from './AssistantContext';

const screenTitles: Record<string, string> = {
  '/': 'Home',
  '/generate': 'Generate Character',
  '/seed-generator': 'Seed Generator',
  '/validation': 'Validation',
  '/batch': 'Batch',
  '/drafts': 'Drafts',
  '/templates': 'Templates',
  '/blueprints': 'Blueprints',
  '/similarity': 'Compare Characters',
  '/offspring': 'Offspring Generator',
  '/lineage': 'Lineage',
  '/settings': 'Settings',
};

export default function GlobalAssistant() {
  const location = useLocation();
  const { screenContext: liveScreenContext } = useAssistantContext();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');

  const draftId = location.pathname.startsWith('/drafts/')
    ? decodeURIComponent(location.pathname.replace('/drafts/', '').split('/')[0] || '')
    : undefined;

  const screenContext = useMemo(() => {
    const matchedPath = Object.keys(screenTitles)
      .filter((path) => location.pathname === path || location.pathname.startsWith(`${path}/`))
      .sort((left, right) => right.length - left.length)[0] || location.pathname;

    return {
      screen_name: matchedPath.replace(/^\//, '') || 'home',
      screen_title: screenTitles[matchedPath] || matchedPath,
      route: location.pathname,
      draft_id: draftId || '',
      ...liveScreenContext,
    };
  }, [draftId, liveScreenContext, location.pathname]);

  const ensureWelcome = () => {
    if (messages.length === 0) {
      setMessages([
        {
          role: 'assistant',
          content: `You're on ${screenContext.screen_title}. Ask for help with this screen, workflow steps, or content strategy.${draftId ? ' I can also use the current draft as context.' : ''}`,
        },
      ]);
    }
  };

  const handleOpen = () => {
    setIsOpen(true);
    ensureWelcome();
  };

  const handleSend = async () => {
    if (!input.trim() || isStreaming) {
      return;
    }

    const userMessage: ChatMessage = { role: 'user', content: input.trim() };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput('');
    setIsStreaming(true);
    setStreamingContent('');

    try {
      const stream = api.chat({
        draft_id: draftId,
        messages: nextMessages,
        screen_context: screenContext,
      });

      let fullContent = '';
      stream.subscribe((event) => {
        if (event.event === 'chunk' && 'content' in event.data) {
          const data = event.data as { content: string };
          fullContent += data.content;
          setStreamingContent(fullContent);
        }
        if (event.event === 'complete') {
          setMessages((previous) => [...previous, { role: 'assistant', content: fullContent }]);
          setStreamingContent('');
        }
        if (event.event === 'error') {
          const data = event.data as { error: string };
          setMessages((previous) => [...previous, { role: 'assistant', content: `Error: ${data.error}` }]);
        }
      });

      stream.onComplete_(() => setIsStreaming(false));
      stream.onError_((error) => {
        setIsStreaming(false);
        setMessages((previous) => [...previous, { role: 'assistant', content: `Error: ${error}` }]);
      });

      await stream.start();
    } catch (error) {
      setIsStreaming(false);
      setMessages((previous) => [...previous, { role: 'assistant', content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}` }]);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={handleOpen}
        className="fixed bottom-6 right-6 z-50 inline-flex items-center gap-2 rounded-full bg-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-lg hover:bg-primary/90"
      >
        <MessageCircle className="h-5 w-5" />
        Assistant
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex max-h-[640px] w-96 flex-col rounded-lg border border-border bg-card shadow-xl">
      <div className="flex items-center justify-between border-b border-border p-4">
        <div>
          <div className="font-semibold">Assistant</div>
          <div className="text-xs text-muted-foreground">{screenContext.screen_title}</div>
        </div>
        <button onClick={() => setIsOpen(false)} className="text-muted-foreground hover:text-foreground">
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-4 min-h-[240px] max-h-[420px]">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`text-sm ${message.role === 'user' ? 'text-right' : ''}`}>
            <div className={`inline-block max-w-[85%] rounded-lg px-3 py-2 ${message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
              {message.content}
            </div>
          </div>
        ))}
        {streamingContent && (
          <div className="text-sm">
            <div className="inline-block max-w-[85%] rounded-lg bg-muted px-3 py-2">{streamingContent}</div>
          </div>
        )}
      </div>

      <div className="border-t border-border p-3">
        <div className="mb-2 text-xs text-muted-foreground">
          {draftId ? `Using draft context: ${draftId}` : 'Using current screen context only'}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                void handleSend();
              }
            }}
            placeholder="Ask for help on this screen..."
            className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
            disabled={isStreaming}
          />
          <button
            onClick={() => void handleSend()}
            disabled={!input.trim() || isStreaming}
            className="inline-flex items-center justify-center rounded-md bg-primary px-3 py-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {isStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}