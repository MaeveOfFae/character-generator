import { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { type ContentMode, type GenerationComplete } from '@char-gen/shared';
import { api } from '../config/api';
import { SparklesIcon, DocumentTextIcon } from '../components/Icons';

export default function GenerateScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const queryClient = useQueryClient();
  const [seed, setSeed] = useState('');
  const [mode, setMode] = useState<ContentMode>('SFW');
  const [template, setTemplate] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [result, setResult] = useState<GenerationComplete | null>(null);

  const { data: templates } = useQuery({
    queryKey: ['templates'],
    queryFn: () => api.getTemplates(),
  });

  useEffect(() => {
    const incomingSeed = (route.params as { seed?: string } | undefined)?.seed;
    if (incomingSeed && incomingSeed !== seed) {
      setSeed(incomingSeed);
    }
  }, [route.params, seed]);

  const handleGenerate = async () => {
    if (!seed.trim()) return;

    setIsGenerating(true);
    setOutput('');
    setError('');
    setResult(null);

    try {
      const stream = api.generate({
        seed,
        mode,
        template: template || undefined,
        stream: true
      });

      stream.subscribe((event) => {
        if (event.event === 'chunk' && 'content' in event.data) {
          const data = event.data as { content: string };
          setOutput((prev) => prev + data.content);
        }
        if (event.event === 'complete') {
          const data = event.data as GenerationComplete;
          setResult(data);
          // Refresh drafts list
          queryClient.invalidateQueries({ queryKey: ['drafts'] });
        }
      });

      stream.onError_((err) => {
        setError(err);
        setIsGenerating(false);
      });

      stream.onComplete_(() => {
        setIsGenerating(false);
      });

      await stream.start();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
      setIsGenerating(false);
    }
  };

  const modes: ContentMode[] = ['SFW', 'NSFW', 'Platform-Safe', 'Auto'];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Generate Character</Text>
      <Text style={styles.subtitle}>Enter a seed concept to create a character</Text>

      <View style={styles.form}>
        {/* Seed Input */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Seed Concept</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={seed}
            onChangeText={setSeed}
            placeholder="e.g., a lonely space pirate..."
            placeholderTextColor="#6b7280"
            multiline
            numberOfLines={4}
          />
        </View>

        {/* Template Selection */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Template</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.templateChips}>
              <TouchableOpacity
                style={[styles.templateChip, !template && styles.templateChipActive]}
                onPress={() => setTemplate('')}
              >
                <Text style={[styles.templateChipText, !template && styles.templateChipTextActive]}>
                  Default
                </Text>
              </TouchableOpacity>
              {templates?.map((t) => (
                <TouchableOpacity
                  key={t.name}
                  style={[styles.templateChip, template === t.name && styles.templateChipActive]}
                  onPress={() => setTemplate(t.name)}
                >
                  <DocumentTextIcon
                    color={template === t.name ? '#fff' : '#9ca3af'}
                    size={14}
                  />
                  <Text style={[styles.templateChipText, template === t.name && styles.templateChipTextActive]}>
                    {t.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>
        </View>

        {/* Mode Selection */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Content Mode</Text>
          <View style={styles.modeButtons}>
            {modes.map((m) => (
              <TouchableOpacity
                key={m}
                style={[styles.modeButton, mode === m && styles.modeButtonActive]}
                onPress={() => setMode(m)}
              >
                <Text style={[styles.modeButtonText, mode === m && styles.modeButtonTextActive]}>
                  {m}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Generate Button */}
        <TouchableOpacity
          style={[styles.generateButton, (!seed.trim() || isGenerating) && styles.generateButtonDisabled]}
          onPress={handleGenerate}
          disabled={!seed.trim() || isGenerating}
        >
          {isGenerating ? (
            <View style={styles.buttonContent}>
              <ActivityIndicator color="#fff" size="small" />
              <Text style={styles.generateButtonText}>Generating...</Text>
            </View>
          ) : (
            <View style={styles.buttonContent}>
              <SparklesIcon color="#fff" size={20} />
              <Text style={styles.generateButtonText}>Generate</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* Error */}
      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorTitle}>Generation Failed</Text>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      {/* Success Result */}
      {result && (
        <View style={styles.successBox}>
          <Text style={styles.successTitle}>Character Created!</Text>
          <View style={styles.successInfo}>
            <Text style={styles.successLabel}>Name</Text>
            <Text style={styles.successValue}>{result.character_name || 'Unknown'}</Text>
          </View>
          <View style={styles.successInfo}>
            <Text style={styles.successLabel}>Duration</Text>
            <Text style={styles.successValue}>{(result.duration_ms / 1000).toFixed(1)}s</Text>
          </View>
          <TouchableOpacity
            style={styles.viewButton}
            onPress={() => {
              if (result?.draft_id) {
                (navigation as any).navigate('Drafts', {
                  screen: 'DraftDetail',
                  params: { draftId: result.draft_id }
                });
              } else {
                (navigation as any).navigate('Drafts');
              }
            }}
          >
            <Text style={styles.viewButtonText}>View Character</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Output Preview */}
      {output && !result && (
        <View style={styles.outputContainer}>
          <Text style={styles.outputTitle}>Generating...</Text>
          <View style={styles.outputBox}>
            <Text style={styles.outputText}>{output}</Text>
            {isGenerating && (
              <View style={styles.typingIndicator}>
                <View style={styles.typingDot} />
                <View style={[styles.typingDot, styles.typingDot2]} />
                <View style={[styles.typingDot, styles.typingDot3]} />
              </View>
            )}
          </View>
        </View>
      )}

      {/* Full Output (after completion) */}
      {output && result && (
        <View style={styles.outputContainer}>
          <Text style={styles.outputTitle}>Generated Content</Text>
          <View style={styles.outputBox}>
            <Text style={styles.outputText}>{output}</Text>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f0f',
  },
  content: {
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#9ca3af',
    marginBottom: 24,
  },
  form: {
    marginBottom: 24,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#fff',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 12,
    color: '#fff',
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  textArea: {
    minHeight: 100,
    textAlignVertical: 'top',
  },
  templateChips: {
    flexDirection: 'row',
    gap: 8,
  },
  templateChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    backgroundColor: '#1f1f1f',
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  templateChipActive: {
    backgroundColor: '#7c3aed',
    borderColor: '#7c3aed',
  },
  templateChipText: {
    color: '#9ca3af',
    fontSize: 13,
  },
  templateChipTextActive: {
    color: '#fff',
    fontWeight: '500',
  },
  modeButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  modeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#1f1f1f',
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  modeButtonActive: {
    backgroundColor: '#7c3aed',
    borderColor: '#7c3aed',
  },
  modeButtonText: {
    color: '#9ca3af',
    fontSize: 14,
  },
  modeButtonTextActive: {
    color: '#fff',
    fontWeight: '500',
  },
  generateButton: {
    backgroundColor: '#7c3aed',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  generateButtonDisabled: {
    backgroundColor: '#3f3f46',
  },
  generateButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  errorBox: {
    backgroundColor: '#7f1d1d',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#dc2626',
  },
  errorTitle: {
    color: '#fca5a5',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  errorText: {
    color: '#fecaca',
    fontSize: 14,
  },
  successBox: {
    backgroundColor: '#14532d',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#22c55e',
  },
  successTitle: {
    color: '#22c55e',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  successInfo: {
    marginBottom: 8,
  },
  successLabel: {
    color: '#86efac',
    fontSize: 12,
    marginBottom: 2,
  },
  successValue: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
  },
  viewButton: {
    backgroundColor: '#22c55e',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  viewButtonText: {
    color: '#052e16',
    fontSize: 14,
    fontWeight: '600',
  },
  outputContainer: {
    marginTop: 8,
  },
  outputTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#9ca3af',
    marginBottom: 8,
  },
  outputBox: {
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  outputText: {
    color: '#d1d5db',
    fontSize: 13,
    fontFamily: 'monospace',
    lineHeight: 18,
  },
  typingIndicator: {
    flexDirection: 'row',
    gap: 4,
    marginTop: 8,
    alignItems: 'center',
  },
  typingDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#7c3aed',
  },
  typingDot2: {
    opacity: 0.7,
  },
  typingDot3: {
    opacity: 0.4,
  },
});
