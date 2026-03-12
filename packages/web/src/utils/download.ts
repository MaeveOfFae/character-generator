interface DownloadResponse {
  blob: Blob;
  filename: string | null;
  contentType: string | null;
}

interface SaveResult {
  saved: boolean;
}

type ShareCapableNavigator = Navigator & {
  canShare?: (data?: ShareData) => boolean;
};

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

function isProbablyMobileBrowser(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }

  const coarsePointer = window.matchMedia?.('(pointer: coarse)').matches ?? false;
  const narrowViewport = window.matchMedia?.('(max-width: 1024px)').matches ?? false;
  const mobileAgent = /Android|webOS|iPhone|iPad|iPod|Opera Mini|IEMobile/i.test(navigator.userAgent);

  return mobileAgent || (coarsePointer && narrowViewport);
}

async function shareWithBrowser(download: DownloadResponse, filename: string): Promise<SaveResult | null> {
  const shareNavigator = navigator as ShareCapableNavigator;

  if (!isProbablyMobileBrowser() || typeof shareNavigator.share !== 'function') {
    return null;
  }

  const file = new File([download.blob], filename, {
    type: download.contentType ?? (download.blob.type || 'application/octet-stream'),
  });
  const shareData: ShareData = {
    files: [file],
    title: filename,
  };

  if (typeof shareNavigator.canShare === 'function' && !shareNavigator.canShare(shareData)) {
    return null;
  }

  try {
    await shareNavigator.share(shareData);
    return { saved: true };
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      return { saved: false };
    }

    return null;
  }
}

async function saveWithBrowser(blob: Blob, filename: string): Promise<SaveResult> {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');

  anchor.href = url;
  anchor.download = filename;
  anchor.rel = 'noopener';
  anchor.style.display = 'none';
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);

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

  const shared = await shareWithBrowser(download, filename);
  if (shared) {
    return shared;
  }

  return saveWithBrowser(download.blob, filename);
}

export async function saveBlobDownload(blob: Blob, filename: string, contentType?: string | null): Promise<SaveResult> {
  return saveDownload(
    {
      blob,
      filename,
      contentType: contentType ?? (blob.type || null),
    },
    filename
  );
}
