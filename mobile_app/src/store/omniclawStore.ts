/**
 * OmniClaw Mobile - Zustand Store
 * Global state management for the app
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Types
export interface APIConfig {
  id: string;
  provider: 'openai' | 'anthropic' | 'google' | 'ollama' | 'custom';
  key: string;
  model: string;
  baseUrl?: string;
  priority: number;
  enabled: boolean;
}

export interface AgentStatus {
  isRunning: boolean;
  currentTask: string | null;
  activeWorkers: number;
  queueSize: number;
  lastActivity: number;
}

export interface SystemStats {
  cpuUsage: number;
  memoryUsage: number;
  batteryLevel: number;
  networkStatus: 'online' | 'offline';
  storageUsed: number;
  storageTotal: number;
}

export interface Message {
  id: string;
  type: 'user' | 'agent' | 'system';
  content: string;
  timestamp: number;
  metadata?: any;
}

interface OmniClawState {
  // App state
  isInitialized: boolean;
  isSetupComplete: boolean;
  
  // API configurations
  apiConfigs: APIConfig[];
  
  // Agent state
  agentStatus: AgentStatus;
  
  // System stats
  systemStats: SystemStats;
  
  // Messages
  messages: Message[];
  
  // Settings
  settings: {
    autoStart: boolean;
    backgroundMode: boolean;
    notifications: boolean;
    voiceInput: boolean;
    darkMode: boolean;
    language: string;
    theme: 'default' | 'cyberpunk' | 'minimal';
  };
  
  // Permissions
  permissions: {
    accessibility: boolean;
    backgroundService: boolean;
    storage: boolean;
    camera: boolean;
    microphone: boolean;
    location: boolean;
  };
  
  // Actions
  setInitialized: (value: boolean) => void;
  setSetupComplete: (value: boolean) => void;
  addApiConfig: (config: APIConfig) => void;
  removeApiConfig: (id: string) => void;
  updateApiConfig: (id: string, updates: Partial<APIConfig>) => void;
  setAgentStatus: (status: Partial<AgentStatus>) => void;
  setSystemStats: (stats: Partial<SystemStats>) => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  clearMessages: () => void;
  updateSettings: (settings: Partial<OmniClawState['settings']>) => void;
  updatePermissions: (permissions: Partial<OmniClawState['permissions']>) => void;
  reset: () => void;
}

const initialState = {
  isInitialized: false,
  isSetupComplete: false,
  apiConfigs: [],
  agentStatus: {
    isRunning: false,
    currentTask: null,
    activeWorkers: 0,
    queueSize: 0,
    lastActivity: 0,
  },
  systemStats: {
    cpuUsage: 0,
    memoryUsage: 0,
    batteryLevel: 100,
    networkStatus: 'online',
    storageUsed: 0,
    storageTotal: 0,
  },
  messages: [],
  settings: {
    autoStart: false,
    backgroundMode: true,
    notifications: true,
    voiceInput: true,
    darkMode: true,
    language: 'en',
    theme: 'cyberpunk',
  },
  permissions: {
    accessibility: false,
    backgroundService: false,
    storage: false,
    camera: false,
    microphone: false,
    location: false,
  },
};

export const useOmniClawStore = create<OmniClawState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      setInitialized: (value) => set({ isInitialized: value }),
      
      setSetupComplete: (value) => set({ isSetupComplete: value }),
      
      addApiConfig: (config) => set((state) => ({
        apiConfigs: [...state.apiConfigs, config],
      })),
      
      removeApiConfig: (id) => set((state) => ({
        apiConfigs: state.apiConfigs.filter((c) => c.id !== id),
      })),
      
      updateApiConfig: (id, updates) => set((state) => ({
        apiConfigs: state.apiConfigs.map((c) =>
          c.id === id ? { ...c, ...updates } : c
        ),
      })),
      
      setAgentStatus: (status) => set((state) => ({
        agentStatus: { ...state.agentStatus, ...status },
      })),
      
      setSystemStats: (stats) => set((state) => ({
        systemStats: { ...state.systemStats, ...stats },
      })),
      
      addMessage: (message) => set((state) => ({
        messages: [
          ...state.messages,
          {
            ...message,
            id: Math.random().toString(36).substr(2, 9),
            timestamp: Date.now(),
          },
        ],
      })),
      
      clearMessages: () => set({ messages: [] }),
      
      updateSettings: (newSettings) => set((state) => ({
        settings: { ...state.settings, ...newSettings },
      })),
      
      updatePermissions: (newPermissions) => set((state) => ({
        permissions: { ...state.permissions, ...newPermissions },
      })),
      
      reset: () => set(initialState),
    }),
    {
      name: 'omniclaw-storage',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);
