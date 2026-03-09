import { useEffect, useMemo, useState } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { Blueprint } from '@char-gen/shared';
import { api } from '../config/api';
import type { BlueprintEditorRouteProp, HomeStackNavigationProp } from '../types/navigation';

interface BlueprintFormData {
  name: string;
  description: string;
  invokable: boolean;
  versionMajor: number;
  versionMinor: number;
}

function splitBlueprintBody(content: string): string {
  const firstMarker = content.indexOf('---');
  if (firstMarker !== 0) {
    return content;
  }

  const secondMarker = content.indexOf('---', firstMarker + 3);
  if (secondMarker < 0) {
    return content;
  }

  return content.slice(secondMarker + 3).trim();
}

export default function BlueprintEditorScreen() {
  const navigation = useNavigation<HomeStackNavigationProp<'BlueprintEditor'>>();
  const route = useRoute<BlueprintEditorRouteProp>();
  const queryClient = useQueryClient();
  const { path } = route.params;

  const [formData, setFormData] = useState<BlueprintFormData>({
    name: '',
    description: '',
    invokable: true,
    versionMajor: 1,
    versionMinor: 0,
  });
  const [content, setContent] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [initialBlueprint, setInitialBlueprint] = useState<Blueprint | null>(null);

  const { data: blueprint, isLoading, error } = useQuery({
    queryKey: ['blueprint', path],
    queryFn: () => api.getBlueprint(path),
    enabled: !!path,
  });

  useEffect(() => {
    if (!blueprint) {
      return;
    }

    setInitialBlueprint(blueprint);
    const [major = 1, minor = 0] = blueprint.version.split('.').map(Number);
    setFormData({
      name: blueprint.name,
      description: blueprint.description,
      invokable: blueprint.invokable,
      versionMajor: major,
      versionMinor: minor,
    });
    setContent(splitBlueprintBody(blueprint.content));
  }, [blueprint]);

  const modified = useMemo(() => {
    if (!initialBlueprint) {
      return false;
    }

    return (
      formData.name !== initialBlueprint.name ||
      formData.description !== initialBlueprint.description ||
      formData.invokable !== initialBlueprint.invokable ||
      `${formData.versionMajor}.${formData.versionMinor}` !== initialBlueprint.version ||
      content !== splitBlueprintBody(initialBlueprint.content)
    );
  }, [content, formData, initialBlueprint]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const fullContent = `---\nname: ${formData.name}\ndescription: ${formData.description}\ninvokable: ${formData.invokable}\nversion: ${formData.versionMajor}.${formData.versionMinor}\n---\n${content.trim()}`;
      return api.updateBlueprint(path, fullContent);
    },
    onSuccess: (updated) => {
      setInitialBlueprint(updated);
      queryClient.invalidateQueries({ queryKey: ['blueprints'] });
      queryClient.invalidateQueries({ queryKey: ['blueprint', path] });
    },
  });

  useEffect(() => {
    navigation.setOptions({
      title: formData.name || 'Edit Blueprint',
    });
  }, [formData.name, navigation]);

  const yamlPreview = `---\nname: ${formData.name}\ndescription: ${formData.description}\ninvokable: ${formData.invokable}\nversion: ${formData.versionMajor}.${formData.versionMinor}\n---`;

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#7c3aed" />
      </View>
    );
  }

  if (error || !blueprint) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>{error instanceof Error ? error.message : 'Failed to load blueprint'}</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.headerRow}>
        <View style={styles.headerTextWrap}>
          <Text style={styles.title}>{formData.name}</Text>
          <Text style={styles.subtitle}>{blueprint.category}</Text>
          <Text style={styles.pathText}>{blueprint.path}</Text>
        </View>
        <View style={styles.headerButtons}>
          <TouchableOpacity style={styles.previewButton} onPress={() => setShowPreview((current) => !current)}>
            <Text style={styles.previewButtonText}>{showPreview ? 'Edit' : 'Preview'}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.saveButton, (!modified || saveMutation.isPending) && styles.disabledButton]}
            onPress={() => saveMutation.mutate()}
            disabled={!modified || saveMutation.isPending}
          >
            <Text style={styles.saveButtonText}>{saveMutation.isPending ? 'Saving...' : 'Save'}</Text>
          </TouchableOpacity>
        </View>
      </View>

      {modified ? <Text style={styles.modifiedBanner}>You have unsaved changes.</Text> : null}
      {saveMutation.error ? (
        <Text style={styles.errorBanner}>
          {saveMutation.error instanceof Error ? saveMutation.error.message : 'Failed to save blueprint'}
        </Text>
      ) : null}

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Frontmatter</Text>
        <Text style={styles.fieldLabel}>Name</Text>
        <TextInput
          style={styles.input}
          value={formData.name}
          onChangeText={(name) => setFormData((current) => ({ ...current, name }))}
          placeholder="blueprint_name"
          placeholderTextColor="#6b7280"
        />

        <Text style={styles.fieldLabel}>Description</Text>
        <TextInput
          style={[styles.input, styles.descriptionInput]}
          value={formData.description}
          onChangeText={(description) => setFormData((current) => ({ ...current, description }))}
          placeholder="Brief description of this blueprint"
          placeholderTextColor="#6b7280"
          multiline
          textAlignVertical="top"
        />

        <View style={styles.versionRow}>
          <View style={styles.versionField}>
            <Text style={styles.fieldLabel}>Version Major</Text>
            <TextInput
              style={styles.input}
              value={String(formData.versionMajor)}
              onChangeText={(value) => setFormData((current) => ({ ...current, versionMajor: parseInt(value, 10) || 0 }))}
              keyboardType="number-pad"
            />
          </View>
          <View style={styles.versionField}>
            <Text style={styles.fieldLabel}>Version Minor</Text>
            <TextInput
              style={styles.input}
              value={String(formData.versionMinor)}
              onChangeText={(value) => setFormData((current) => ({ ...current, versionMinor: parseInt(value, 10) || 0 }))}
              keyboardType="number-pad"
            />
          </View>
        </View>

        <TouchableOpacity
          style={[styles.toggleChip, formData.invokable && styles.toggleChipActive]}
          onPress={() => setFormData((current) => ({ ...current, invokable: !current.invokable }))}
        >
          <Text style={[styles.toggleChipText, formData.invokable && styles.toggleChipTextActive]}>
            {formData.invokable ? 'Invokable: On' : 'Invokable: Off'}
          </Text>
        </TouchableOpacity>

        <Text style={styles.fieldLabel}>YAML Preview</Text>
        <View style={styles.previewCard}>
          <Text style={styles.previewText}>{yamlPreview}</Text>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Content</Text>
        {showPreview ? (
          <View style={styles.previewCard}>
            <Text style={styles.previewText}>{content || 'No content yet.'}</Text>
          </View>
        ) : (
          <TextInput
            style={[styles.input, styles.contentInput]}
            value={content}
            onChangeText={setContent}
            placeholder="Enter markdown content here..."
            placeholderTextColor="#6b7280"
            multiline
            textAlignVertical="top"
          />
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
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f0f0f',
    padding: 16,
  },
  content: {
    padding: 16,
    gap: 16,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  headerTextWrap: {
    flex: 1,
  },
  headerButtons: {
    gap: 8,
  },
  title: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  subtitle: {
    color: '#9ca3af',
    fontSize: 13,
    marginBottom: 2,
    textTransform: 'capitalize',
  },
  pathText: {
    color: '#6b7280',
    fontSize: 12,
  },
  previewButton: {
    backgroundColor: '#27272a',
    borderWidth: 1,
    borderColor: '#3f3f46',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    alignItems: 'center',
  },
  previewButtonText: {
    color: '#d1d5db',
    fontSize: 13,
    fontWeight: '500',
  },
  saveButton: {
    backgroundColor: '#7c3aed',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
  disabledButton: {
    opacity: 0.5,
  },
  modifiedBanner: {
    color: '#fcd34d',
    backgroundColor: '#422006',
    borderWidth: 1,
    borderColor: '#854d0e',
    borderRadius: 10,
    padding: 12,
    fontSize: 13,
  },
  errorBanner: {
    color: '#fca5a5',
    backgroundColor: '#450a0a',
    borderWidth: 1,
    borderColor: '#7f1d1d',
    borderRadius: 10,
    padding: 12,
    fontSize: 13,
  },
  card: {
    backgroundColor: '#1f1f1f',
    borderWidth: 1,
    borderColor: '#2f2f2f',
    borderRadius: 12,
    padding: 16,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  fieldLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    marginTop: 6,
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
  descriptionInput: {
    minHeight: 90,
  },
  versionRow: {
    flexDirection: 'row',
    gap: 12,
  },
  versionField: {
    flex: 1,
  },
  toggleChip: {
    marginTop: 14,
    alignSelf: 'flex-start',
    backgroundColor: '#27272a',
    borderWidth: 1,
    borderColor: '#3f3f46',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  toggleChipActive: {
    backgroundColor: '#7c3aed',
    borderColor: '#7c3aed',
  },
  toggleChipText: {
    color: '#d1d5db',
    fontSize: 13,
    fontWeight: '500',
  },
  toggleChipTextActive: {
    color: '#fff',
  },
  previewCard: {
    marginTop: 8,
    backgroundColor: '#111111',
    borderWidth: 1,
    borderColor: '#2f2f2f',
    borderRadius: 10,
    padding: 12,
  },
  previewText: {
    color: '#d1d5db',
    fontSize: 12,
    lineHeight: 19,
    fontFamily: 'monospace',
  },
  contentInput: {
    minHeight: 420,
  },
  errorText: {
    color: '#fca5a5',
    fontSize: 14,
    textAlign: 'center',
  },
});