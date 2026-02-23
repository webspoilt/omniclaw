/**
 * OmniClaw Mobile - Agent Screen
 * Chat interface for interacting with the AI agent
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Animated,
} from 'react-native';
import { Card, IconButton, Avatar } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useOmniClawStore, Message } from '../store/omniclawStore';

export default function AgentScreen() {
  const { messages, addMessage, agentStatus } = useOmniClawStore();
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const flatListRef = useRef<FlatList>(null);
  const inputRef = useRef<TextInput>(null);
  
  // Auto-scroll to bottom
  useEffect(() => {
    if (messages.length > 0) {
      flatListRef.current?.scrollToEnd({ animated: true });
    }
  }, [messages]);
  
  const sendMessage = async () => {
    if (!inputText.trim()) return;
    
    const userMessage = inputText.trim();
    setInputText('');
    
    // Add user message
    addMessage({
      type: 'user',
      content: userMessage,
    });
    
    // Simulate agent response (replace with actual API call)
    setTimeout(() => {
      addMessage({
        type: 'agent',
        content: `Processing: "${userMessage}"...`,
        metadata: { task_id: 'task_001' },
      });
    }, 500);
  };
  
  const startVoiceInput = () => {
    setIsRecording(true);
    // Implement voice recognition
    setTimeout(() => {
      setIsRecording(false);
      setInputText('Voice input simulated');
    }, 2000);
  };
  
  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.type === 'user';
    const isSystem = item.type === 'system';
    
    return (
      <Animated.View
        style={[
          styles.messageContainer,
          isUser ? styles.userMessage : styles.agentMessage,
        ]}
      >
        {!isUser && (
          <Avatar.Icon
            size={32}
            icon={isSystem ? 'information' : 'robot'}
            style={[
              styles.avatar,
              { backgroundColor: isSystem ? '#6b7280' : '#6366f1' },
            ]}
          />
        )}
        
        <Card
          style={[
            styles.messageCard,
            isUser
              ? styles.userCard
              : isSystem
              ? styles.systemCard
              : styles.agentCard,
          ]}
        >
          <Card.Content>
            <Text
              style={[
                styles.messageText,
                isUser ? styles.userText : styles.agentText,
              ]}
            >
              {item.content}
            </Text>
            
            {item.metadata?.task_id && (
              <View style={styles.taskBadge}>
                <Icon name="tag" size={10} color="#6366f1" />
                <Text style={styles.taskText}>{item.metadata.task_id}</Text>
              </View>
            )}
          </Card.Content>
        </Card>
        
        {isUser && (
          <Avatar.Icon
            size={32}
            icon="account"
            style={[styles.avatar, { backgroundColor: '#3b82f6' }]}
          />
        )}
      </Animated.View>
    );
  };
  
  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerInfo}>
          <Icon name="robot" size={24} color="#6366f1" />
          <View style={styles.headerText}>
            <Text style={styles.headerTitle}>OmniClaw Agent</Text>
            <View style={styles.statusRow}>
              <View
                style={[
                  styles.statusDot,
                  {
                    backgroundColor: agentStatus.isRunning
                      ? '#10b981'
                      : '#ef4444',
                  },
                ]}
              />
              <Text style={styles.statusText}>
                {agentStatus.isRunning ? 'Online' : 'Offline'}
              </Text>
            </View>
          </View>
        </View>
        
        <View style={styles.headerActions}>
          <IconButton
            icon="history"
            iconColor="#ffffff"
            size={20}
            onPress={() => {}}
          />
          <IconButton
            icon="cog"
            iconColor="#ffffff"
            size={20}
            onPress={() => {}}
          />
        </View>
      </View>
      
      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.messagesList}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Icon name="robot-happy" size={64} color="#6366f1" />
            <Text style={styles.emptyTitle}>Welcome to OmniClaw</Text>
            <Text style={styles.emptySubtitle}>
              Start a conversation with your AI agent
            </Text>
            
            <View style={styles.suggestions}>
              <SuggestionChip
                text="Research latest AI trends"
                onPress={() => setInputText('Research latest AI trends')}
              />
              <SuggestionChip
                text="Analyze my system"
                onPress={() => setInputText('Analyze my system performance')}
              />
              <SuggestionChip
                text="Write Python script"
                onPress={() => setInputText('Write a Python script to automate file organization')}
              />
            </View>
          </View>
        }
      />
      
      {/* Input Area */}
      <View style={styles.inputContainer}>
        <TouchableOpacity
          style={[
            styles.voiceButton,
            isRecording && styles.voiceButtonActive,
          ]}
          onPress={startVoiceInput}
        >
          <Icon
            name={isRecording ? 'microphone' : 'microphone-outline'}
            size={24}
            color={isRecording ? '#ef4444' : '#ffffff'}
          />
        </TouchableOpacity>
        
        <TextInput
          ref={inputRef}
          style={styles.input}
          placeholder="Type a message..."
          placeholderTextColor="#6b7280"
          value={inputText}
          onChangeText={setInputText}
          onSubmitEditing={sendMessage}
          multiline
          maxLength={2000}
        />
        
        <TouchableOpacity
          style={[
            styles.sendButton,
            !inputText.trim() && styles.sendButtonDisabled,
          ]}
          onPress={sendMessage}
          disabled={!inputText.trim()}
        >
          <Icon name="send" size={20} color="#ffffff" />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

