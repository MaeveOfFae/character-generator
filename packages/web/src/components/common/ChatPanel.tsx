import { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, Loader2, X, Check, RefreshCw } from 'lucide-react';
import type { ChatMessage } from '@char-gen/shared';
import { api } from '@/lib/api';

interface ChatPanelProps {
  draftId: string;
  assetName?: string;
  onAssetRefined?: (assetName: string, newContent: string) => void;
}

export default function ChatPanel({ draftId, assetName, onAssetRefined }: ChatPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [refinedContent, setRefinedContent] = useState<string | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<string | undefined>(assetName);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([{
        role: 'assistant',
        content: `Hi! I'm here to help you refine this character${selectedAsset ? `'s ${selectedAsset.replace(/_/g, ' ')}` : ''}. What would you like to change or improve?`
      }]);
    }
  }, [isOpen, messages.length, selectedAsset]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage: ChatMessage = { role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);
    setStreamingContent('');

    try {
      const stream = api.chat({
        draft_id: draftId,
        messages: [...messages, userMessage],
        context_asset: selectedAsset,
      });

      let fullContent = '';
      stream.subscribe((event) => {
        if (event.event === 'chunk' && 'content' in event.data) {
          const data = event.data as { content: string };
          fullContent += data.content;
          setStreamingContent(fullContent);
        }
        if (event.event === 'complete') {
          setMessages(prev => [...prev, { role: 'assistant', content: fullContent }]);
          setStreamingContent('');
          setIsStreaming(false);
        }
      });

      stream.onError_((error) => {
        setIsStreaming(false);
        setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${error}` }]);
      });

      await stream.start();
    } catch (err) {
      setIsStreaming(false);
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err instanceof Error ? err.message : 'Unknown error'}` }]);
    }
  };

  const handleRefineAsset = async () => {
    if (!selectedAsset || !input.trim() || isStreaming) return;

    setIsStreaming(true);
    setStreamingContent('');
    const userMessage = input.trim();
    setInput('');

    try {
      const stream = api.refine({
        draft_id: draftId,
        asset: selectedAsset,
        message: userMessage,
      });

      let fullContent = '';
      stream.subscribe((event) => {
        if (event.event === 'chunk' && 'content' in event.data) {
          const data = event.data as { content: string };
          fullContent += data.content;
          setStreamingContent(fullContent);
        }
        if (event.event === 'complete') {
          setRefinedContent(fullContent);
          setMessages(prev => [...prev,
            { role: 'user', content: `Refine ${selectedAsset}: ${userMessage}` },
            { role: 'assistant', content: `Here's the updated ${selectedAsset.replace(/_/g, ' ')}:` }
          ]);
          setIsStreaming(false);
        }
      });

      stream.onError_((error) => {
        setIsStreaming(false);
        setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${error}` }]);
      });

      await stream.start();
    } catch {
      setIsStreaming(false);
    }
  };

  const handleApplyRefinement = () => {
    if (refinedContent && selectedAsset && onAssetRefined) {
      onAssetRefined(selectedAsset, refinedContent);
      setRefinedContent(null);
      setMessages(prev => [...prev, { role: 'assistant', content: '✅ Applied!' }]);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 inline-flex items-center gap-2 rounded-full bg-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-lg hover:bg-primary/90 z-50"
      >
        <MessageCircle className="h-5 w-5" />
        Refine with AI
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 max-h-[600px] rounded-lg border border-border bg-card shadow-xl flex flex-col z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <MessageCircle className="h-5 w-5 text-primary" />
          <span className="font-semibold">AI Refinement</span>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-muted-foreground hover:text-foreground"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Asset Selector */}
      <div className="p-3 border-b border-border">
        <label className="text-xs text-muted-foreground mb-1 block">Focus Asset</label>
        <select
          value={selectedAsset || ''}
          onChange={(e) => setSelectedAsset(e.target.value || undefined)}
          className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
        >
          <option value="">All assets</option>
          {assetName && (
            <option value={assetName}>{assetName.replace(/_/g, ' ')}</option>
          )}
        </select>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[200px] max-h-[300px]">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`text-sm ${msg.role === 'user' ? 'text-right' : ''}`}
          >
            <div
              className={`inline-block rounded-lg px-3 py-2 max-w-[85%] ${
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {streamingContent && (
          <div className="text-sm">
            <div className="inline-block rounded-lg px-3 py-2 max-w-[85%] bg-muted">
              {streamingContent}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Refined Content Preview */}
      {refinedContent && (
        <div className="p-3 border-t border-border">
          <div className="text-xs font-medium mb-2">Refined Content Preview:</div>
          <div className="max-h-32 overflow-y-auto rounded bg-muted p-2 text-xs font-mono whitespace-pre-wrap mb-2">
            {refinedContent}
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleApplyRefinement}
              className="flex-1 inline-flex items-center justify-center gap-1 rounded bg-green-600 px-3 py-1.5 text-xs text-white hover:bg-green-700"
            >
              <Check className="h-3 w-3" />
              Apply
            </button>
            <button
              onClick={() => setRefinedContent(null)}
              className="flex-1 inline-flex items-center justify-center gap-1 rounded bg-muted px-3 py-1.5 text-xs hover:bg-muted/80"
            >
              <X className="h-3 w-3" />
              Discard
            </button>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-3 border-t border-border">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder="Ask for changes..."
            className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            disabled={isStreaming}
          />
          <button
            onClick={selectedAsset ? handleRefineAsset : handleSend}
            disabled={!input.trim() || isStreaming}
            className="inline-flex items-center justify-center rounded-md bg-primary px-3 py-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {isStreaming ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
        {selectedAsset && (
          <div className="mt-2 text-xs text-muted-foreground">
            <RefreshCw className="h-3 w-3 inline mr-1" />
            Refine mode: updates will replace {selectedAsset.replace(/_/g, ' ')}
          </div>
        )}
      </div>
    </div>
  );
}
