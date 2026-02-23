/**
 * OmniClaw Mobile - Home Screen
 * Main dashboard showing agent status and quick actions
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
  Dimensions,
} from 'react-native';
import { Card, Button, ProgressBar, Avatar } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import LinearGradient from 'react-native-linear-gradient';
import { useOmniClawStore } from '../store/omniclawStore';

const { width } = Dimensions.get('window');

export default function HomeScreen({ navigation }: any) {
  const { agentStatus, systemStats, messages, apiConfigs } = useOmniClawStore();
  const [pulseAnim] = useState(new Animated.Value(1));
  
  // Pulse animation for active agent
  useEffect(() => {
    if (agentStatus.isRunning) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.2,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [agentStatus.isRunning]);
  
  const getStatusColor = () => {
    if (agentStatus.isRunning) return '#10b981';
    if (apiConfigs.length === 0) return '#ef4444';
    return '#f59e0b';
  };
  
  const getStatusText = () => {
    if (agentStatus.isRunning) return 'Active';
    if (apiConfigs.length === 0) return 'No APIs';
    return 'Standby';
  };
  
  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <LinearGradient
        colors={['#6366f1', '#8b5cf6']}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <View>
            <Text style={styles.headerTitle}>OmniClaw</Text>
            <Text style={styles.headerSubtitle}>Hybrid Hive AI Agent</Text>
          </View>
          <Animated.View
            style={[
              styles.statusIndicator,
              {
                backgroundColor: getStatusColor(),
                transform: [{ scale: pulseAnim }],
              },
            ]}
          />
        </View>
        
        <View style={styles.statusCard}>
          <Text style={styles.statusLabel}>Status</Text>
          <Text style={[styles.statusValue, { color: getStatusColor() }]}>
            {getStatusText()}
          </Text>
          {agentStatus.currentTask && (
            <Text style={styles.currentTask} numberOfLines={1}>
              {agentStatus.currentTask}
            </Text>
          )}
        </View>
      </LinearGradient>
      
      {/* Quick Stats */}
      <View style={styles.statsContainer}>
        <StatCard
          icon="cpu-64-bit"
          label="CPU"
          value={`${systemStats.cpuUsage.toFixed(1)}%`}
          color="#3b82f6"
        />
        <StatCard
          icon="memory"
          label="Memory"
          value={`${systemStats.memoryUsage.toFixed(1)}%`}
          color="#8b5cf6"
        />
        <StatCard
          icon="battery"
          label="Battery"
          value={`${systemStats.batteryLevel}%`}
          color="#10b981"
        />
        <StatCard
          icon="account-group"
          label="Workers"
          value={agentStatus.activeWorkers.toString()}
          color="#f59e0b"
        />
      </View>
      
      {/* Agent Control */}
      <Card style={styles.controlCard}>
        <Card.Content>
          <Text style={styles.cardTitle}>Agent Control</Text>
          
          <View style={styles.controlButtons}>
            <TouchableOpacity
              style={[
                styles.controlButton,
                agentStatus.isRunning && styles.controlButtonActive,
              ]}
              onPress={() => {}}
            >
              <Icon
                name={agentStatus.isRunning ? 'stop' : 'play'}
                size={24}
                color={agentStatus.isRunning ? '#ef4444' : '#10b981'}
              />
              <Text style={styles.controlButtonText}>
                {agentStatus.isRunning ? 'Stop' : 'Start'}
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.controlButton} onPress={() => {}}>
              <Icon name="refresh" size={24} color="#3b82f6" />
              <Text style={styles.controlButtonText}>Restart</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.controlButton} onPress={() => {}}>
              <Icon name="cog" size={24} color="#8b5cf6" />
              <Text style={styles.controlButtonText}>Configure</Text>
            </TouchableOpacity>
          </View>
          
          {agentStatus.queueSize > 0 && (
            <View style={styles.queueInfo}>
              <Text style={styles.queueText}>
                {agentStatus.queueSize} tasks in queue
              </Text>
              <ProgressBar
                progress={0.5}
                color="#6366f1"
                style={styles.queueProgress}
              />
            </View>
          )}
        </Card.Content>
      </Card>
      
      {/* API Status */}
      <Card style={styles.apiCard}>
        <Card.Content>
          <Text style={styles.cardTitle}>API Connections</Text>
          
          {apiConfigs.length === 0 ? (
            <View style={styles.emptyState}>
              <Icon name="api-off" size={48} color="#6b7280" />
              <Text style={styles.emptyText}>No APIs configured</Text>
              <Button
                mode="contained"
                onPress={() => navigation.navigate('Settings')}
                style={styles.emptyButton}
              >
                Add API
              </Button>
            </View>
          ) : (
            <View>
              {apiConfigs.slice(0, 3).map((api) => (
                <View key={api.id} style={styles.apiItem}>
                  <View style={styles.apiInfo}>
                    <Icon
                      name={getProviderIcon(api.provider)}
                      size={20}
                      color="#6366f1"
                    />
                    <Text style={styles.apiName}>{api.provider}</Text>
                  </View>
                  <View
                    style={[
                      styles.apiStatus,
                      { backgroundColor: api.enabled ? '#10b981' : '#ef4444' },
                    ]}
                  >
                    <Text style={styles.apiStatusText}>
                      {api.enabled ? 'Active' : 'Disabled'}
                    </Text>
                  </View>
                </View>
              ))}
              
              {apiConfigs.length > 3 && (
                <Text style={styles.moreApis}>
                  +{apiConfigs.length - 3} more
                </Text>
              )}
            </View>
          )}
        </Card.Content>
      </Card>
      
      {/* Recent Activity */}
      <Card style={styles.activityCard}>
        <Card.Content>
          <Text style={styles.cardTitle}>Recent Activity</Text>
          
          {messages.length === 0 ? (
            <Text style={styles.noActivity}>No recent activity</Text>
          ) : (
            messages.slice(-5).reverse().map((msg) => (
              <View key={msg.id} style={styles.activityItem}>
                <Icon
                  name={getMessageIcon(msg.type)}
                  size={16}
                  color={getMessageColor(msg.type)}
                />
                <Text style={styles.activityText} numberOfLines={2}>
                  {msg.content}
                </Text>
                <Text style={styles.activityTime}>
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </Text>
              </View>
            ))
          )}
        </Card.Content>
      </Card>
    </ScrollView>
  );
}

