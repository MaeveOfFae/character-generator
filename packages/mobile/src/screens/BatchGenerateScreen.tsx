import { useRef, useState } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useQuery } from '@tanstack/react-query';
import type { ContentMode } from '@char-gen/shared';
import { api } from '../config/api';
import type { HomeStackNavigationProp } from '../types/navigation';

interface BatchJob {
  seed: string;
  status: 'pending' | 'generating' | 'complete' | 'error';
  draftId?: string;
  characterName?: string;
  error?: string;
}

export default function BatchGenerateScreen() {
  const navigation = useNavigation<HomeStackNavigationProp<'BatchGenerate'>>();
  const abortRef = useRef<(() => void) | null>(null);
  const [seeds, setSeeds] = useState<string[]>([]);
  const [mode, setMode] = useState<ContentMode>('SFW');
  const [template, setTemplate] = useState('');
  const [parallel, setParallel] = useState(true);
  const [maxConcurrent, setMaxConcurrent] = useState(3);
  const [jobs, setJobs] = useState<BatchJob[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentSeed, setCurrentSeed] = useState('');
  const [inputText, setInputText] = useState('');

  const { data: templates } = useQuery({
    queryKey: ['templates'],
    queryFn: () => api.getTemplates(),
  });

  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: () => api.getConfig(),
  });

  const effectiveMaxConcurrent = maxConcurrent || config?.batch?.max_concurrent || 3;
  const modes: ContentMode[] = ['SFW', 'NSFW', 'Platform-Safe', 'Auto'];

  const handleAddSeeds = () => {
    const newSeeds = inputText
      .split('\n')
      .map((seed) => seed.trim())
      .filter((seed) => seed.length > 0 && !seeds.includes(seed));

    if (newSeeds.length > 0) {
      setSeeds((previous) => [...previous, ...newSeeds]);
      setInputText('');
    }
  };

  const handleRemoveSeed = (seed: string) => {
    setSeeds((previous) => previous.filter((entry) => entry !== seed));
  };

  const handleClearAll = () => {
    setSeeds([]);
    setJobs([]);
  };

  const handleRunBatch = async () => {
    if (seeds.length === 0 || isRunning) {
      return;
    }

    setIsRunning(true);
    setCurrentSeed('');
    setJobs(seeds.map((seed) => ({ seed, status: 'pending' })));

    try {
      const stream = api.generateBatch(seeds, {
        mode,
        template: template || undefined,
        parallel,
        max_concurrent: effectiveMaxConcurrent,
      });

      abortRef.current = () => stream.abort();

      stream.subscribe((event) => {
        if (event.event === 'batch_start') {
          const data = event.data as { index: number; seed: string };
          setCurrentSeed(data.seed);
          setJobs((previous) => previous.map((job, index) => (
            index === data.index ? { ...job, status: 'generating' } : job
          )));
        }

        if (event.event === 'batch_complete') {
          const data = event.data as { index: number; seed: string; draft_id?: string; character_name?: string };
          setJobs((previous) => previous.map((job, index) => (
            index === data.index
              ? {
                  ...job,
                  status: 'complete',
                  draftId: data.draft_id,
                  characterName: data.character_name,
                }
              : job
          )));
        }

        if (event.event === 'batch_error') {
          const data = event.data as { index: number; seed: string; error: string };
          setJobs((previous) => previous.map((job, index) => (
            index === data.index ? { ...job, status: 'error', error: data.error } : job
          )));
        }

        if (event.event === 'complete') {
          setIsRunning(false);
          setCurrentSeed('');
        }
      });

      stream.onError_((error) => {
        console.error('Batch error:', error);
        setIsRunning(false);
        setCurrentSeed('');
      });

      stream.onComplete_(() => {
        setIsRunning(false);
        setCurrentSeed('');
      });

      await stream.start();
    } catch (error) {
      console.error(error);
      setIsRunning(false);
      setCurrentSeed('');
    }
  };

  const handleStop = () => {
    if (abortRef.current) {
      abortRef.current();
      setIsRunning(false);
      setCurrentSeed('');
    }
  };

  const completedCount = jobs.filter((job) => job.status === 'complete').length;
  const errorCount = jobs.filter((job) => job.status === 'error').length;
  const progress = jobs.length > 0 ? ((completedCount + errorCount) / jobs.length) * 100 : 0;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Batch Generation</Text>
      <Text style={styles.subtitle}>Generate multiple characters from a list of seeds.</Text>

      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.sectionTitle}>Seeds</Text>
          <Text style={styles.sectionMeta}>{seeds.length} added</Text>
        </View>
        <TextInput
          style={[styles.input, styles.textArea]}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Enter seeds, one per line"
          placeholderTextColor="#6b7280"
          multiline
          textAlignVertical="top"
          editable={!isRunning}
        />
        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[styles.primaryButton, (!inputText.trim() || isRunning) && styles.disabledButton]}
            onPress={handleAddSeeds}
            disabled={!inputText.trim() || isRunning}
          >
            <Text style={styles.primaryButtonText}>Add Seeds</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.secondaryButton, (seeds.length === 0 || isRunning) && styles.disabledButton]}
            onPress={handleClearAll}
            disabled={seeds.length === 0 || isRunning}
          >
            <Text style={styles.secondaryButtonText}>Clear All</Text>
          </TouchableOpacity>
        </View>

        {seeds.length > 0 ? (
          <View style={styles.seedList}>
            {seeds.map((seed) => (
              <View key={seed} style={styles.seedRow}>
                <Text style={styles.seedRowText}>{seed}</Text>
                <TouchableOpacity onPress={() => handleRemoveSeed(seed)} disabled={isRunning}>
                  <Text style={[styles.removeText, isRunning && styles.disabledText]}>Remove</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
        ) : null}
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Options</Text>
        <Text style={styles.fieldLabel}>Content Mode</Text>
        <View style={styles.modeRow}>
          {modes.map((entry) => (
            <TouchableOpacity
              key={entry}
              style={[styles.modeChip, mode === entry && styles.modeChipActive, isRunning && styles.disabledButton]}
              onPress={() => setMode(entry)}
              disabled={isRunning}
            >
              <Text style={[styles.modeChipText, mode === entry && styles.modeChipTextActive]}>{entry}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.fieldLabel}>Template</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.templateRow}>
          <TouchableOpacity
            style={[styles.templateChip, !template && styles.templateChipActive]}
            onPress={() => setTemplate('')}
            disabled={isRunning}
          >
            <Text style={[styles.templateChipText, !template && styles.templateChipTextActive]}>Default</Text>
          </TouchableOpacity>
          {templates?.map((entry) => (
            <TouchableOpacity
              key={entry.name}
              style={[styles.templateChip, template === entry.name && styles.templateChipActive]}
              onPress={() => setTemplate(entry.name)}
              disabled={isRunning}
            >
              <Text style={[styles.templateChipText, template === entry.name && styles.templateChipTextActive]}>
                {entry.name}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <View style={styles.toggleRow}>
          <TouchableOpacity
            style={[styles.toggleChip, parallel && styles.templateChipActive, isRunning && styles.disabledButton]}
            onPress={() => setParallel((current) => !current)}
            disabled={isRunning}
          >
            <Text style={[styles.templateChipText, parallel && styles.templateChipTextActive]}>
              {parallel ? 'Parallel On' : 'Parallel Off'}
            </Text>
          </TouchableOpacity>
          <View style={styles.concurrentControl}>
            <TouchableOpacity
              style={styles.controlButton}
              onPress={() => setMaxConcurrent((current) => Math.max(1, current - 1))}
              disabled={isRunning || !parallel}
            >
              <Text style={styles.controlButtonText}>-</Text>
            </TouchableOpacity>
            <Text style={[styles.concurrentValue, !parallel && styles.disabledText]}>Max {effectiveMaxConcurrent}</Text>
            <TouchableOpacity
              style={styles.controlButton}
              onPress={() => setMaxConcurrent((current) => Math.min(10, current + 1))}
              disabled={isRunning || !parallel}
            >
              <Text style={styles.controlButtonText}>+</Text>
            </TouchableOpacity>
          </View>
        </View>

        {config?.batch ? (
          <Text style={styles.helperText}>
            Current saved batch config: {config.batch.max_concurrent} concurrent, {config.batch.rate_limit_delay}s delay.
          </Text>
        ) : null}
      </View>

      {jobs.length > 0 ? (
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.sectionTitle}>Progress</Text>
            <Text style={styles.sectionMeta}>
              {completedCount}/{jobs.length} complete{errorCount > 0 ? ` • ${errorCount} failed` : ''}
            </Text>
          </View>
          <View style={styles.progressTrack}>
            <View style={[styles.progressFill, { width: `${progress}%` }]} />
          </View>
          {currentSeed ? (
            <View style={styles.currentSeedRow}>
              <ActivityIndicator size="small" color="#7c3aed" />
              <Text style={styles.currentSeedText}>Generating: {currentSeed}</Text>
            </View>
          ) : null}

          <View style={styles.jobsList}>
            {jobs.map((job) => (
              <View key={job.seed} style={styles.jobRow}>
                <View style={styles.jobTextWrap}>
                  <Text style={styles.jobSeed}>{job.seed}</Text>
                  {job.characterName ? <Text style={styles.jobName}>{job.characterName}</Text> : null}
                </View>
                {job.status === 'pending' ? <Text style={styles.pendingText}>Pending</Text> : null}
                {job.status === 'generating' ? <Text style={styles.generatingText}>Generating</Text> : null}
                {job.status === 'error' ? <Text style={styles.errorText}>{job.error || 'Error'}</Text> : null}
                {job.status === 'complete' ? (
                  <TouchableOpacity
                    onPress={() =>
                      job.draftId
                        ? navigation.navigate('Drafts', {
                            screen: 'DraftDetail',
                            params: { draftId: job.draftId },
                          })
                        : undefined
                    }
                    disabled={!job.draftId}
                  >
                    <Text style={[styles.viewText, !job.draftId && styles.disabledText]}>View</Text>
                  </TouchableOpacity>
                ) : null}
              </View>
            ))}
          </View>
        </View>
      ) : null}

      {isRunning ? (
        <TouchableOpacity style={styles.stopButton} onPress={handleStop}>
          <Text style={styles.stopButtonText}>Stop</Text>
        </TouchableOpacity>
      ) : (
        <TouchableOpacity
          style={[styles.startButton, seeds.length === 0 && styles.disabledButton]}
          onPress={handleRunBatch}
          disabled={seeds.length === 0}
        >
          <Text style={styles.startButtonText}>Start Generation ({seeds.length} seeds)</Text>
        </TouchableOpacity>
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
    borderWidth: 1,
    borderColor: '#2f2f2f',
    borderRadius: 12,
    padding: 16,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
    marginBottom: 12,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  sectionMeta: {
    color: '#9ca3af',
    fontSize: 12,
    alignSelf: 'center',
  },
  input: {
    backgroundColor: '#111111',
    borderWidth: 1,
    borderColor: '#2f2f2f',
    borderRadius: 10,
    padding: 12,
    color: '#fff',
    fontSize: 14,
  },
  textArea: {
    minHeight: 120,
    marginBottom: 12,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10,
  },
  primaryButton: {
    flex: 1,
    backgroundColor: '#7c3aed',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: '#27272a',
    borderWidth: 1,
    borderColor: '#3f3f46',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#d1d5db',
    fontSize: 14,
    fontWeight: '500',
  },
  disabledButton: {
    opacity: 0.5,
  },
  disabledText: {
    opacity: 0.5,
  },
  seedList: {
    marginTop: 12,
    gap: 8,
  },
  seedRow: {
    backgroundColor: '#111111',
    borderWidth: 1,
    borderColor: '#2f2f2f',
    borderRadius: 10,
    padding: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
    alignItems: 'center',
  },
  seedRowText: {
    color: '#d1d5db',
    flex: 1,
    fontSize: 13,
  },
  removeText: {
    color: '#fca5a5',
    fontSize: 12,
    fontWeight: '600',
  },
  fieldLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    marginTop: 4,
  },
  modeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  modeChip: {
    backgroundColor: '#27272a',
    borderWidth: 1,
    borderColor: '#3f3f46',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  modeChipActive: {
    backgroundColor: '#7c3aed',
    borderColor: '#7c3aed',
  },
  modeChipText: {
    color: '#d1d5db',
    fontSize: 13,
    fontWeight: '500',
  },
  modeChipTextActive: {
    color: '#fff',
  },
  templateRow: {
    gap: 8,
    paddingBottom: 8,
  },
  templateChip: {
    backgroundColor: '#27272a',
    borderWidth: 1,
    borderColor: '#3f3f46',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  templateChipActive: {
    backgroundColor: '#7c3aed',
    borderColor: '#7c3aed',
  },
  templateChipText: {
    color: '#d1d5db',
    fontSize: 13,
    fontWeight: '500',
  },
  templateChipTextActive: {
    color: '#fff',
  },
  toggleRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    alignItems: 'center',
    marginTop: 12,
  },
  toggleChip: {
    backgroundColor: '#27272a',
    borderWidth: 1,
    borderColor: '#3f3f46',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  concurrentControl: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  controlButton: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: '#27272a',
    borderWidth: 1,
    borderColor: '#3f3f46',
    alignItems: 'center',
    justifyContent: 'center',
  },
  controlButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  concurrentValue: {
    color: '#d1d5db',
    fontSize: 13,
    fontWeight: '500',
  },
  helperText: {
    color: '#9ca3af',
    fontSize: 12,
    marginTop: 12,
  },
  progressTrack: {
    height: 8,
    borderRadius: 999,
    backgroundColor: '#27272a',
    overflow: 'hidden',
    marginBottom: 12,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#7c3aed',
  },
  currentSeedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  currentSeedText: {
    color: '#d1d5db',
    fontSize: 13,
  },
  jobsList: {
    gap: 8,
  },
  jobRow: {
    backgroundColor: '#111111',
    borderWidth: 1,
    borderColor: '#2f2f2f',
    borderRadius: 10,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
  },
  jobTextWrap: {
    flex: 1,
  },
  jobSeed: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '500',
  },
  jobName: {
    color: '#9ca3af',
    fontSize: 12,
    marginTop: 4,
  },
  pendingText: {
    color: '#9ca3af',
    fontSize: 12,
  },
  generatingText: {
    color: '#c4b5fd',
    fontSize: 12,
    fontWeight: '600',
  },
  errorText: {
    color: '#fca5a5',
    fontSize: 12,
    maxWidth: 110,
    textAlign: 'right',
  },
  viewText: {
    color: '#86efac',
    fontSize: 12,
    fontWeight: '600',
  },
  stopButton: {
    backgroundColor: '#b91c1c',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
  },
  stopButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
  startButton: {
    backgroundColor: '#7c3aed',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
  },
  startButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
});