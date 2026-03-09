import { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { type ChatMessage } from '@char-gen/shared';
import { api } from '../config/api';
import { ArrowLeftIcon, ChatBubbleIcon, PaperAirplaneIcon } from '../components/Icons';
import type { ChatRouteProp, DraftsStackNavigationProp } from '../types/navigation';

export default function ChatScreen() {
  const navigation = useNavigation<DraftsStackNavigationProp<'Chat'>>();
  const route = useRoute<ChatRouteProp>();
  const queryClient = useQueryClient();
  const { draftId, asset } = route.params;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  const { data: draft, isLoading } = useQuery({
    queryKey: ['draft', draftId],
    queryFn: () => api.getDraft(decodeURIComponent(draftId)),
    enabled: !!draftId,
  });

  useEffect(() => {
    if (draft) {
      // Initialize with a system context
      const contextMessage: ChatMessage = {
        role: 'system',
        content: `You are helping refine the character "${draft.metadata.character_name || draftId}". ${asset ? `Focus on the "${asset}" aspect.` : 'You can help with any aspect of the character.'}`,
      };
      setMessages([contextMessage]);
    }
  }, [draft, asset]);

  const handleSend = async () => {
    if (!inputText.trim() || isGenerating) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputText.trim(),
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputText('');
    setIsGenerating(true);

    try {
      const stream = api.chat({
        draft_id: draftId,
        messages: newMessages,
        context_asset: asset,
      });

      let assistantContent = '';
      stream.subscribe((event) => {
        if (event.event === 'chunk' && 'content' in event.data) {
          const data = event.data as { content: string };
          assistantContent += data.content;

          // Update the assistant message in place
          setMessages(prev => {
            const updated = [...prev];
            // Check if last message is assistant, update it
            if (updated[updated.length - 1]?.role === 'assistant') {
              updated[updated.length - 1] = {
                role: 'assistant',
                content: assistantContent,
              };
            } else {
              // Add new assistant message
              updated.push({
                role: 'assistant',
                content: assistantContent,
              });
            }
            return updated;
          });
        }
      });

      stream.onError_((error) => {
        console.error('Chat error:', error);
        Alert.alert('Error', 'Failed to get response');
        setIsGenerating(false);
      });

      stream.onComplete_(() => {
        setIsGenerating(false);
        // Refresh draft in case it was updated
        queryClient.invalidateQueries({ queryKey: ['draft', draftId] });
      });

      await stream.start();
    } catch (error) {
      console.error('Chat error:', error);
      Alert.alert('Error', 'Failed to send message');
      setIsGenerating(false);
    }
  };

  const renderMessage = ({ item, index }: { item: ChatMessage; index: number }) => {
    if (item.role === 'system') return null;

    const isUser = item.role === 'user';
    return (
      <View
        style={[
          styles.messageBubble,
          isUser ? styles.userBubble : styles.assistantBubble,
        ]}
      >
        <Text style={[styles.messageText, isUser && styles.userMessageText]}>
          {item.content}
        </Text>
      </View>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#7c3aed" />
      </View>
    );
  }

  const visibleMessages = messages.filter(m => m.role !== 'system');

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <ArrowLeftIcon color="#9ca3af" size={24} />
        </TouchableOpacity>
        <View style={styles.headerContent}>
          <ChatBubbleIcon color="#7c3aed" size={20} />
          <View style={styles.headerText}>
            <Text style={styles.title} numberOfLines={1}>
              {draft?.metadata.character_name || 'Chat'}
            </Text>
            {asset && (
              <Text style={styles.subtitle}>Refining: {asset.replace(/_/g, ' ')}</Text>
            )}
          </View>
        </View>
      </View>

      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={visibleMessages}
        keyExtractor={(_, index) => index.toString()}
        renderItem={renderMessage}
        contentContainerStyle={styles.messagesList}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <ChatBubbleIcon color="#6b7280" size={48} />
            <Text style={styles.emptyTitle}>Start a conversation</Text>
            <Text style={styles.emptyText}>
              Ask for changes, additions, or refinements to your character
            </Text>
          </View>
        }
      />

      {/* Input */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Ask for changes..."
          placeholderTextColor="#6b7280"
          multiline
          maxLength={1000}
          editable={!isGenerating}
        />
        <TouchableOpacity
          style={[styles.sendButton, (!inputText.trim() || isGenerating) && styles.sendButtonDisabled]}
          onPress={handleSend}
          disabled={!inputText.trim() || isGenerating}
        >
          {isGenerating ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <PaperAirplaneIcon color="#fff" size={20} />
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
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
    gap: 12,
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  subtitle: {
    fontSize: 12,
    color: '#9ca3af',
  },
  messagesList: {
    padding: 16,
    paddingBottom: 8,
  },
  messageBubble: {
    maxWidth: '85%',
    padding: 12,
    borderRadius: 16,
    marginBottom: 12,
  },
  userBubble: {
    backgroundColor: '#7c3aed',
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#1f1f1f',
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  messageText: {
    color: '#d1d5db',
    fontSize: 14,
    lineHeight: 20,
  },
  userMessageText: {
    color: '#fff',
  },
  emptyState: {
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
    color: '#6b7280',
    fontSize: 14,
    textAlign: 'center',
    paddingHorizontal: 32,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 12,
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: '#1f1f1f',
    backgroundColor: '#0f0f0f',
  },
  input: {
    flex: 1,
    backgroundColor: '#1f1f1f',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    color: '#fff',
    fontSize: 14,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: '#2f2f2f',
  },
  sendButton: {
    backgroundColor: '#7c3aed',
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#3f3f46',
  },
});