// Stat Card Component
function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: string;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <View style={[styles.statCard, { borderColor: color }]}>
      <Icon name={icon} size={20} color={color} />
      <Text style={[styles.statValue, { color }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

// Helper functions
function getProviderIcon(provider: string): string {
  const icons: Record<string, string> = {
    openai: 'brain',
    anthropic: 'message-text',
    google: 'google',
    ollama: 'llama',
    custom: 'code-braces',
  };
  return icons[provider] || 'api';
}

function getMessageIcon(type: string): string {
  const icons: Record<string, string> = {
    user: 'account',
    agent: 'robot',
    system: 'information',
  };
  return icons[type] || 'help-circle';
}

function getMessageColor(type: string): string {
  const colors: Record<string, string> = {
    user: '#3b82f6',
    agent: '#10b981',
    system: '#6b7280',
  };
  return colors[type] || '#6b7280';
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f1a',
  },
  header: {
    padding: 20,
    paddingTop: 60,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
    marginTop: 4,
  },
  statusIndicator: {
    width: 16,
    height: 16,
    borderRadius: 8,
  },
  statusCard: {
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderRadius: 12,
    padding: 16,
  },
  statusLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.6)',
    textTransform: 'uppercase',
  },
  statusValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 4,
  },
  currentTask: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.7)',
    marginTop: 8,
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    gap: 12,
  },
  statCard: {
    width: (width - 56) / 2,
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2d2d44',
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
  controlCard: {
    margin: 16,
    marginTop: 0,
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 16,
  },
  controlButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  controlButton: {
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    backgroundColor: '#2d2d44',
    minWidth: 80,
  },
  controlButtonActive: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
  },
  controlButtonText: {
    color: '#ffffff',
    marginTop: 8,
    fontSize: 12,
  },
  queueInfo: {
    marginTop: 8,
  },
  queueText: {
    color: '#6b7280',
    fontSize: 12,
    marginBottom: 8,
  },
  queueProgress: {
    height: 4,
    borderRadius: 2,
  },
  apiCard: {
    margin: 16,
    marginTop: 0,
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
  },
  emptyState: {
    alignItems: 'center',
    padding: 24,
  },
  emptyText: {
    color: '#6b7280',
    marginTop: 12,
    marginBottom: 16,
  },
  emptyButton: {
    backgroundColor: '#6366f1',
  },
  apiItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#2d2d44',
  },
  apiInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  apiName: {
    color: '#ffffff',
    marginLeft: 12,
    textTransform: 'capitalize',
  },
  apiStatus: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  apiStatusText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  moreApis: {
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 12,
  },
  activityCard: {
    margin: 16,
    marginTop: 0,
    marginBottom: 32,
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
  },
  noActivity: {
    color: '#6b7280',
    textAlign: 'center',
    padding: 24,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#2d2d44',
  },
  activityText: {
    color: '#ffffff',
    flex: 1,
    marginLeft: 12,
    marginRight: 8,
  },
  activityTime: {
    color: '#6b7280',
    fontSize: 11,
  },
});
