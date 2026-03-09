import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useQuery } from '@tanstack/react-query';
import { api } from '../config/api';
import { SparklesIcon, FolderIcon, StarIcon, DocumentTextIcon, GitCompareIcon } from '../components/Icons';
import type { HomeScreenNavigationProp } from '../types/navigation';

export default function HomeScreen() {
  const navigation = useNavigation<HomeScreenNavigationProp>();

  const { data: statsData } = useQuery({
    queryKey: ['drafts', 'stats'],
    queryFn: () => api.getDrafts(),
  });

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Character Generator</Text>
        <Text style={styles.subtitle}>Create rich, consistent characters with AI</Text>
      </View>

      {/* Quick Actions */}
      <View style={styles.actionsGrid}>
        <TouchableOpacity
          style={styles.actionCard}
          onPress={() => navigation.navigate('Generate')}
        >
          <SparklesIcon color="#7c3aed" size={32} />
          <Text style={styles.actionTitle}>Generate</Text>
          <Text style={styles.actionDesc}>Create a new character</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.actionCard}
          onPress={() => navigation.navigate('Drafts')}
        >
          <FolderIcon color="#7c3aed" size={32} />
          <Text style={styles.actionTitle}>Drafts</Text>
          <Text style={styles.actionDesc}>Browse saved characters</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.toolsContainer}>
        <Text style={styles.sectionTitle}>Tools</Text>
        <View style={styles.actionsGrid}>
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigation.navigate('SeedGenerator')}
          >
            <SparklesIcon color="#7c3aed" size={32} />
            <Text style={styles.actionTitle}>Seed Generator</Text>
            <Text style={styles.actionDesc}>Generate concepts from genre lines</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigation.navigate('Validation')}
          >
            <DocumentTextIcon color="#7c3aed" size={32} />
            <Text style={styles.actionTitle}>Validation</Text>
            <Text style={styles.actionDesc}>Run pack checks on drafts or paths</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.actionsGrid}>
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigation.navigate('Lineage')}
          >
            <GitCompareIcon color="#7c3aed" size={32} />
            <Text style={styles.actionTitle}>Lineage</Text>
            <Text style={styles.actionDesc}>Browse family trees and offspring branches</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigation.navigate('Blueprints')}
          >
            <DocumentTextIcon color="#7c3aed" size={32} />
            <Text style={styles.actionTitle}>Blueprints</Text>
            <Text style={styles.actionDesc}>Browse prompt blueprints and template files</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.actionsGrid}>
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigation.navigate('BatchGenerate')}
          >
            <FolderIcon color="#7c3aed" size={32} />
            <Text style={styles.actionTitle}>Batch Generate</Text>
            <Text style={styles.actionDesc}>Run multiple seeds with current batch settings</Text>
          </TouchableOpacity>

          <View style={styles.actionCardPlaceholder} />
        </View>
      </View>

      {/* Stats */}
      <View style={styles.statsContainer}>
        <Text style={styles.sectionTitle}>Quick Stats</Text>
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{statsData?.stats?.total_drafts ?? '--'}</Text>
            <Text style={styles.statLabel}>Characters</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{statsData?.stats?.favorites ?? '--'}</Text>
            <Text style={styles.statLabel}>Favorites</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>
              {statsData?.stats?.by_genre ? Object.keys(statsData.stats.by_genre).length : '--'}
            </Text>
            <Text style={styles.statLabel}>Genres</Text>
          </View>
        </View>
      </View>

      {/* Recent */}
      {statsData?.drafts && statsData.drafts.length > 0 && (
        <View style={styles.recentContainer}>
          <Text style={styles.sectionTitle}>Recent Characters</Text>
          {statsData.drafts.slice(0, 5).map((draft) => (
            <TouchableOpacity
              key={draft.review_id}
              style={styles.recentItem}
              onPress={() => navigation.navigate('Drafts', {
                screen: 'DraftDetail',
                params: { draftId: draft.review_id }
              })}
            >
              <View style={styles.recentInfo}>
                <Text style={styles.recentName}>{draft.character_name || draft.seed}</Text>
                <Text style={styles.recentMeta}>
                  {draft.mode} • {draft.template_name || 'Default'}
                </Text>
              </View>
              {draft.favorite && <StarIcon color="#eab308" size={20} />}
            </TouchableOpacity>
          ))}
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
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#9ca3af',
  },
  actionsGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  toolsContainer: {
    marginBottom: 8,
  },
  actionCard: {
    flex: 1,
    backgroundColor: '#1f1f1f',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  actionCardPlaceholder: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginTop: 8,
    marginBottom: 4,
  },
  actionDesc: {
    fontSize: 12,
    color: '#9ca3af',
    textAlign: 'center',
  },
  statsContainer: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 12,
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#7c3aed',
  },
  statLabel: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 4,
  },
  recentContainer: {
    marginBottom: 24,
  },
  recentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  recentInfo: {
    flex: 1,
  },
  recentName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#fff',
  },
  recentMeta: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 2,
  },
});
