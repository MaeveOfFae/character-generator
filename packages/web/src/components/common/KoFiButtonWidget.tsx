import { useEffect, useRef } from 'react';

declare global {
  interface Window {
    kofiwidget2?: {
      init: (label: string, backgroundColor: string, supportId: string) => void;
      draw: () => void;
    };
  }
}

export default function KoFiButtonWidget() {
  const hostRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const host = hostRef.current;

    if (!host) {
      return;
    }

    host.innerHTML = '';

    const externalScript = document.createElement('script');
    externalScript.src = 'https://storage.ko-fi.com/cdn/widget/Widget_2.js';
    externalScript.type = 'text/javascript';

    externalScript.onload = () => {
      const inlineScript = document.createElement('script');
      inlineScript.type = 'text/javascript';
      inlineScript.text = "kofiwidget2.init('Support me on Ko-fi', '#72a4f2', 'K3K21UXSS1');kofiwidget2.draw();";
      host.appendChild(inlineScript);
    };

    host.appendChild(externalScript);

    return () => {
      host.innerHTML = '';
    };
  }, []);

  return <div ref={hostRef} className="kofi-widget-shell min-h-11" />;
}