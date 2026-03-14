import { lazy, Suspense } from 'react';
import { Loader2 } from 'lucide-react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import {
  appRouteHelpCoverage,
  guidedTourTargetCatalog,
  validateGuidedTourConfiguration,
  validateHelpRouteCoverage,
} from './lib/help';

const Home = lazy(() => import('./components/Home'));
const Generation = lazy(() => import('./components/generation/Generation'));
const SeedGenerator = lazy(() => import('./components/generation/SeedGenerator'));
const Validation = lazy(() => import('./components/validation/Validation'));
const Drafts = lazy(() => import('./components/drafts/Drafts'));
const Review = lazy(() => import('./components/drafts/Review'));
const Blueprints = lazy(() => import('./components/blueprints/Blueprints'));
const BlueprintEditor = lazy(() => import('./components/blueprints/BlueprintEditor'));
const Templates = lazy(() => import('./components/templates/Templates'));
const Lineage = lazy(() => import('./components/lineage/Lineage'));
const Similarity = lazy(() => import('./components/similarity/Similarity'));
const Offspring = lazy(() => import('./components/offspring/Offspring'));
const Settings = lazy(() => import('./components/settings/Settings'));
const Themes = lazy(() => import('./components/settings/Themes'));
const DataManager = lazy(() => import('./components/common/DataManager'));
const BatchGenerate = lazy(() => import('./components/batch/BatchGenerate'));
const About = lazy(() => import('./components/info/About'));
const HelpCenterPage = lazy(() => import('./components/info/HelpCenterPage'));
const WhatsNewPage = lazy(() => import('./components/info/WhatsNewPage'));
const LicensePage = lazy(() => import('./components/info/LicensePage'));
const TermsPage = lazy(() => import('./components/info/TermsPage'));
const PrivacyPage = lazy(() => import('./components/info/PrivacyPage'));
const SecurityPage = lazy(() => import('./components/info/SecurityPage'));
const CodeOfConductPage = lazy(() => import('./components/info/CodeOfConductPage'));

if (import.meta.env.DEV) {
  const helpCoverageIssues = validateHelpRouteCoverage(appRouteHelpCoverage);
  const guidedTourIssues = validateGuidedTourConfiguration(appRouteHelpCoverage, guidedTourTargetCatalog);
  if (helpCoverageIssues.length > 0) {
    for (const issue of helpCoverageIssues) {
      console.warn(`[help] ${issue}`);
    }
  }
  if (guidedTourIssues.length > 0) {
    for (const issue of guidedTourIssues) {
      console.warn(`[help] ${issue}`);
    }
  }
}

function RouteFallback() {
  return (
    <div className="flex h-[60vh] items-center justify-center">
      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading screen...
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Layout>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/generate" element={<Generation />} />
          <Route path="/seed-generator" element={<SeedGenerator />} />
          <Route path="/validation" element={<Validation />} />
          <Route path="/batch" element={<BatchGenerate />} />
          <Route path="/drafts" element={<Drafts />} />
          <Route path="/drafts/:id" element={<Review />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/blueprints" element={<Blueprints />} />
          <Route path="/blueprints/edit/*" element={<BlueprintEditor />} />
          <Route path="/lineage" element={<Lineage />} />
          <Route path="/similarity" element={<Similarity />} />
          <Route path="/offspring" element={<Offspring />} />
          <Route path="/themes" element={<Themes />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/data" element={<DataManager />} />
          <Route path="/about" element={<About />} />
          <Route path="/help" element={<HelpCenterPage />} />
          <Route path="/whats-new" element={<WhatsNewPage />} />
          <Route path="/license" element={<LicensePage />} />
          <Route path="/terms" element={<TermsPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/security" element={<SecurityPage />} />
          <Route path="/code-of-conduct" element={<CodeOfConductPage />} />
        </Routes>
      </Suspense>
    </Layout>
  );
}
