import { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, ActivityIndicator, Alert, Share, Modal, TextInput, KeyboardAvoidingView, Platform } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as Clipboard from 'expo-clipboard';
import { api } from '../config/api';
import { StarIcon, ArrowLeftIcon, TrashIcon, DocumentTextIcon, ChatBubbleIcon, ClipboardDocumentIcon, PencilIcon } from '../components/Icons';
import type { DraftDetailRouteProp, DraftsStackNavigationProp } from '../types/navigation';

export default function DraftDetailScreen() {
  const navigation = useNavigation<DraftsStackNavigationProp<'DraftDetail'>>();
  const route = useRoute<DraftDetailRouteProp>();
  const queryClient = useQueryClient();
  const { draftId } = route.params;

  // Metadata editing state
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editName, setEditName] = useState('');
  const [editGenre, setEditGenre] = useState('');
  const [editTags, setEditTags] = useState('');
  const [editNotes, setEditNotes] = useState('');

  const { data: draft, isLoading, error } = useQuery({
    queryKey: ['draft', draftId],
    queryFn: () => api.getDraft(decodeURIComponent(draftId)),
    enabled: !!draftId,
  });

  const toggleFavorite = useMutation({
    mutationFn: () => api.updateMetadata(draftId, { favorite: !draft?.metadata.favorite }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['draft', draftId] });
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
    },
  });

  const updateMetadataMutation = useMutation({
    mutationFn: (metadata: Parameters<typeof api.updateMetadata>[1]) => api.updateMetadata(draftId, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['draft', draftId] });
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
      setEditModalVisible(false);
    },
    onError: (error: any) => {
      Alert.alert('Error', error?.detail || 'Failed to update metadata');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteDraft(draftId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
      navigation.goBack();
    },
    onError: (error: any) => {
      Alert.alert('Error', error?.detail || 'Failed to delete draft');
    },
  });

  const handleDelete = () => {
    Alert.alert(
      'Delete Character',
      `Delete "${draft?.metadata.character_name || 'this character'}"? This cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => deleteMutation.mutate(),
        },
      ]
    );
  };

  const handleExport = async () => {
    try {
      const assets = draft?.assets || {};
      const content = Object.entries(assets)
        .map(([name, value]) => `=== ${name.replace(/_/g, ' ').toUpperCase()} ===\n${value}`)
        .join('\n\n');

      await Share.share({
        message: content,
        title: draft?.metadata.character_name || 'Character Export',
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to export character');
    }
  };

  const handleShareJson = async () => {
    try {
      const jsonContent = JSON.stringify(draft, null, 2);
      await Share.share({
        message: jsonContent,
        title: `${draft?.metadata.character_name || 'Character'} (JSON)`,
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to export character');
    }
  };

  const handleCopyAsset = async (assetName: string, content: string) => {
    await Clipboard.setStringAsync(content);
    Alert.alert('Copied', `${assetName.replace(/_/g, ' ')} copied to clipboard`);
  };

  const handleRefine = (assetName?: string) => {
    navigation.navigate('Chat', { draftId, asset: assetName });
  };

  const handleOpenEditModal = () => {
    if (draft) {
      setEditName(draft.metadata.character_name || '');
      setEditGenre(draft.metadata.genre || '');
      setEditTags(draft.metadata.tags?.join(', ') || '');
      setEditNotes(draft.metadata.notes || '');
      setEditModalVisible(true);
    }
  };

  const handleSaveMetadata = () => {
    const tagsArray = editTags
      .split(',')
      .map(t => t.trim())
      .filter(t => t.length > 0);

    updateMetadataMutation.mutate({
      character_name: editName.trim() || undefined,
      genre: editGenre.trim() || undefined,
      tags: tagsArray.length > 0 ? tagsArray : undefined,
      notes: editNotes.trim() || undefined,
    });
  };

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#7c3aed" />
      </View>
    );
  }

  if (error || !draft) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>Error loading draft</Text>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const assetNames = Object.keys(draft.assets);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <ArrowLeftIcon color="#9ca3af" size={24} />
        </TouchableOpacity>
        <View style={styles.headerContent}>
          <Text style={styles.title} numberOfLines={1}>
            {draft.metadata.character_name || 'Character'}
          </Text>
          <View style={styles.headerActions}>
            <TouchableOpacity
              onPress={handleOpenEditModal}
              style={styles.editHeaderButton}
            >
              <PencilIcon color="#7c3aed" size={20} />
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => handleRefine()}
              style={styles.refineHeaderButton}
            >
              <ChatBubbleIcon color="#7c3aed" size={20} />
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => toggleFavorite.mutate()}
              style={styles.favoriteButton}
            >
              <StarIcon
                color={draft.metadata.favorite ? '#eab308' : '#6b7280'}
                size={24}
              />
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* Tags */}
      <ScrollView horizontal style={styles.tagsContainer} contentContainerStyle={styles.tagsContent}>
        {draft.metadata.mode && (
          <View style={[styles.tag, styles.tagPrimary]}>
            <Text style={styles.tagPrimaryText}>{draft.metadata.mode}</Text>
          </View>
        )}
        {draft.metadata.genre && (
          <View style={styles.tag}>
            <Text style={styles.tagText}>{draft.metadata.genre}</Text>
          </View>
        )}
        {draft.metadata.template_name && (
          <View style={styles.tag}>
            <Text style={styles.tagText}>{draft.metadata.template_name}</Text>
          </View>
        )}
        {draft.metadata.tags?.map((tag) => (
          <View key={tag} style={styles.tag}>
            <Text style={styles.tagText}>{tag}</Text>
          </View>
        ))}
      </ScrollView>

      {/* Actions */}
      <View style={styles.actionsContainer}>
        <TouchableOpacity style={styles.actionButton} onPress={() => handleRefine()}>
          <ChatBubbleIcon color="#7c3aed" size={18} />
          <Text style={styles.actionButtonText}>Refine</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton} onPress={handleExport}>
          <DocumentTextIcon color="#7c3aed" size={18} />
          <Text style={styles.actionButtonText}>Text</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton} onPress={handleShareJson}>
          <DocumentTextIcon color="#7c3aed" size={18} />
          <Text style={styles.actionButtonText}>JSON</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.actionButton, styles.deleteActionButton]} onPress={handleDelete}>
          <TrashIcon color="#ef4444" size={18} />
          <Text style={[styles.actionButtonText, styles.deleteActionText]}>Delete</Text>
        </TouchableOpacity>
      </View>

      {/* Metadata Info */}
      <View style={styles.metaContainer}>
        {draft.metadata.created && (
          <View style={styles.metaItem}>
            <Text style={styles.metaLabel}>Created</Text>
            <Text style={styles.metaValue}>{new Date(draft.metadata.created).toLocaleDateString()}</Text>
          </View>
        )}
        {draft.metadata.model && (
          <View style={styles.metaItem}>
            <Text style={styles.metaLabel}>Model</Text>
            <Text style={styles.metaValue} numberOfLines={1}>{draft.metadata.model}</Text>
          </View>
        )}
        {draft.metadata.parent_drafts && draft.metadata.parent_drafts.length > 0 && (
          <View style={styles.metaItem}>
            <Text style={styles.metaLabel}>Parents</Text>
            <Text style={styles.metaValue}>{draft.metadata.parent_drafts.join(' + ')}</Text>
          </View>
        )}
      </View>

      {/* Assets */}
      <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>
        {draft.metadata.notes && (
          <View style={styles.notesSection}>
            <Text style={styles.notesLabel}>Notes</Text>
            <Text style={styles.notesText}>{draft.metadata.notes}</Text>
          </View>
        )}

        {assetNames.map((assetName) => (
          <View key={assetName} style={styles.assetSection}>
            <View style={styles.assetHeader}>
              <Text style={styles.assetTitle}>
                {assetName.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </Text>
              <View style={styles.assetActions}>
                <TouchableOpacity
                  style={styles.assetActionButton}
                  onPress={() => handleCopyAsset(assetName, draft.assets[assetName])}
                >
                  <ClipboardDocumentIcon color="#9ca3af" size={16} />
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.assetActionButton}
                  onPress={() => handleRefine(assetName)}
                >
                  <ChatBubbleIcon color="#7c3aed" size={16} />
                </TouchableOpacity>
              </View>
            </View>
            <View style={styles.assetContent}>
              <Text style={styles.assetText}>{draft.assets[assetName]}</Text>
            </View>
          </View>
        ))}
      </ScrollView>

      {/* Edit Metadata Modal */}
      <Modal
        visible={editModalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setEditModalVisible(false)}
      >
        <KeyboardAvoidingView
          style={styles.modalContainer}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setEditModalVisible(false)}>
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Edit Details</Text>
            <TouchableOpacity
              onPress={handleSaveMetadata}
              disabled={updateMetadataMutation.isPending}
            >
              {updateMetadataMutation.isPending ? (
                <ActivityIndicator size="small" color="#7c3aed" />
              ) : (
                <Text style={styles.modalSaveText}>Save</Text>
              )}
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent} contentContainerStyle={styles.modalContentContainer}>
            {/* Character Name */}
            <View style={styles.editField}>
              <Text style={styles.editLabel}>Character Name</Text>
              <TextInput
                style={styles.editInput}
                value={editName}
                onChangeText={setEditName}
                placeholder="Enter character name"
                placeholderTextColor="#6b7280"
              />
            </View>

            {/* Genre */}
            <View style={styles.editField}>
              <Text style={styles.editLabel}>Genre</Text>
              <TextInput
                style={styles.editInput}
                value={editGenre}
                onChangeText={setEditGenre}
                placeholder="e.g., Fantasy, Sci-Fi, Romance"
                placeholderTextColor="#6b7280"
              />
            </View>

            {/* Tags */}
            <View style={styles.editField}>
              <Text style={styles.editLabel}>Tags</Text>
              <TextInput
                style={styles.editInput}
                value={editTags}
                onChangeText={setEditTags}
                placeholder="Comma-separated tags"
                placeholderTextColor="#6b7280"
              />
              <Text style={styles.editHint}>Separate multiple tags with commas</Text>
            </View>

            {/* Notes */}
            <View style={styles.editField}>
              <Text style={styles.editLabel}>Notes</Text>
              <TextInput
                style={[styles.editInput, styles.editTextArea]}
                value={editNotes}
                onChangeText={setEditNotes}
                placeholder="Add personal notes about this character..."
                placeholderTextColor="#6b7280"
                multiline
                numberOfLines={4}
                textAlignVertical="top"
              />
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>
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
  errorText: {
    color: '#ef4444',
    fontSize: 16,
    marginBottom: 16,
  },
  backText: {
    color: '#7c3aed',
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1f1f1f',
  },
  backButton: {
    marginRight: 12,
  },
  headerContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  refineHeaderButton: {
    padding: 8,
  },
  editHeaderButton: {
    padding: 8,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    flex: 1,
  },
  favoriteButton: {
    padding: 8,
  },
  tagsContainer: {
    maxHeight: 50,
    borderBottomWidth: 1,
    borderBottomColor: '#1f1f1f',
  },
  tagsContent: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
  },
  tag: {
    backgroundColor: '#1f1f1f',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
  },
  tagPrimary: {
    backgroundColor: '#7c3aed',
  },
  tagText: {
    color: '#9ca3af',
    fontSize: 12,
  },
  tagPrimaryText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '500',
  },
  actionsContainer: {
    flexDirection: 'row',
    padding: 12,
    gap: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#1f1f1f',
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#1f1f1f',
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  deleteActionButton: {
    borderColor: '#7f1d1d',
    backgroundColor: 'transparent',
  },
  actionButtonText: {
    color: '#7c3aed',
    fontSize: 13,
    fontWeight: '500',
  },
  deleteActionText: {
    color: '#ef4444',
  },
  metaContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1f1f1f',
  },
  metaItem: {
    flex: 1,
  },
  metaLabel: {
    color: '#6b7280',
    fontSize: 11,
    marginBottom: 2,
  },
  metaValue: {
    color: '#d1d5db',
    fontSize: 12,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
  },
  notesSection: {
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  notesLabel: {
    color: '#9ca3af',
    fontSize: 12,
    marginBottom: 4,
  },
  notesText: {
    color: '#d1d5db',
    fontSize: 14,
  },
  assetSection: {
    marginBottom: 24,
  },
  assetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  assetTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    flex: 1,
  },
  assetActions: {
    flexDirection: 'row',
    gap: 8,
  },
  assetActionButton: {
    padding: 4,
  },
  assetContent: {
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  assetText: {
    color: '#d1d5db',
    fontSize: 14,
    fontFamily: 'monospace',
    lineHeight: 20,
  },
  // Modal styles
  modalContainer: {
    flex: 1,
    backgroundColor: '#0f0f0f',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1f1f1f',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  modalCancelText: {
    color: '#9ca3af',
    fontSize: 16,
  },
  modalSaveText: {
    color: '#7c3aed',
    fontSize: 16,
    fontWeight: '600',
  },
  modalContent: {
    flex: 1,
  },
  modalContentContainer: {
    padding: 16,
  },
  editField: {
    marginBottom: 20,
  },
  editLabel: {
    color: '#9ca3af',
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  editInput: {
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 12,
    color: '#fff',
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  editTextArea: {
    minHeight: 100,
  },
  editHint: {
    color: '#6b7280',
    fontSize: 12,
    marginTop: 4,
  },
});
