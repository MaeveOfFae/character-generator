import { useMemo, useState } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import { useMutation, useQuery } from '@tanstack/react-query';
import type { ValidationResponse } from '@char-gen/shared';
import { api } from '../config/api';

export default function ValidationScreen() {
  const [path, setPath] = useState('');
  const [selectedDraftId, setSelectedDraftId] = useState('');
  const [result, setResult] = useState<ValidationResponse | null>(null);

  const { data: draftsData, isLoading } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
  });

  const validatePathMutation = useMutation({
    mutationFn: () => api.validatePath({ path }),
    onSuccess: (data) => setResult(data),
  });

  const validateDraftMutation = useMutation({
    mutationFn: (draftId: string) => api.validateDraft(draftId),
    onSuccess: (data) => setResult(data),
  });

  const findings = useMemo(() => {
    if (!result?.output) {
      return [] as string[];
    }

    return result.output
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);
  }, [result]);

  const mutationError = validatePathMutation.error || validateDraftMutation.error;
  const isPending = validatePathMutation.isPending || validateDraftMutation.isPending;

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#7c3aed" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Validation</Text>
      <Text style={styles.subtitle}>
        Run the pack validator against a workspace path or one of your saved drafts.
      </Text>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Validate Directory</Text>
        <Text style={styles.helperText}>Use a workspace-relative path like drafts/... or output/...</Text>
        <TextInput
          style={styles.input}
          value={path}
          onChangeText={setPath}
          placeholder="drafts/20260307_203638_unnamed_character"
          placeholderTextColor="#6b7280"
          autoCapitalize="none"
        />
        <TouchableOpacity
          style={[styles.primaryButton, (!path.trim() || isPending) && styles.disabledButton]}
          onPress={() => validatePathMutation.mutate()}
          disabled={!path.trim() || isPending}
        >
          {validatePathMutation.isPending ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : null}
          <Text style={styles.primaryButtonText}>Validate Path</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Validate Saved Draft</Text>
        <Text style={styles.helperText}>Pick a saved draft by review ID and run the same validator.</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipsContainer}>
          {draftsData?.drafts.map((draft) => (
            <TouchableOpacity
              key={draft.review_id}
              style={[styles.chip, selectedDraftId === draft.review_id && styles.chipActive]}
              onPress={() => setSelectedDraftId(draft.review_id)}
            >
              <Text style={[styles.chipText, selectedDraftId === draft.review_id && styles.chipTextActive]}>
                {draft.character_name || draft.seed}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
        <TouchableOpacity
          style={[styles.secondaryButton, (!selectedDraftId || isPending) && styles.disabledButton]}
          onPress={() => validateDraftMutation.mutate(selectedDraftId)}
          disabled={!selectedDraftId || isPending}
        >
          {validateDraftMutation.isPending ? (
            <ActivityIndicator color="#d1d5db" size="small" />
          ) : null}
          <Text style={styles.secondaryButtonText}>Validate Draft</Text>
        </TouchableOpacity>
      </View>

      {mutationError ? (
        <View style={styles.errorCard}>
          <Text style={styles.errorText}>
            {mutationError instanceof Error ? mutationError.message : 'Validation failed'}
          </Text>
        </View>
      ) : null}

      {result ? (
        <View style={styles.card}>
          <View style={styles.resultHeader}>
            <View style={styles.resultHeaderText}>
              <Text style={styles.sectionTitle}>Validation Results</Text>
              <Text style={styles.resultPath}>{result.path}</Text>
            </View>
            <View style={[styles.statusBadge, result.success ? styles.statusBadgeSuccess : styles.statusBadgeFailure]}>
              <Text style={[styles.statusText, result.success ? styles.statusTextSuccess : styles.statusTextFailure]}>
                {result.success ? 'Passed' : 'Failed'}
              </Text>
            </View>
          </View>

          <View style={styles.outputCard}>
            {findings.length === 0 ? (
              <Text style={styles.emptyText}>No validator output.</Text>
            ) : (
              findings.map((line) => (
                <Text
                  key={line}
                  style={[
                    styles.outputLine,
                    line.startsWith('OK') && styles.outputLineSuccess,
                    line.startsWith('VALIDATION FAILED') && styles.outputLineFailure,
                    line.startsWith('- ') && styles.outputLineWarning,
                  ]}
                >
                  {line}
                </Text>
              ))
            )}
          </View>

          {result.errors ? (
            <View style={styles.stderrCard}>
              <Text style={styles.stderrTitle}>Stderr</Text>
              <Text style={styles.stderrText}>{result.errors}</Text>
            </View>
          ) : null}
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f0f',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f0f0f',
  },
  content: {
    padding: 16,
    gap: 16,
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
    marginBottom: 8,
  },
  card: {
    backgroundColor: '#1f1f1f',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 6,
  },
  helperText: {
    color: '#9ca3af',
    fontSize: 12,
    marginBottom: 12,
  },
  input: {
    backgroundColor: '#111111',
    borderRadius: 8,
    padding: 12,
    color: '#fff',
    borderWidth: 1,
    borderColor: '#2f2f2f',
    fontSize: 14,
    marginBottom: 12,
  },
  chipsContainer: {
    gap: 8,
    paddingBottom: 8,
  },
  chip: {
    backgroundColor: '#27272a',
    borderWidth: 1,
    borderColor: '#3f3f46',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 999,
  },
  chipActive: {
    backgroundColor: '#7c3aed',
    borderColor: '#7c3aed',
  },
  chipText: {
    color: '#d1d5db',
    fontSize: 13,
    fontWeight: '500',
  },
  chipTextActive: {
    color: '#fff',
  },
  primaryButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#7c3aed',
    paddingVertical: 12,
    borderRadius: 8,
  },
  secondaryButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#27272a',
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#3f3f46',
    marginTop: 8,
  },
  disabledButton: {
    opacity: 0.5,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  secondaryButtonText: {
    color: '#d1d5db',
    fontSize: 14,
    fontWeight: '500',
  },
  errorCard: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#7f1d1d',
    backgroundColor: '#450a0a',
    padding: 14,
  },
  errorText: {
    color: '#fca5a5',
    fontSize: 13,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
    marginBottom: 12,
  },
  resultHeaderText: {
    flex: 1,
  },
  resultPath: {
    color: '#9ca3af',
    fontSize: 12,
  },
  statusBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
  },
  statusBadgeSuccess: {
    backgroundColor: '#052e16',
  },
  statusBadgeFailure: {
    backgroundColor: '#450a0a',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  statusTextSuccess: {
    color: '#86efac',
  },
  statusTextFailure: {
    color: '#fca5a5',
  },
  outputCard: {
    backgroundColor: '#111111',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#2f2f2f',
    padding: 14,
    gap: 8,
  },
  outputLine: {
    color: '#d1d5db',
    fontSize: 13,
    lineHeight: 20,
  },
  outputLineSuccess: {
    color: '#86efac',
  },
  outputLineFailure: {
    color: '#fca5a5',
    fontWeight: '600',
  },
  outputLineWarning: {
    color: '#fcd34d',
  },
  stderrCard: {
    marginTop: 12,
    backgroundColor: '#450a0a',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#7f1d1d',
    padding: 14,
  },
  stderrTitle: {
    color: '#fecaca',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 8,
  },
  stderrText: {
    color: '#fca5a5',
    fontSize: 12,
    lineHeight: 18,
  },
  emptyText: {
    color: '#9ca3af',
    fontSize: 13,
  },
});