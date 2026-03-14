import {
  appRouteHelpCoverage,
  guidedTourTargetCatalog,
  resolvePageHelp,
  validateGuidedTourConfiguration,
  validateHelpRouteCoverage,
} from './help';

describe('help configuration', () => {
  it('keeps page help coverage aligned with routed pages', () => {
    expect(validateHelpRouteCoverage(appRouteHelpCoverage)).toEqual([]);
  });

  it('keeps guided tours aligned with known routes and target anchors', () => {
    expect(validateGuidedTourConfiguration(appRouteHelpCoverage, guidedTourTargetCatalog)).toEqual([]);
  });

  it('resolves the draft review page using prefix matching', () => {
    expect(resolvePageHelp('/drafts/example-review-id')?.id).toBe('draft-review');
  });
});