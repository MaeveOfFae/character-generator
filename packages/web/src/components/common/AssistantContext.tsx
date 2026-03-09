import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';

type AssistantScreenContext = Record<string, unknown>;

interface AssistantContextValue {
  screenContext: AssistantScreenContext;
  setScreenContext: (ownerId: string, context: AssistantScreenContext, serializedContext: string) => void;
  clearScreenContext: (ownerId: string) => void;
}

const AssistantContext = createContext<AssistantContextValue | null>(null);

interface AssistantContextState {
  ownerId: string | null;
  screenContext: AssistantScreenContext;
  serializedContext: string;
}

export function AssistantContextProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AssistantContextState>({
    ownerId: null,
    screenContext: {},
    serializedContext: '',
  });

  const setScreenContext = useCallback((ownerId: string, context: AssistantScreenContext, serializedContext: string) => {
    setState((previous) => {
      if (previous.ownerId === ownerId && previous.serializedContext === serializedContext) {
        return previous;
      }

      return {
        ownerId,
        screenContext: context,
        serializedContext,
      };
    });
  }, []);

  const clearScreenContext = useCallback((ownerId: string) => {
    setState((previous) => {
      if (previous.ownerId !== ownerId) {
        return previous;
      }

      if (previous.ownerId === null && previous.serializedContext === '') {
        return previous;
      }

      return {
        ownerId: null,
        screenContext: {},
        serializedContext: '',
      };
    });
  }, []);

  const value = useMemo<AssistantContextValue>(
    () => ({
      screenContext: state.screenContext,
      setScreenContext,
      clearScreenContext,
    }),
    [clearScreenContext, setScreenContext, state.screenContext]
  );

  return <AssistantContext.Provider value={value}>{children}</AssistantContext.Provider>;
}

export function useAssistantContext() {
  const context = useContext(AssistantContext);
  if (!context) {
    throw new Error('useAssistantContext must be used within AssistantContextProvider');
  }
  return context;
}

export function useAssistantScreenContext(context: AssistantScreenContext) {
  const { setScreenContext, clearScreenContext } = useAssistantContext();
  const ownerIdRef = useRef(`screen-${Math.random().toString(36).slice(2)}`);
  const serializedContext = useMemo(() => JSON.stringify(context), [context]);
  const stableContext = useMemo(() => context, [serializedContext]);

  useEffect(() => {
    setScreenContext(ownerIdRef.current, stableContext, serializedContext);

    return () => {
      clearScreenContext(ownerIdRef.current);
    };
  }, [clearScreenContext, serializedContext, setScreenContext, stableContext]);
}