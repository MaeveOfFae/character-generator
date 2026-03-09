import { useState, useMemo } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, TextInput, ScrollView, ActivityIndicator } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useQuery } from '@tanstack/react-query';
import { type DraftMetadata, type ContentMode } from '@char-gen/shared';
import { api } from '../config/api';
import { StarIcon, FolderIcon, MagnifyingGlassIcon, FunnelIcon } from '../components/Icons';
import type { DraftsStackNavigationProp } from '../types/navigation';

type SortOption = 'created' | 'modified' | 'name';
type FilterMode = 'all' | 'favorites';

export default function DraftsScreen() {
  const navigation = useNavigation<DraftsStackNavigationProp<'DraftsList'>>();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOption, setSortOption] = useState<SortOption>('created');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterMode, setFilterMode] = useState<FilterMode>('all');
  const [filterContentMode, setFilterContentMode] = useState<ContentMode | 'all'>('all');
  const [showFilters, setShowFilters] = useState(false);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => api.getDrafts(),
  });

  const filteredDrafts = useMemo(() => {
    let drafts = data?.drafts || [];

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      drafts = drafts.filter(draft =>
        draft.character_name?.toLowerCase().includes(query) ||
        draft.seed.toLowerCase().includes(query) ||
        draft.tags?.some(tag => tag.toLowerCase().includes(query)) ||
        draft.genre?.toLowerCase().includes(query)
      );
    }

    // Filter by favorites
    if (filterMode === 'favorites') {
      drafts = drafts.filter(draft => draft.favorite);
    }

    // Filter by content mode
    if (filterContentMode !== 'all') {
      drafts = drafts.filter(draft => draft.mode === filterContentMode);
    }

    // Sort
    drafts = [...drafts].sort((a, b) => {
      let comparison = 0;
      if (sortOption === 'name') {
        comparison = (a.character_name || a.seed).localeCompare(b.character_name || b.seed);
      } else if (sortOption === 'created') {
        comparison = new Date(a.created || 0).getTime() - new Date(b.created || 0).getTime();
      } else if (sortOption === 'modified') {
        comparison = new Date(a.modified || 0).getTime() - new Date(b.modified || 0).getTime();
      }
      return sortOrder === 'desc' ? -comparison : comparison;
    });

    return drafts;
  }, [data?.drafts, searchQuery, filterMode, filterContentMode, sortOption, sortOrder]);

  const renderDraft = ({ item }: { item: DraftMetadata }) => (
    <TouchableOpacity
      style={styles.draftItem}
      onPress={() => navigation.navigate('DraftDetail', { draftId: item.review_id })}
    >
      <View style={styles.draftInfo}>
        <View style={styles.draftHeader}>
          <Text style={styles.draftName} numberOfLines={1}>{item.character_name || item.seed}</Text>
          {item.favorite && <StarIcon color="#eab308" size={18} />}
        </View>
        <View style={styles.draftMeta}>
          {item.mode && <Text style={styles.draftTag}>{item.mode}</Text>}
          {item.genre && <Text style={styles.draftTag}>{item.genre}</Text>}
          {item.template_name && <Text style={styles.draftTag}>{item.template_name}</Text>}
        </View>
        {item.created && (
          <Text style={styles.draftDate}>{new Date(item.created).toLocaleDateString()}</Text>
        )}
      </View>
    </TouchableOpacity>
  );

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#7c3aed" />
        <Text style={styles.loadingText}>Loading drafts...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>Error loading drafts</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const contentModes: ContentMode[] = ['SFW', 'NSFW', 'Platform-Safe', 'Auto'];

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchInputContainer}>
          <MagnifyingGlassIcon color="#6b7280" size={18} />
          <TextInput
            style={styles.searchInput}
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholder="Search characters..."
            placeholderTextColor="#6b7280"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Text style={styles.clearButton}>✕</Text>
            </TouchableOpacity>
          )}
        </View>
        <TouchableOpacity
          style={[styles.filterButton, showFilters && styles.filterButtonActive]}
          onPress={() => setShowFilters(!showFilters)}
        >
          <FunnelIcon color={showFilters ? '#fff' : '#9ca3af'} size={18} />
        </TouchableOpacity>
      </View>

      {/* Filters Panel */}
      {showFilters && (
        <View style={styles.filtersPanel}>
          {/* Filter Mode */}
          <View style={styles.filterRow}>
            <Text style={styles.filterLabel}>Show</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View style={styles.filterChips}>
                <TouchableOpacity
                  style={[styles.filterChip, filterMode === 'all' && styles.filterChipActive]}
                  onPress={() => setFilterMode('all')}
                >
                  <Text style={[styles.filterChipText, filterMode === 'all' && styles.filterChipTextActive]}>All</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.filterChip, filterMode === 'favorites' && styles.filterChipActive]}
                  onPress={() => setFilterMode('favorites')}
                >
                  <StarIcon color={filterMode === 'favorites' ? '#fff' : '#9ca3af'} size={14} />
                  <Text style={[styles.filterChipText, filterMode === 'favorites' && styles.filterChipTextActive]}>Favorites</Text>
                </TouchableOpacity>
              </View>
            </ScrollView>
          </View>

          {/* Content Mode Filter */}
          <View style={styles.filterRow}>
            <Text style={styles.filterLabel}>Mode</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View style={styles.filterChips}>
                <TouchableOpacity
                  style={[styles.filterChip, filterContentMode === 'all' && styles.filterChipActive]}
                  onPress={() => setFilterContentMode('all')}
                >
                  <Text style={[styles.filterChipText, filterContentMode === 'all' && styles.filterChipTextActive]}>All</Text>
                </TouchableOpacity>
                {contentModes.map(mode => (
                  <TouchableOpacity
                    key={mode}
                    style={[styles.filterChip, filterContentMode === mode && styles.filterChipActive]}
                    onPress={() => setFilterContentMode(mode)}
                  >
                    <Text style={[styles.filterChipText, filterContentMode === mode && styles.filterChipTextActive]}>{mode}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>
          </View>

          {/* Sort Options */}
          <View style={styles.filterRow}>
            <Text style={styles.filterLabel}>Sort by</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View style={styles.filterChips}>
                {(['created', 'modified', 'name'] as SortOption[]).map(option => (
                  <TouchableOpacity
                    key={option}
                    style={[styles.filterChip, sortOption === option && styles.filterChipActive]}
                    onPress={() => setSortOption(option)}
                  >
                    <Text style={[styles.filterChipText, sortOption === option && styles.filterChipTextActive]}>
                      {option.charAt(0).toUpperCase() + option.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
                <TouchableOpacity
                  style={[styles.filterChip, sortOrder === 'desc' && styles.filterChipActive]}
                  onPress={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                >
                  <Text style={[styles.filterChipText, sortOrder === 'desc' && styles.filterChipTextActive]}>
                    {sortOrder === 'desc' ? '↓ Desc' : '↑ Asc'}
                  </Text>
                </TouchableOpacity>
              </View>
            </ScrollView>
          </View>
        </View>
      )}

      {/* Stats */}
      {data?.stats && (
        <View style={styles.statsBar}>
          <Text style={styles.statsText}>
            {filteredDrafts.length} of {data.stats.total_drafts} characters
            {filterMode === 'favorites' && ' • Favorites only'}
            {searchQuery.length > 0 && ' • Filtered'}
          </Text>
        </View>
      )}

      {/* List */}
      <FlatList
        data={filteredDrafts}
        keyExtractor={(item) => item.review_id}
        renderItem={renderDraft}
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor="#7c3aed" />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <FolderIcon color="#6b7280" size={48} />
            <Text style={styles.emptyTitle}>
              {searchQuery || filterMode !== 'all' || filterContentMode !== 'all'
                ? 'No matches found'
                : 'No drafts yet'}
            </Text>
            <Text style={styles.emptyText}>
              {searchQuery || filterMode !== 'all' || filterContentMode !== 'all'
                ? 'Try adjusting your search or filters'
                : 'Generate your first character to get started'}
            </Text>
          </View>
        }
      />
    </View>
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
  loadingText: {
    color: '#9ca3af',
    fontSize: 14,
    marginTop: 12,
  },
  errorText: {
    color: '#ef4444',
    fontSize: 16,
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: '#7c3aed',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryText: {
    color: '#fff',
    fontSize: 16,
  },
  searchContainer: {
    flexDirection: 'row',
    padding: 12,
    gap: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#1f1f1f',
  },
  searchInputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  searchInput: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 8,
    color: '#fff',
    fontSize: 14,
  },
  clearButton: {
    color: '#6b7280',
    fontSize: 16,
    padding: 4,
  },
  filterButton: {
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 10,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  filterButtonActive: {
    backgroundColor: '#7c3aed',
    borderColor: '#7c3aed',
  },
  filtersPanel: {
    backgroundColor: '#1f1f1f',
    borderBottomWidth: 1,
    borderBottomColor: '#2f2f2f',
    padding: 12,
  },
  filterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  filterLabel: {
    color: '#9ca3af',
    fontSize: 12,
    width: 60,
  },
  filterChips: {
    flexDirection: 'row',
    gap: 8,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#2f2f2f',
  },
  filterChipActive: {
    backgroundColor: '#7c3aed',
  },
  filterChipText: {
    color: '#9ca3af',
    fontSize: 12,
  },
  filterChipTextActive: {
    color: '#fff',
    fontWeight: '500',
  },
  statsBar: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#1f1f1f',
  },
  statsText: {
    color: '#9ca3af',
    fontSize: 13,
  },
  listContent: {
    padding: 16,
  },
  draftItem: {
    backgroundColor: '#1f1f1f',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  draftInfo: {
    flex: 1,
  },
  draftHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  draftName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    flex: 1,
  },
  draftMeta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 4,
  },
  draftTag: {
    backgroundColor: '#2f2f2f',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    color: '#9ca3af',
    fontSize: 12,
  },
  draftDate: {
    color: '#6b7280',
    fontSize: 12,
  },
  empty: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyText: {
    color: '#9ca3af',
    fontSize: 14,
    textAlign: 'center',
  },
});
