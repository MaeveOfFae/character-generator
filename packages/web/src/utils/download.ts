interface DownloadResponse {
  blob: Blob;
  filename: string | null;
  contentType: string | null;
}

interface SaveResult {
  saved: boolean;
}

function sanitizeFilename(filename: string): string {
  const sanitized = filename.trim().replace(/[\\/:*?"<>|]+/g, '_');
  return sanitized || 'download';
}

function extensionFor(filename: string): string | null {
  const parts = filename.split('.');
  if (parts.length < 2) {
    return null;
  }

  const extension = parts.at(-1)?.trim().toLowerCase() ?? '';
  return extension ? extension : null;
}

function buildDialogFilters(filename: string, contentType: string | null) {
  const extension = extensionFor(filename);
  if (!extension) {
    return undefined;
  }

  const filterName = contentType ?? `${extension.toUpperCase()} file`;
  return [{ name: filterName, extensions: [extension] }];
}

async function saveWithBrowser(blob: Blob, filename: string): Promise<SaveResult> {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');

  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);

  return { saved: true };
}

async function saveWithTauri(download: DownloadResponse, filename: string): Promise<SaveResult> {
  const { invoke } = await import('@tauri-apps/api/core');
  const bytes = new Uint8Array(await download.blob.arrayBuffer());
  const saved = await invoke<boolean>('save_export', {
    defaultFilename: filename,
    filters: buildDialogFilters(filename, download.contentType),
    data: Array.from(bytes),
  });

  if (!saved) {
    return { saved: false };
  }

  return { saved: true };
}

export async function saveDownload(download: DownloadResponse, fallbackFilename: string): Promise<SaveResult> {
  const filename = sanitizeFilename(download.filename ?? fallbackFilename);

  const { isTauri } = await import('@tauri-apps/api/core');

  if (isTauri()) {
    return saveWithTauri(download, filename);
  }

  return saveWithBrowser(download.blob, filename);
}