// Suggestion Chip Component
function SuggestionChip({
  text,
  onPress,
}: {
  text: string;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity style={styles.suggestionChip} onPress={onPress}>
      <Text style={styles.suggestionText}>{text}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f1a',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#1a1a2e',
    borderBottomWidth: 1,
    borderBottomColor: '#2d2d44',
  },
  headerInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerText: {
    marginLeft: 12,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 12,
    color: '#6b7280',
  },
  headerActions: {
    flexDirection: 'row',
  },
  messagesList: {
    padding: 16,
    flexGrow: 1,
  },
  messageContainer: {
    flexDirection: 'row',
    marginBottom: 12,
    alignItems: 'flex-end',
  },
  userMessage: {
    justifyContent: 'flex-end',
  },
  agentMessage: {
    justifyContent: 'flex-start',
  },
  avatar: {
    marginHorizontal: 8,
  },
  messageCard: {
    maxWidth: '75%',
    borderRadius: 16,
  },
  userCard: {
    backgroundColor: '#3b82f6',
    borderBottomRightRadius: 4,
  },
  agentCard: {
    backgroundColor: '#1a1a2e',
    borderBottomLeftRadius: 4,
  },
  systemCard: {
    backgroundColor: '#2d2d44',
    alignSelf: 'center',
  },
  messageText: {
    fontSize: 14,
    lineHeight: 20,
  },
  userText: {
    color: '#ffffff',
  },
  agentText: {
    color: '#ffffff',
  },
  taskBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(99, 102, 241, 0.3)',
  },
  taskText: {
    fontSize: 10,
    color: '#6366f1',
    marginLeft: 4,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
    marginTop: 16,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 8,
    textAlign: 'center',
  },
  suggestions: {
    marginTop: 24,
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 8,
  },
  suggestionChip: {
    backgroundColor: '#1a1a2e',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#2d2d44',
  },
  suggestionText: {
    color: '#6366f1',
    fontSize: 13,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#1a1a2e',
    borderTopWidth: 1,
    borderTopColor: '#2d2d44',
  },
  voiceButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#2d2d44',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  voiceButtonActive: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
  },
  input: {
    flex: 1,
    backgroundColor: '#2d2d44',
    borderRadius: 22,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: '#ffffff',
    fontSize: 14,
    maxHeight: 100,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#6366f1',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  sendButtonDisabled: {
    backgroundColor: '#2d2d44',
  },
});
