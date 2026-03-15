import type { ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';

interface DocumentPageProps {
  eyebrow: string;
  title: string;
  summary: string;
  markdown?: string;
  children?: ReactNode;
}

const markdownComponents = {
  h1: ({ children }: { children?: ReactNode }) => <h1 className="text-3xl font-bold text-foreground">{children}</h1>,
  h2: ({ children }: { children?: ReactNode }) => <h2 className="mt-8 text-2xl font-semibold text-foreground">{children}</h2>,
  h3: ({ children }: { children?: ReactNode }) => <h3 className="mt-6 text-lg font-semibold text-foreground">{children}</h3>,
  p: ({ children }: { children?: ReactNode }) => <p className="leading-7 text-muted-foreground">{children}</p>,
  ul: ({ children }: { children?: ReactNode }) => <ul className="ml-5 list-disc space-y-2 text-muted-foreground">{children}</ul>,
  ol: ({ children }: { children?: ReactNode }) => <ol className="ml-5 list-decimal space-y-2 text-muted-foreground">{children}</ol>,
  li: ({ children }: { children?: ReactNode }) => <li className="pl-1">{children}</li>,
  strong: ({ children }: { children?: ReactNode }) => <strong className="font-semibold text-foreground">{children}</strong>,
  a: ({ href, children }: { href?: string; children?: ReactNode }) => (
    <a href={href} className="text-primary underline decoration-primary/40 underline-offset-4 hover:decoration-primary">
      {children}
    </a>
  ),
  code: ({ children }: { children?: ReactNode }) => (
    <code className="rounded bg-muted px-1.5 py-0.5 text-sm text-foreground">{children}</code>
  ),
  pre: ({ children }: { children?: ReactNode }) => (
    <pre className="overflow-x-auto rounded-2xl border border-border/60 bg-slate-950/90 p-4 text-sm text-slate-100">{children}</pre>
  ),
  blockquote: ({ children }: { children?: ReactNode }) => (
    <blockquote className="border-l-2 border-primary/40 pl-4 italic text-muted-foreground">{children}</blockquote>
  ),
  table: ({ children }: { children?: ReactNode }) => (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse overflow-hidden rounded-2xl border border-border/60">{children}</table>
    </div>
  ),
  thead: ({ children }: { children?: ReactNode }) => <thead className="bg-muted/60 text-left text-foreground">{children}</thead>,
  th: ({ children }: { children?: ReactNode }) => <th className="border-b border-border/60 px-4 py-3 text-sm font-semibold">{children}</th>,
  td: ({ children }: { children?: ReactNode }) => <td className="border-b border-border/40 px-4 py-3 align-top text-sm text-muted-foreground">{children}</td>,
};

export default function DocumentPage({ eyebrow, title, summary, markdown, children }: DocumentPageProps) {
  return (
    <div className="space-y-8 pb-12">
      <section className="overflow-hidden rounded-3xl border border-border/50 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 px-8 py-10">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-primary/80">{eyebrow}</p>
        <h1 className="mt-3 text-4xl font-bold text-white">{title}</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">{summary}</p>
      </section>

      {children ? <section className="space-y-6">{children}</section> : null}

      {markdown ? (
        <section className="space-y-4 rounded-3xl border border-border/60 bg-card/70 p-6 shadow-sm backdrop-blur-sm">
          <ReactMarkdown components={markdownComponents}>{markdown}</ReactMarkdown>
        </section>
      ) : null}
    </div>
  );
}