import type { ThemeColors, ThemeOverride, ThemePreset } from '@char-gen/shared';

const APP_OVERRIDE_MAP: Record<string, keyof ThemeColors> = {
  background: 'background',
  text: 'text',
  accent: 'accent',
  button: 'button',
  button_text: 'button_text',
  border: 'border',
  highlight: 'highlight',
  window: 'window',
  muted_text: 'muted_text',
  surface: 'surface',
  success_bg: 'success_bg',
  danger_bg: 'danger_bg',
  accent_bg: 'accent_bg',
  accent_title: 'accent_title',
  success_text: 'success_text',
  error_text: 'error_text',
  warning_text: 'warning_text',
};

export const EDITABLE_THEME_FIELDS = [
  { key: 'background', label: 'Background' },
  { key: 'surface', label: 'Surface' },
  { key: 'window', label: 'Window' },
  { key: 'text', label: 'Text' },
  { key: 'muted_text', label: 'Muted Text' },
  { key: 'accent', label: 'Primary Accent' },
  { key: 'accent_bg', label: 'Accent Surface' },
  { key: 'button', label: 'Button' },
  { key: 'button_text', label: 'Button Text' },
  { key: 'border', label: 'Border' },
  { key: 'highlight', label: 'Ring / Highlight' },
  { key: 'success_text', label: 'Success' },
  { key: 'warning_text', label: 'Warning' },
  { key: 'error_text', label: 'Error' },
] as const;

export type EditableThemeField = typeof EDITABLE_THEME_FIELDS[number]['key'];

export function resolveThemeColors(
  preset: ThemePreset | undefined,
  overrides?: ThemeOverride
): ThemeColors | null {
  if (!preset) {
    return null;
  }

  const merged: ThemeColors = {
    ...preset.colors,
  };

  for (const [overrideKey, value] of Object.entries(overrides?.app ?? {})) {
    if (!value) {
      continue;
    }

    const mappedKey = APP_OVERRIDE_MAP[overrideKey];
    if (mappedKey) {
      merged[mappedKey] = value;
    }
  }

  return merged;
}

export function buildThemeOverride(colors: Partial<Record<EditableThemeField, string>>): ThemeOverride {
  return {
    app: { ...colors },
  };
}

export function extractEditableThemeFields(overrides?: ThemeOverride): Partial<Record<EditableThemeField, string>> {
  const result: Partial<Record<EditableThemeField, string>> = {};

  for (const field of EDITABLE_THEME_FIELDS) {
    const value = overrides?.app?.[field.key];
    if (value) {
      result[field.key] = value;
    }
  }

  return result;
}

function hexToHsl(hex: string): string {
  const normalized = hex.replace('#', '').trim();
  const expanded = normalized.length === 3
    ? normalized.split('').map((value) => value + value).join('')
    : normalized;

  if (!/^[0-9a-fA-F]{6}$/.test(expanded)) {
    return '0 0% 0%';
  }

  const red = parseInt(expanded.slice(0, 2), 16) / 255;
  const green = parseInt(expanded.slice(2, 4), 16) / 255;
  const blue = parseInt(expanded.slice(4, 6), 16) / 255;

  const max = Math.max(red, green, blue);
  const min = Math.min(red, green, blue);
  const delta = max - min;
  const lightness = (max + min) / 2;

  let hue = 0;
  let saturation = 0;

  if (delta !== 0) {
    saturation = delta / (1 - Math.abs(2 * lightness - 1));

    switch (max) {
      case red:
        hue = ((green - blue) / delta) % 6;
        break;
      case green:
        hue = (blue - red) / delta + 2;
        break;
      default:
        hue = (red - green) / delta + 4;
        break;
    }
  }

  const h = Math.round(hue * 60 < 0 ? hue * 60 + 360 : hue * 60);
  const s = Math.round(saturation * 1000) / 10;
  const l = Math.round(lightness * 1000) / 10;
  return `${h} ${s}% ${l}%`;
}

export function themeColorsToCssVariables(colors: ThemeColors): Record<string, string> {
  return {
    '--background': hexToHsl(colors.background),
    '--foreground': hexToHsl(colors.text),
    '--card': hexToHsl(colors.surface),
    '--card-foreground': hexToHsl(colors.text),
    '--primary': hexToHsl(colors.accent),
    '--primary-foreground': hexToHsl(colors.button_text),
    '--secondary': hexToHsl(colors.button),
    '--secondary-foreground': hexToHsl(colors.button_text),
    '--muted': hexToHsl(colors.window),
    '--muted-foreground': hexToHsl(colors.muted_text),
    '--accent': hexToHsl(colors.accent_bg),
    '--accent-foreground': hexToHsl(colors.text),
    '--destructive': hexToHsl(colors.danger_bg),
    '--destructive-foreground': hexToHsl(colors.button_text),
    '--border': hexToHsl(colors.border),
    '--input': hexToHsl(colors.border),
    '--ring': hexToHsl(colors.highlight),
  };
}

export function applyThemeToDocument(colors: ThemeColors): void {
  const root = document.documentElement;
  const variables = themeColorsToCssVariables(colors);

  Object.entries(variables).forEach(([key, value]) => {
    root.style.setProperty(key, value);
  });

  root.style.setProperty('--app-bg', colors.background);
  root.style.setProperty('--app-surface', colors.surface);
  root.style.setProperty('--app-border', colors.border);
  root.style.setProperty('--app-highlight', colors.highlight);
  root.style.setProperty('--app-accent', colors.accent);

  const themeMeta = document.querySelector('meta[name="theme-color"]');
  if (themeMeta) {
    themeMeta.setAttribute('content', colors.window);
  }
}
