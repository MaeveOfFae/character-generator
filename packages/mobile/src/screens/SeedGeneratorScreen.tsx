import { useState } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, ActivityIndicator, Alert, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useMutation } from '@tanstack/react-query';
import * as Clipboard from 'expo-clipboard';
import { api } from '../config/api';
import { SparklesIcon, ClipboardIcon } from '../components/Icons';

const defaultGenreLines = ['Noir detective', 'Cyberpunk mercenary', 'Fantasy sorceress'].join('\n');

export default function SeedGeneratorScreen() {
  const navigation = useNavigation();
  const [genreLines, setGenreLines] = useState(defaultGenreLines);
  const [copiedSeed, setCopiedSeed] = useState<string | null>(null);

  const seedMutation = useMutation({
    mutationFn: (request: { genre_lines: string; surprise_mode?: boolean }) => api.generateSeeds(request),
    onError: (error: unknown) => {
      Alert.alert('Error', error instanceof Error ? error.message : 'Seed generation failed');
    },
  });

  const seeds = seedMutation.data?.seeds ?? [];

  const handleGenerate = () => {
    if (!genreLines.trim()) {
      return;
    }
    seedMutation.mutate({ genre_lines: genreLines, surprise_mode: false });
  };

  const handleSurprise = () => {
    seedMutation.mutate({ genre_lines: '', surprise_mode: true });
  };

  const handleUseSeed = (seed: string) => {
    const parentNavigation = navigation.getParent() as any;
    if (parentNavigation?.navigate) {
      parentNavigation.navigate('Generate', { seed });
      return;
    }

    Alert.alert('Seed Ready', seed);
  };

  const handleCopySeed = async (seed: string) => {
    await Clipboard.setStringAsync(seed);
    setCopiedSeed(seed);
    setTimeout(() => setCopiedSeed(null), 1500);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Seed Generator</Text>
      <Text style={styles.subtitle}>
        Turn genre lines into character seeds or let the model surprise you.
      </Text>

      <View style={styles.card}>
        <Text style={styles.label}>Genre or Theme Lines</Text>
        <Text style={styles.helperText}>Use one line per genre, tone, or hook.</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          value={genreLines}
          onChangeText={setGenreLines}
          placeholder="fantasy&#10;cyberpunk noir&#10;Victorian horror"
          placeholderTextColor="#6b7280"
          multiline
          textAlignVertical="top"
        />

        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[styles.primaryButton, (!genreLines.trim() || seedMutation.isPending) && styles.disabledButton]}
            onPress={handleGenerate}
            disabled={!genreLines.trim() || seedMutation.isPending}
          >
            {seedMutation.isPending && !seedMutation.variables?.surprise_mode ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <SparklesIcon color="#fff" size={18} />
            )}
            <Text style={styles.primaryButtonText}>Generate Seeds</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.secondaryButton, seedMutation.isPending && styles.disabledButton]}
            onPress={handleSurprise}
            disabled={seedMutation.isPending}
          >
            {seedMutation.isPending && seedMutation.variables?.surprise_mode ? (
              <ActivityIndicator color="#d1d5db" size="small" />
            ) : (
              <SparklesIcon color="#d1d5db" size={18} />
            )}
            <Text style={styles.secondaryButtonText}>Surprise Me</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.card}>
        <View style={styles.resultsHeader}>
          <View>
            <Text style={styles.sectionTitle}>Generated Seeds</Text>
            <Text style={styles.helperText}>Send any result directly into Generate.</Text>
          </View>
          <View style={styles.countBadge}>
            <Text style={styles.countText}>{seeds.length} seeds</Text>
          </View>
        </View>

        {seeds.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>No seeds yet</Text>
            <Text style={styles.emptyText}>Generate a set to start exploring concepts.</Text>
          </View>
        ) : (
          <View style={styles.resultsList}>
            {seeds.map((seed) => (
              <View key={seed} style={styles.seedCard}>
                <Text style={styles.seedText}>{seed}</Text>
                <View style={styles.seedActions}>
                  <TouchableOpacity style={styles.primaryButtonSmall} onPress={() => handleUseSeed(seed)}>
                    <Text style={styles.primaryButtonText}>Use In Generate</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.secondaryButtonSmall} onPress={() => handleCopySeed(seed)}>
                    <ClipboardIcon color="#d1d5db" size={16} />
                    <Text style={styles.secondaryButtonText}>{copiedSeed === seed ? 'Copied' : 'Copy'}</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>
        )}
      </View>
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
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 6,
  },
  helperText: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 12,
  },
  input: {
    backgroundColor: '#111111',
    borderRadius: 8,
    padding: 12,
    color: '#fff',
    borderWidth: 1,
    borderColor: '#2f2f2f',
    fontSize: 15,
  },
  textArea: {
    minHeight: 140,
    marginBottom: 12,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  primaryButton: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#7c3aed',
    paddingVertical: 12,
    borderRadius: 8,
  },
  secondaryButton: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#27272a',
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#3f3f46',
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
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  countBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#27272a',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  countText: {
    color: '#9ca3af',
    fontSize: 12,
    fontWeight: '500',
  },
  emptyState: {
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: '#3f3f46',
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
  },
  emptyTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 6,
  },
  emptyText: {
    color: '#9ca3af',
    fontSize: 13,
    textAlign: 'center',
  },
  resultsList: {
    gap: 12,
  },
  seedCard: {
    backgroundColor: '#111111',
    borderWidth: 1,
    borderColor: '#2f2f2f',
    borderRadius: 10,
    padding: 14,
  },
  seedText: {
    color: '#f3f4f6',
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 12,
  },
  seedActions: {
    flexDirection: 'row',
    gap: 8,
  },
  primaryButtonSmall: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#7c3aed',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
  },
  secondaryButtonSmall: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#27272a',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#3f3f46',
  },
});