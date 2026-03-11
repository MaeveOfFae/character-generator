import { Link } from 'react-router-dom';
import { BookOpen, FileLock2, ShieldCheck, Scale, Info, Sparkles } from 'lucide-react';
import DocumentPage from './DocumentPage';

const infoCards = [
  {
    to: '/terms',
    title: 'Terms of Use',
    description: 'Ground rules for using the web app, exports, and generated content responsibly.',
    icon: Scale,
  },
  {
    to: '/privacy',
    title: 'Privacy',
    description: 'What stays in your browser, what reaches model providers, and where sensitive data lives.',
    icon: FileLock2,
  },
  {
    to: '/license',
    title: 'License',
    description: 'The repository license text and current attribution requirements.',
    icon: BookOpen,
  },
  {
    to: '/security',
    title: 'Security',
    description: 'How to report vulnerabilities and handle provider keys safely.',
    icon: ShieldCheck,
  },
];

export default function About() {
  return (
    <DocumentPage
      eyebrow="About"
      title="About Eidolon Simulacra"
      summary="Eidolon Simulacra is a browser-first blueprint compiler for character packages. It builds structured assets from a seed, preserves template-specific formats, and keeps draft state local by default."
    >
      <section className="grid gap-4 md:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-3xl border border-border/60 bg-card/70 p-6 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-gradient-to-br from-primary to-accent p-3 text-white shadow-lg shadow-primary/20">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-foreground">What It Does</h2>
              <p className="text-sm text-muted-foreground">Structured generation, validation, review, and export in one browser workspace.</p>
            </div>
          </div>
          <div className="mt-6 space-y-4 text-sm leading-7 text-muted-foreground">
            <p>
              The app compiles template-aware drafts from a single seed, keeps asset dependencies in order, and exposes review, validation, lineage, similarity, and export flows directly in the browser.
            </p>
            <p>
              Sensitive settings like API keys and draft content are stored client-side by default. Model requests go directly to the selected provider configuration in the active session.
            </p>
            <p>
              The repository also contains the blueprint source, rules, presets, and shared TypeScript utilities that power the browser runtime.
            </p>
          </div>
        </div>

        <div className="rounded-3xl border border-border/60 bg-card/70 p-6 backdrop-blur-sm">
          <div className="flex items-center gap-2 text-foreground">
            <Info className="h-5 w-5 text-primary" />
            <h2 className="text-xl font-semibold">Quick Facts</h2>
          </div>
          <div className="mt-5 space-y-4 text-sm text-muted-foreground">
            <div>
              <p className="font-medium text-foreground">Current surface</p>
              <p>Browser-first React app with shared generation and export utilities.</p>
            </div>
            <div>
              <p className="font-medium text-foreground">Primary workflow</p>
              <p>Seed to reviewed asset pack with template-aware dependency handling.</p>
            </div>
            <div>
              <p className="font-medium text-foreground">Storage model</p>
              <p>Local browser storage and IndexedDB, with migration support from pre-rebrand keys.</p>
            </div>
            <div>
              <p className="font-medium text-foreground">Version line</p>
              <p>v2.x browser generation stack.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-border/60 bg-card/70 p-6 backdrop-blur-sm">
        <div className="flex items-center gap-2 text-foreground">
          <BookOpen className="h-5 w-5 text-primary" />
          <h2 className="text-xl font-semibold">Info and Legal</h2>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {infoCards.map((card) => {
            const Icon = card.icon;
            return (
              <Link
                key={card.to}
                to={card.to}
                className="group rounded-2xl border border-border/60 bg-background/60 p-5 transition-colors hover:border-primary/40 hover:bg-accent/20"
              >
                <div className="flex items-start gap-3">
                  <div className="rounded-xl bg-primary/10 p-2 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-foreground">{card.title}</p>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">{card.description}</p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
          <Link to="/code-of-conduct" className="text-primary hover:underline">Code of Conduct</Link>
          <Link to="/settings" className="text-primary hover:underline">Settings</Link>
          <Link to="/data" className="text-primary hover:underline">Data Manager</Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-[0.85fr_1.15fr]">
        <div className="rounded-3xl border border-border/60 bg-card/70 p-6 backdrop-blur-sm">
          <div className="flex items-center gap-2 text-foreground">
            <Sparkles className="h-5 w-5 text-primary" />
            <h2 className="text-xl font-semibold">Support the Project</h2>
          </div>
          <div className="mt-5 space-y-4 text-sm leading-7 text-muted-foreground">
            <p>
              If Eidolon Simulacra is useful to you, Ko-fi is the cleanest way to back ongoing blueprint work, browser tooling, and release upkeep.
            </p>
            <p>
              Support helps fund template updates, validation improvements, UI polish, and the less glamorous maintenance work that keeps the compiler stack stable.
            </p>
            <p>
              The full Ko-fi panel lives here instead of the sidebar so it has enough room to stay usable without crushing navigation.
            </p>
          </div>
        </div>

        <div className="overflow-hidden rounded-3xl border border-border/60 bg-card/70 p-3 backdrop-blur-sm">
          <iframe
            id="kofiframe"
            src="https://ko-fi.com/maeveoffae/?hidefeed=true&widget=true&embed=true&preview=true"
            className="block w-full border-0 bg-[#f9f9f9]"
            height="712"
            title="maeveoffae"
          />
        </div>
      </section>
    </DocumentPage>
  );
}