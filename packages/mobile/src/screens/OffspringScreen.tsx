import { useState, useRef } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, ScrollView, Alert, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { type ContentMode } from '@char-gen/shared';
import { api } from '../config/api';
import { BabyIcon, UsersIcon } from '../components/Icons';

export default function OffspringScreen() {
  const navigation = useNavigation();
  const queryClient = useQueryClient();
  const [parent1, setParent1] = useState<string>('');
  const [parent2, setParent2] = useState<string>('');
  const [mode, setMode] = useState<ContentMode>('SFW');
  const [isGenerating, setIsGenerating] = useState(false);
  const [output, setOutput] = useState('');
  const [result, setResult] = useState<{ draftId: string; characterName: string } | null>(null);
  const abortRef = useRef<(() => void) | null>(null);

  const { data: draftsData, isLoading } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
  });

  const getParentName = (id: string) => {
    const draft = draftsData?.drafts.find((d) => d.review_id === id);
    return draft?.character_name || id;
  };

  const handleGenerate = async () => {
    if (!parent1 || !parent2) {
      Alert.alert('Error', 'Please select two parents');
      return;
    }

    setIsGenerating(true);
    setOutput('');
    setResult(null);

    try {
      const stream = api.generateOffspring({
        parent1_id: parent1,
        parent2_id: parent2,
        mode,
      });

      abortRef.current = () => stream.abort();

      stream.subscribe((event) => {
        if (event.event === 'chunk' && 'content' in event.data) {
          const data = event.data as { content: string };
          setOutput((prev) => prev + data.content);
        }
        if (event.event === 'complete' && 'draft_id' in event.data) {
          const data = event.data as { draft_id?: string; character_name?: string };
          setResult({
            draftId: data.draft_id || '',
            characterName: data.character_name || 'Unknown',
          });
          // Refresh drafts list
          queryClient.invalidateQueries({ queryKey: ['drafts'] });
        }
      });

      stream.onError_((error) => {
        console.error('Offspring generation error:', error);
        Alert.alert('Error', 'Failed to generate offspring');
        setIsGenerating(false);
      });

      stream.onComplete_(() => {
        setIsGenerating(false);
      });

      await stream.start();
    } catch (err) {
      console.error(err);
      Alert.alert('Error', 'Failed to generate offspring');
      setIsGenerating(false);
    }
  };

  const handleCancel = () => {
    if (abortRef.current) {
      abortRef.current();
      setIsGenerating(false);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#7c3aed" />
      </View>
    );
  }

  const modes: ContentMode[] = ['SFW', 'NSFW', 'Platform-Safe', 'Auto'];
  const drafts = draftsData?.drafts || [];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <BabyIcon color="#7c3aed" size={28} />
        <Text style={styles.title}>Offspring Generator</Text>
      </View>
      <Text style={styles.subtitle}>
        Create a child character from two parent characters
      </Text>

      {/* Parent Selection */}
      <View style={styles.selectionContainer}>
        {/* Parent 1 */}
        <View style={styles.parentCard}>
          <View style={styles.parentHeader}>
            <UsersIcon color="#7c3aed" size={20} />
            <Text style={styles.parentLabel}>Parent 1</Text>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.chipContainer}>
              {drafts.filter(d => d.review_id !== parent2).map((draft) => (
                <TouchableOpacity
                  key={draft.review_id}
                  onPress={() => setParent1(draft.review_id)}
                  style={[styles.chip, parent1 === draft.review_id && styles.chipActive]}
                >
                  <Text style={[styles.chipText, parent1 === draft.review_id && styles.chipTextActive]} numberOfLines={1}>
                    {draft.character_name || draft.review_id}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>
          {parent1 && (
            <Text style={styles.selectedText}>Selected: {getParentName(parent1)}</Text>
          )}
        </View>

        {/* Connector */}
        <View style={styles.connector}>
          <View style={styles.connectorLine} />
          <BabyIcon color="#7c3aed" size={20} />
          <View style={styles.connectorLine} />
        </View>

        {/* Parent 2 */}
        <View style={styles.parentCard}>
          <View style={styles.parentHeader}>
            <UsersIcon color="#a78bfa" size={20} />
            <Text style={styles.parentLabel}>Parent 2</Text>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.chipContainer}>
              {drafts.filter(d => d.review_id !== parent1).map((draft) => (
                <TouchableOpacity
                  key={draft.review_id}
                  onPress={() => setParent2(draft.review_id)}
                  style={[styles.chip, parent2 === draft.review_id && styles.chipActive]}
                >
                  <Text style={[styles.chipText, parent2 === draft.review_id && styles.chipTextActive]} numberOfLines={1}>
                    {draft.character_name || draft.review_id}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>
          {parent2 && (
            <Text style={styles.selectedText}>Selected: {getParentName(parent2)}</Text>
          )}
        </View>
      </View>

      {/* Mode Selection */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>Content Mode</Text>
        <View style={styles.modeContainer}>
          {modes.map((m) => (
            <TouchableOpacity
              key={m}
              onPress={() => setMode(m)}
              style={[styles.modeButton, mode === m && styles.modeButtonActive]}
            >
              <Text style={[styles.modeButtonText, mode === m && styles.modeButtonTextActive]}>{m}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Generate Button */}
      <TouchableOpacity
        onPress={isGenerating ? handleCancel : handleGenerate}
        disabled={!parent1 || !parent2}
        style={[
          styles.generateButton,
          (!parent1 || !parent2) && styles.generateButtonDisabled,
          isGenerating && styles.generateButtonCancel,
        ]}
      >
        {isGenerating ? (
          <View style={styles.buttonContent}>
            <ActivityIndicator color="#fff" size="small" />
            <Text style={styles.generateButtonText}>Cancel</Text>
          </View>
        ) : (
          <View style={styles.buttonContent}>
            <BabyIcon color="#fff" size={20} />
            <Text style={styles.generateButtonText}>Generate Offspring</Text>
          </View>
        )}
      </TouchableOpacity>

      {/* Result */}
      {result && (
        <View style={styles.resultCard}>
          <Text style={styles.resultTitle}>Offspring Created!</Text>
          <View style={styles.resultInfo}>
            <Text style={styles.resultLabel}>Character</Text>
            <Text style={styles.resultValue}>{result.characterName}</Text>
          </View>
          <View style={styles.resultInfo}>
            <Text style={styles.resultLabel}>Parents</Text>
            <Text style={styles.resultValue}>{getParentName(parent1)} + {getParentName(parent2)}</Text>
          </View>
          <TouchableOpacity
            style={styles.viewButton}
            onPress={() => {
              if (result?.draftId) {
                // Navigate to Drafts tab, then to the draft detail
                (navigation as any).navigate('Drafts', {
                  screen: 'DraftDetail',
                  params: { draftId: result.draftId }
                });
              } else {
                // Fallback: just go to drafts list
                (navigation as any).navigate('Drafts');
              }
            }}
          >
            <Text style={styles.viewButtonText}>View Character</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Output Preview */}
      {output && (
        <View style={styles.outputCard}>
          <Text style={styles.outputTitle}>Generation Output</Text>
          <Text style={styles.outputText}>{output}</Text>
        </View>
      )}

      {/* Empty State */}
      {!parent1 && !parent2 && !isGenerating && (
        <View style={styles.emptyState}>
          <BabyIcon color="#6b7280" size={48} />
          <Text style={styles.emptyTitle}>Select Two Parents</Text>
          <Text style={styles.emptyText}>
            Choose two characters to combine their traits into a new character
          </Text>
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
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f0f0f',
  },
  content: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 14,
    color: '#9ca3af',
    marginBottom: 24,
  },
  selectionContainer: {
    gap: 0,
    marginBottom: 24,
  },
  parentCard: {
    backgroundColor: '#1f1f1f',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  parentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  parentLabel: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  chipContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  chip: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    backgroundColor: '#2f2f2f',
    borderRadius: 16,
  },
  chipActive: {
    backgroundColor: '#7c3aed',
  },
  chipText: {
    color: '#9ca3af',
    fontSize: 13,
  },
  chipTextActive: {
    color: '#fff',
    fontWeight: '500',
  },
  selectedText: {
    color: '#71717a',
    fontSize: 12,
    marginTop: 8,
  },
  connector: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    justifyContent: 'center',
  },
  connectorLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#2f2f2f',
  },
  section: {
    marginBottom: 24,
  },
  sectionLabel: {
    color: '#a1a1aa',
    fontSize: 14,
    marginBottom: 8,
  },
  modeContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  modeButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
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
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 24,
  },
  generateButtonDisabled: {
    backgroundColor: '#3f3f46',
  },
  generateButtonCancel: {
    backgroundColor: '#dc2626',
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
  resultCard: {
    backgroundColor: '#14532d',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#22c55e',
    marginBottom: 24,
  },
  resultTitle: {
    color: '#22c55e',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  resultInfo: {
    marginBottom: 8,
  },
  resultLabel: {
    color: '#86efac',
    fontSize: 12,
    marginBottom: 2,
  },
  resultValue: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  viewButton: {
    backgroundColor: '#22c55e',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  viewButtonText: {
    color: '#052e16',
    fontSize: 14,
    fontWeight: '600',
  },
  outputCard: {
    backgroundColor: '#1f1f1f',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2f2f2f',
    marginBottom: 24,
  },
  outputTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  outputText: {
    color: '#a1a1aa',
    fontSize: 12,
    lineHeight: 18,
  },
  emptyState: {
    backgroundColor: '#1f1f1f',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  emptyTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyText: {
    color: '#6b7280',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
});
