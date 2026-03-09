import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, type ThemeOverride, type ThemePreset } from '@char-gen/shared';
import { applyThemeToDocument, resolveThemeColors } from '../../theme/theme';

interface ThemePreviewState {
  themeName: string;
  overrides?: ThemeOverride;
}

interface ThemeContextValue {
  themes: ThemePreset[];
  isLoading: boolean;
  previewTheme: (themeName: string, overrides?: ThemeOverride) => void;
  clearPreview: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preview, setPreview] = useState<ThemePreviewState | null>(null);

  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: () => api.getConfig(),
  });

  const { data: themes = [], isLoading } = useQuery({
    queryKey: ['themes'],
    queryFn: () => api.getThemes(),
  });

  const activeThemeName = preview?.themeName ?? config?.theme_name ?? 'dark';
  const activeOverrides = preview?.overrides ?? config?.theme;

  useEffect(() => {
    const preset = themes.find((theme) => theme.name === activeThemeName) ?? themes[0];
    const resolved = resolveThemeColors(preset, activeOverrides);
    if (resolved) {
      applyThemeToDocument(resolved);
    }
  }, [themes, activeThemeName, activeOverrides]);

  const value = useMemo<ThemeContextValue>(() => ({
    themes,
    isLoading,
    previewTheme: (themeName: string, overrides?: ThemeOverride) => {
      setPreview({ themeName, overrides });
    },
    clearPreview: () => {
      setPreview(null);
    },
  }), [themes, isLoading]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useThemePreview() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useThemePreview must be used within ThemeProvider');
  }

  return context;
}
