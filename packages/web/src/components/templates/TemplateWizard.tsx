import { useEffect, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X, ChevronLeft, ChevronRight, Loader2, CheckCircle2 } from 'lucide-react';
import type { CreateTemplateRequest, AssetDefinition, Template } from '@char-gen/shared';
import { api } from '@/lib/api';
import BasicInfoStep from './wizard/BasicInfoStep';
import AssetSelectionStep from './wizard/AssetSelectionStep';
import DependenciesStep from './wizard/DependenciesStep';
import ReviewStep from './wizard/ReviewStep';

interface TemplateWizardProps {
  open: boolean;
  onClose: () => void;
  initialData?: CreateTemplateRequest;
  templateName?: string;
}

type Step = 1 | 2 | 3 | 4;

const defaultTemplateData: CreateTemplateRequest = {
  name: '',
  version: '1.0',
  description: '',
  assets: [],
  blueprint_contents: {},
};

export default function TemplateWizard({ open, onClose, initialData, templateName }: TemplateWizardProps) {
  const queryClient = useQueryClient();
  const isEditMode = Boolean(templateName);

  // Wizard state
  const [currentStep, setCurrentStep] = useState<Step>(1);
  const [templateData, setTemplateData] = useState<CreateTemplateRequest>(initialData ?? defaultTemplateData);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Creation state
  const [isCreating, setIsCreating] = useState(false);
  const [created, setCreated] = useState(false);
  const [createdTemplate, setCreatedTemplate] = useState<Template | null>(null);

  useEffect(() => {
    if (!open) {
      setCurrentStep(1);
      setTemplateData(initialData ?? defaultTemplateData);
      setErrors({});
      setIsCreating(false);
      setCreated(false);
      setCreatedTemplate(null);
      return;
    }

    setCurrentStep(1);
    setTemplateData(initialData ?? defaultTemplateData);
    setErrors({});
    setIsCreating(false);
    setCreated(false);
    setCreatedTemplate(null);
  }, [open, initialData]);

  const createMutation = useMutation({
    mutationFn: (data: CreateTemplateRequest) =>
      isEditMode && templateName
        ? api.updateTemplate(templateName, data)
        : api.createTemplate(data),
    onSuccess: (template) => {
      setCreated(true);
      setCreatedTemplate(template);
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setTimeout(() => onClose(), 2000);
    },
    onError: (err: Error) => {
      setErrors({ submit: err.message || 'Failed to create template' });
    },
  });

  // Step validators
  const validateStep = (step: Step): boolean => {
    const newErrors: Record<string, string> = {};

    if (step === 1) {
      // Basic info validation
      if (!templateData.name.trim()) {
        newErrors.name = 'Template name is required';
      } else if (!/^[a-z_][a-z0-9_]*$/i.test(templateData.name)) {
        newErrors.name = 'Name must start with letter or underscore and contain only letters, numbers, and underscores';
      }

      if (!templateData.version.trim()) {
        newErrors.version = 'Version is required';
      } else if (!/^\d+\.\d+$/.test(templateData.version)) {
        newErrors.version = 'Version must be in X.Y format (e.g., 1.0)';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const canProceed = (step: Step): boolean => {
    if (step === 1) {
      return templateData.name.trim() !== '' &&
             templateData.version.trim() !== '' &&
             !errors.name && !errors.version;
    }
    if (step === 2) {
      return templateData.assets.length > 0;
    }
    if (step === 3) {
      // Check for circular dependencies
      for (const asset of templateData.assets) {
        const deps = asset.depends_on || [];
        if (deps.includes(asset.name)) return false;

        // Check for transitive circular dependencies
        for (const dep of deps) {
          const depAsset = templateData.assets.find(a => a.name === dep);
          if (depAsset && depAsset.depends_on?.includes(asset.name)) {
            return false;
          }
        }
      }
      return true;
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep(currentStep) && currentStep < 4) {
      setCurrentStep((prev) => (prev + 1) as Step);
      setErrors({});
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((prev) => (prev - 1) as Step);
      setErrors({});
    }
  };

  const handleCreate = () => {
    setIsCreating(true);
    createMutation.mutate(templateData);
  };

  const handleFieldChange = (field: 'name' | 'version' | 'description', value: string) => {
    setTemplateData(prev => ({ ...prev, [field]: value }));
    setErrors(prev => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  };

  const handleAssetsChange = (assets: AssetDefinition[]) => {
    setTemplateData(prev => ({ ...prev, assets }));
  };

  const handleBlueprintContentsChange = (blueprint_contents: Record<string, string>) => {
    setTemplateData(prev => ({ ...prev, blueprint_contents }));
  };

  if (!open) return null;

  const stepTitles: Record<Step, string> = {
    1: 'Basic Information',
    2: 'Asset Selection',
    3: 'Dependencies',
    4: 'Review & Create',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-card border border-border rounded-lg shadow-xl w-full max-w-3xl mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div>
            <h2 className="text-lg font-semibold">{isEditMode ? 'Edit Template' : 'Create Template'}</h2>
            <p className="text-sm text-muted-foreground">
              Step {currentStep} of 4: {stepTitles[currentStep]}
            </p>
          </div>
          {!created && (
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* Progress Indicator */}
        {!created && (
          <div className="px-4 pt-4">
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4].map((step) => (
                <div key={step} className="flex-1">
                  <div className="flex items-center gap-2">
                    <div
                      className={`
                        flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold
                        ${currentStep >= step
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-muted-foreground'}
                      `}
                    >
                      {currentStep > step ? <CheckCircle2 className="h-3.5 w-3.5" /> : step}
                    </div>
                    {step < 4 && (
                      <div
                        className={`
                          flex-1 h-0.5 rounded-full
                          ${currentStep > step ? 'bg-primary' : 'bg-muted'}
                        `}
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {errors.submit && (
            <div className="mb-4 rounded-lg border border-destructive bg-destructive/10 p-4 text-sm text-destructive">
              {errors.submit}
            </div>
          )}

          {created ? (
            <div className="flex flex-col items-center justify-center h-full py-12">
              <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mb-4">
                <CheckCircle2 className="h-8 w-8 text-green-500" />
              </div>
                <h3 className="text-xl font-semibold mb-2">{isEditMode ? 'Template Updated!' : 'Template Created!'}</h3>
              <p className="text-muted-foreground mb-1">
                {createdTemplate?.name}
              </p>
              <p className="text-sm text-muted-foreground">
                Closing in a moment...
              </p>
            </div>
          ) : (
            <>
              {currentStep === 1 && (
                <BasicInfoStep
                  name={templateData.name}
                  version={templateData.version}
                  description={templateData.description}
                  onChange={handleFieldChange}
                  errors={errors}
                />
              )}

              {currentStep === 2 && (
                <AssetSelectionStep
                  assets={templateData.assets}
                  onChange={handleAssetsChange}
                  blueprintContents={templateData.blueprint_contents}
                  onBlueprintContentsChange={handleBlueprintContentsChange}
                />
              )}

              {currentStep === 3 && (
                <DependenciesStep
                  assets={templateData.assets}
                  onChange={handleAssetsChange}
                />
              )}

              {currentStep === 4 && (
                <ReviewStep templateData={templateData} />
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {!created && (
          <div className="flex justify-between items-center p-4 border-t border-border">
            <button
              onClick={handleBack}
              disabled={currentStep === 1}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md border border-input bg-background hover:bg-accent disabled:opacity-50"
            >
              <ChevronLeft className="h-4 w-4" />
              Back
            </button>

            <button
              onClick={currentStep === 4 ? handleCreate : handleNext}
              disabled={!canProceed(currentStep) || isCreating}
              className={`
                inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md
                ${currentStep === 4
                  ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'}
                disabled:opacity-50
              `}
            >
              {isCreating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {isEditMode ? 'Saving...' : 'Creating...'}
                </>
              ) : currentStep === 4 ? (
                <>
                  <CheckCircle2 className="h-4 w-4" />
                  {isEditMode ? 'Save Template' : 'Create Template'}
                </>
              ) : (
                <>
                  Next Step
                  <ChevronRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
