import { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Alert, Modal, FlatList } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../config/api';
import { Cog6ToothIcon } from '../components/Icons';
import type { ModelInfo, Config, BatchConfig } from '@char-gen/shared';

export default function SettingsScreen() {
  const queryClient = useQueryClient();
  const [testProvider, setTestProvider] = useState<string | null>(null);
  const [modelsModalVisible, setModelsModalVisible] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [refreshingModels, setRefreshingModels] = useState(false);

  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: () => api.getConfig(),
  });

  const { data: modelsData, isLoading: modelsLoading, refetch: refetchModels } = useQuery({
    queryKey: ['models', selectedProvider],
    queryFn: () => api.getModels(selectedProvider!),
    enabled: !!selectedProvider,
  });

  const testMutation = useMutation({
    mutationFn: (provider: string) => api.testConnection({ provider }),
    onSuccess: (result) => {
      setTestProvider(null);
      if (result.success) {
        Alert.alert('Success', `Connected! Latency: ${result.latency_ms?.toFixed(0)}ms`);
      } else {
        Alert.alert('Failed', result.error || 'Connection failed');
      }
    },
    onError: (error: any) => {
      setTestProvider(null);
      Alert.alert('Error', error?.detail || 'Test failed');
    },
  });

  const updateConfigMutation = useMutation({
    mutationFn: (updates: Partial<Config>) => api.updateConfig(updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
    },
    onError: (error: any) => {
      Alert.alert('Error', error?.detail || 'Failed to update config');
    },
  });

  const handleTest = (provider: string) => {
    setTestProvider(provider);
    testMutation.mutate(provider);
  };

  const handleOpenModels = (provider: string) => {
    setSelectedProvider(provider);
    setModelsModalVisible(true);
  };

  const handleRefreshModels = async () => {
    if (!selectedProvider) return;
    setRefreshingModels(true);
    try {
      await api.refreshModels(selectedProvider);
      await refetchModels();
    } catch (error) {
      Alert.alert('Error', 'Failed to refresh models');
    } finally {
      setRefreshingModels(false);
    }
  };

  const handleSelectModel = (model: ModelInfo) => {
    updateConfigMutation.mutate({
      engine: selectedProvider as any,
      model: model.id,
    });
    setModelsModalVisible(false);
  };

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#7c3aed" />
      </View>
    );
  }

  const providers = ['openai', 'google', 'openrouter', 'anthropic', 'deepseek', 'zai', 'moonshot'];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Settings</Text>
      <Text style={styles.subtitle}>Configure API keys and generation settings</Text>

      {/* API Keys */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>API Providers</Text>
        <Text style={styles.sectionDesc}>Test connections and select models</Text>

        {providers.map((provider) => {
          const isActive = config?.engine === provider;
          return (
            <View key={provider} style={[styles.apiKeyItem, isActive && styles.apiKeyItemActive]}>
              <View style={styles.apiKeyHeader}>
                <View style={styles.apiKeyLabelRow}>
                  <Text style={styles.apiKeyLabel}>
                    {provider.charAt(0).toUpperCase() + provider.slice(1)}
                  </Text>
                  {isActive && (
                    <View style={styles.activeBadge}>
                      <Text style={styles.activeBadgeText}>Active</Text>
                    </View>
                  )}
                </View>
                <View style={styles.apiKeyActions}>
                  <TouchableOpacity
                    style={[styles.testButton, testProvider === provider && styles.testButtonLoading]}
                    onPress={() => handleTest(provider)}
                    disabled={testMutation.isPending}
                  >
                    {testProvider === provider ? (
                      <ActivityIndicator size="small" color="#7c3aed" />
                    ) : (
                      <Text style={styles.testButtonText}>Test</Text>
                    )}
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.modelsButton}
                    onPress={() => handleOpenModels(provider)}
                  >
                    <Text style={styles.modelsButtonText}>Models</Text>
                  </TouchableOpacity>
                </View>
              </View>
              <View style={styles.apiKeyStatus}>
                <View style={[styles.statusDot, config?.api_keys?.[provider] ? styles.statusDotActive : styles.statusDotInactive]} />
                <Text style={styles.statusText}>
                  {config?.api_keys?.[provider] ? 'API key set' : 'No API key'}
                </Text>
                {isActive && config?.model && (
                  <Text style={styles.activeModelText} numberOfLines={1}>
                    {' • '}{config.model}
                  </Text>
                )}
              </View>
            </View>
          );
        })}
      </View>

      {/* Current Model */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Current Model</Text>

        <View style={styles.currentModelCard}>
          <View style={styles.currentModelRow}>
            <Text style={styles.currentModelLabel}>Engine</Text>
            <Text style={styles.currentModelValue}>{config?.engine || 'auto'}</Text>
          </View>
          <View style={styles.currentModelRow}>
            <Text style={styles.currentModelLabel}>Model</Text>
            <Text style={styles.currentModelValue} numberOfLines={1}>
              {config?.model || 'Not set'}
            </Text>
          </View>
          {config?.base_url && (
            <View style={styles.currentModelRow}>
              <Text style={styles.currentModelLabel}>Base URL</Text>
              <Text style={styles.currentModelValue} numberOfLines={1}>
                {config.base_url}
              </Text>
            </View>
          )}
        </View>
      </View>

      {/* Generation Settings */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Generation Settings</Text>

        <View style={styles.settingItem}>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Temperature</Text>
            <Text style={styles.settingValue}>{config?.temperature ?? 0.7}</Text>
          </View>
          <View style={styles.settingButtons}>
            <TouchableOpacity
              style={styles.settingButton}
              onPress={() => {
                const newTemp = Math.max(0, (config?.temperature ?? 0.7) - 0.1);
                updateConfigMutation.mutate({ temperature: Math.round(newTemp * 10) / 10 });
              }}
            >
              <Text style={styles.settingButtonText}>−</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.settingButton}
              onPress={() => {
                const newTemp = Math.min(2, (config?.temperature ?? 0.7) + 0.1);
                updateConfigMutation.mutate({ temperature: Math.round(newTemp * 10) / 10 });
              }}
            >
              <Text style={styles.settingButtonText}>+</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.settingItem}>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Max Tokens</Text>
            <Text style={styles.settingValue}>{config?.max_tokens ?? 4096}</Text>
          </View>
          <View style={styles.settingButtons}>
            <TouchableOpacity
              style={styles.settingButton}
              onPress={() => {
                const newTokens = Math.max(256, (config?.max_tokens ?? 4096) - 256);
                updateConfigMutation.mutate({ max_tokens: newTokens });
              }}
            >
              <Text style={styles.settingButtonText}>−</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.settingButton}
              onPress={() => {
                const newTokens = Math.min(32768, (config?.max_tokens ?? 4096) + 256);
                updateConfigMutation.mutate({ max_tokens: newTokens });
              }}
            >
              <Text style={styles.settingButtonText}>+</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.settingItem}>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Max Concurrent</Text>
            <Text style={styles.settingValue}>{config?.batch?.max_concurrent ?? 3}</Text>
          </View>
          <View style={styles.settingButtons}>
            <TouchableOpacity
              style={styles.settingButton}
              onPress={() => {
                const currentBatch = config?.batch ?? { max_concurrent: 3, rate_limit_delay: 1 };
                const newConcurrent = Math.max(1, currentBatch.max_concurrent - 1);
                updateConfigMutation.mutate({ batch: { ...currentBatch, max_concurrent: newConcurrent } });
              }}
            >
              <Text style={styles.settingButtonText}>−</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.settingButton}
              onPress={() => {
                const currentBatch = config?.batch ?? { max_concurrent: 3, rate_limit_delay: 1 };
                const newConcurrent = Math.min(10, currentBatch.max_concurrent + 1);
                updateConfigMutation.mutate({ batch: { ...currentBatch, max_concurrent: newConcurrent } });
              }}
            >
              <Text style={styles.settingButtonText}>+</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.settingItem}>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Rate Limit Delay</Text>
            <Text style={styles.settingValue}>{config?.batch?.rate_limit_delay ?? 1}s</Text>
          </View>
          <View style={styles.settingButtons}>
            <TouchableOpacity
              style={styles.settingButton}
              onPress={() => {
                const currentBatch = config?.batch ?? { max_concurrent: 3, rate_limit_delay: 1 };
                const newDelay = Math.max(0, currentBatch.rate_limit_delay - 0.5);
                updateConfigMutation.mutate({ batch: { ...currentBatch, rate_limit_delay: Math.round(newDelay * 10) / 10 } });
              }}
            >
              <Text style={styles.settingButtonText}>−</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.settingButton}
              onPress={() => {
                const currentBatch = config?.batch ?? { max_concurrent: 3, rate_limit_delay: 1 };
                const newDelay = Math.min(10, currentBatch.rate_limit_delay + 0.5);
                updateConfigMutation.mutate({ batch: { ...currentBatch, rate_limit_delay: Math.round(newDelay * 10) / 10 } });
              }}
            >
              <Text style={styles.settingButtonText}>+</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* Engine Mode */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Engine Mode</Text>
        <Text style={styles.sectionDesc}>How the AI provider is selected</Text>

        <View style={styles.engineModeContainer}>
          <TouchableOpacity
            style={[styles.engineModeButton, config?.engine_mode === 'auto' && styles.engineModeButtonActive]}
            onPress={() => updateConfigMutation.mutate({ engine_mode: 'auto' })}
          >
            <Text style={[styles.engineModeText, config?.engine_mode === 'auto' && styles.engineModeTextActive]}>
              Auto
            </Text>
            <Text style={styles.engineModeDesc}>Automatically select best available</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.engineModeButton, config?.engine_mode === 'explicit' && styles.engineModeButtonActive]}
            onPress={() => updateConfigMutation.mutate({ engine_mode: 'explicit' })}
          >
            <Text style={[styles.engineModeText, config?.engine_mode === 'explicit' && styles.engineModeTextActive]}>
              Explicit
            </Text>
            <Text style={styles.engineModeDesc}>Use only the selected engine</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>
        <View style={styles.aboutCard}>
          <Cog6ToothIcon color="#7c3aed" size={32} />
          <Text style={styles.aboutTitle}>Eidolon Simulacra</Text>
          <Text style={styles.aboutVersion}>Version 2.0.0</Text>
          <Text style={styles.aboutText}>
            Mobile companion app for the Eidolon Simulacra system.
            Configure API keys through the web interface.
          </Text>
        </View>
      </View>

      {/* Connection Status */}
      <View style={styles.connectionCard}>
        <View style={styles.connectionHeader}>
          <Text style={styles.connectionTitle}>Server Connection</Text>
          <View style={[styles.connectionDot, styles.connectionDotActive]} />
        </View>
        <Text style={styles.connectionUrl}>
          Connected to API server
        </Text>
      </View>

      {/* Models Modal */}
      <Modal
        visible={modelsModalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setModelsModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {selectedProvider ? `${selectedProvider.charAt(0).toUpperCase()}${selectedProvider.slice(1)} Models` : 'Models'}
            </Text>
            <TouchableOpacity onPress={() => setModelsModalVisible(false)}>
              <Text style={styles.modalCloseText}>Close</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={styles.refreshButton}
            onPress={handleRefreshModels}
            disabled={refreshingModels}
          >
            {refreshingModels ? (
              <ActivityIndicator size="small" color="#7c3aed" />
            ) : (
              <Text style={styles.refreshButtonText}>Refresh Models</Text>
            )}
          </TouchableOpacity>

          {modelsLoading ? (
            <View style={styles.modalLoading}>
              <ActivityIndicator size="large" color="#7c3aed" />
              <Text style={styles.modalLoadingText}>Loading models...</Text>
            </View>
          ) : (
            <FlatList
              data={modelsData?.models || []}
              keyExtractor={(item) => item.id}
              contentContainerStyle={styles.modelsList}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={[
                    styles.modelItem,
                    config?.model === item.id && styles.modelItemActive,
                  ]}
                  onPress={() => handleSelectModel(item)}
                >
                  <View style={styles.modelInfo}>
                    <Text style={[
                      styles.modelName,
                      config?.model === item.id && styles.modelNameActive,
                    ]}>
                      {item.name}
                    </Text>
                    <Text style={styles.modelId}>{item.id}</Text>
                    {item.context_length && (
                      <Text style={styles.modelMeta}>
                        Context: {(item.context_length / 1000).toFixed(0)}k tokens
                      </Text>
                    )}
                  </View>
                  {config?.model === item.id && (
                    <View style={styles.modelCheckmark}>
                      <Text style={styles.modelCheckmarkText}>✓</Text>
                    </View>
                  )}
                </TouchableOpacity>
              )}
              ListEmptyComponent={
                <View style={styles.modalEmpty}>
                  <Text style={styles.modalEmptyText}>No models found</Text>
                  <Text style={styles.modalEmptySubtext}>
                    Make sure your API key is configured
                  </Text>
                </View>
              }
            />
          )}
        </View>
      </Modal>
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
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  sectionDesc: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 12,
  },
  apiKeyItem: {
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  apiKeyItemActive: {
    borderColor: '#7c3aed',
    backgroundColor: '#1e1b4b',
  },
  apiKeyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  apiKeyLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  apiKeyLabel: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
  },
  activeBadge: {
    backgroundColor: '#7c3aed',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  activeBadgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
  },
  apiKeyActions: {
    flexDirection: 'row',
    gap: 8,
  },
  testButton: {
    backgroundColor: '#2f2f2f',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  testButtonLoading: {
    opacity: 0.7,
  },
  testButtonText: {
    color: '#7c3aed',
    fontSize: 14,
    fontWeight: '500',
  },
  modelsButton: {
    backgroundColor: '#7c3aed',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  modelsButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  apiKeyStatus: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusDotActive: {
    backgroundColor: '#22c55e',
  },
  statusDotInactive: {
    backgroundColor: '#6b7280',
  },
  statusText: {
    color: '#9ca3af',
    fontSize: 12,
  },
  activeModelText: {
    color: '#7c3aed',
    fontSize: 12,
    flex: 1,
  },
  currentModelCard: {
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  currentModelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#2f2f2f',
  },
  currentModelLabel: {
    color: '#9ca3af',
    fontSize: 14,
  },
  currentModelValue: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
    textAlign: 'right',
    marginLeft: 16,
  },
  settingItem: {
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#2f2f2f',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  settingLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  settingValue: {
    color: '#7c3aed',
    fontSize: 18,
    fontWeight: '600',
  },
  settingButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  settingButton: {
    backgroundColor: '#2f2f2f',
    width: 32,
    height: 32,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  settingButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  // Engine Mode styles
  engineModeContainer: {
    gap: 8,
  },
  engineModeButton: {
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  engineModeButtonActive: {
    borderColor: '#7c3aed',
    backgroundColor: '#1e1b4b',
  },
  engineModeText: {
    color: '#9ca3af',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  engineModeTextActive: {
    color: '#a78bfa',
  },
  engineModeDesc: {
    color: '#6b7280',
    fontSize: 12,
  },
  aboutCard: {
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 20,
    borderWidth: 1,
    borderColor: '#2f2f2f',
    alignItems: 'center',
  },
  aboutTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginTop: 12,
    marginBottom: 4,
  },
  aboutVersion: {
    color: '#7c3aed',
    fontSize: 14,
    marginBottom: 12,
  },
  aboutText: {
    color: '#9ca3af',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  connectionCard: {
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: '#22c55e',
    marginBottom: 24,
  },
  connectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  connectionTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  connectionDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  connectionDotActive: {
    backgroundColor: '#22c55e',
  },
  connectionUrl: {
    color: '#9ca3af',
    fontSize: 12,
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
  modalCloseText: {
    color: '#7c3aed',
    fontSize: 16,
  },
  refreshButton: {
    margin: 16,
    padding: 12,
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  refreshButtonText: {
    color: '#7c3aed',
    fontSize: 14,
    fontWeight: '500',
  },
  modalLoading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalLoadingText: {
    color: '#9ca3af',
    fontSize: 14,
    marginTop: 12,
  },
  modelsList: {
    padding: 16,
    paddingTop: 0,
  },
  modelItem: {
    backgroundColor: '#1f1f1f',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#2f2f2f',
    flexDirection: 'row',
    alignItems: 'center',
  },
  modelItemActive: {
    borderColor: '#7c3aed',
    backgroundColor: '#1e1b4b',
  },
  modelInfo: {
    flex: 1,
  },
  modelName: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 2,
  },
  modelNameActive: {
    color: '#a78bfa',
  },
  modelId: {
    color: '#6b7280',
    fontSize: 12,
    marginBottom: 2,
  },
  modelMeta: {
    color: '#9ca3af',
    fontSize: 11,
  },
  modelCheckmark: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#7c3aed',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modelCheckmarkText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  modalEmpty: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  modalEmptyText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 4,
  },
  modalEmptySubtext: {
    color: '#6b7280',
    fontSize: 14,
  },
});
