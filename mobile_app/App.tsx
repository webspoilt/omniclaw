/**
 * OmniClaw Mobile Super-App
 * Main entry point for the AI Agent Controller
 */

import React, { useEffect, useState } from 'react';
import { StatusBar, LogBox, View, Text, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Provider as PaperProvider, DefaultTheme } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

// Screens
import HomeScreen from './src/screens/HomeScreen';
import AgentScreen from './src/screens/AgentScreen';
import TerminalScreen from './src/screens/TerminalScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import PermissionsScreen from './src/screens/PermissionsScreen';
import SetupScreen from './src/screens/SetupScreen';

// Services
import { initializeServices } from './src/services/InitializationService';
import { useOmniClawStore } from './src/store/omniclawStore';

// Theme
const theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: '#6366f1',
    accent: '#8b5cf6',
    background: '#0f0f1a',
    surface: '#1a1a2e',
    text: '#ffffff',
    placeholder: '#6b7280',
  },
};

// Navigation
const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

// Main Tab Navigator
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;
          
          switch (route.name) {
            case 'Home':
              iconName = focused ? 'home' : 'home-outline';
              break;
            case 'Agent':
              iconName = focused ? 'robot' : 'robot-outline';
              break;
            case 'Terminal':
              iconName = focused ? 'console' : 'console-line';
              break;
            case 'Settings':
              iconName = focused ? 'cog' : 'cog-outline';
              break;
            default:
              iconName = 'help-circle';
          }
          
          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#6366f1',
        tabBarInactiveTintColor: '#6b7280',
        tabBarStyle: {
          backgroundColor: '#1a1a2e',
          borderTopColor: '#2d2d44',
        },
        headerStyle: {
          backgroundColor: '#1a1a2e',
        },
        headerTintColor: '#ffffff',
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Agent" component={AgentScreen} />
      <Tab.Screen name="Terminal" component={TerminalScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

// Loading Screen
function LoadingScreen({ message }: { message: string }) {
  return (
    <View style={styles.loadingContainer}>
      <Icon name="brain" size={80} color="#6366f1" />
      <Text style={styles.loadingTitle}>OmniClaw</Text>
      <Text style={styles.loadingSubtitle}>{message}</Text>
    </View>
  );
}

// Main App Component
export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState('Initializing...');
  const [isFirstRun, setIsFirstRun] = useState(false);
  const [hasPermissions, setHasPermissions] = useState(false);
  
  const { isInitialized, setInitialized } = useOmniClawStore();
  
  useEffect(() => {
    // Ignore specific warnings
    LogBox.ignoreLogs([
      'Non-serializable values were found in the navigation state',
    ]);
    
    // Initialize app
    initializeApp();
  }, []);
  
  const initializeApp = async () => {
    try {
      setLoadingMessage('Checking first run...');
      const needsSetup = await checkFirstRun();
      
      if (needsSetup) {
        setIsFirstRun(true);
        setIsLoading(false);
        return;
      }
      
      setLoadingMessage('Checking permissions...');
      const permissionsGranted = await checkPermissions();
      
      if (!permissionsGranted) {
        setHasPermissions(false);
        setIsLoading(false);
        return;
      }
      
      setLoadingMessage('Starting OmniClaw services...');
      await initializeServices((msg) => setLoadingMessage(msg));
      
      setInitialized(true);
      setIsLoading(false);
    } catch (error) {
      console.error('Initialization error:', error);
      setLoadingMessage('Initialization failed. Please restart.');
    }
  };
  
  const checkFirstRun = async (): Promise<boolean> => {
    // Check if app has been set up before
    // Return true if setup needed
    return false; // Placeholder
  };
  
  const checkPermissions = async (): Promise<boolean> => {
    // Check required permissions
    return true; // Placeholder
  };
  
  if (isLoading) {
    return (
      <PaperProvider theme={theme}>
        <StatusBar barStyle="light-content" backgroundColor="#0f0f1a" />
        <LoadingScreen message={loadingMessage} />
      </PaperProvider>
    );
  }
  
  return (
    <PaperProvider theme={theme}>
      <StatusBar barStyle="light-content" backgroundColor="#0f0f1a" />
      <NavigationContainer>
        <Stack.Navigator
          screenOptions={{
            headerStyle: { backgroundColor: '#1a1a2e' },
            headerTintColor: '#ffffff',
            cardStyle: { backgroundColor: '#0f0f1a' },
          }}
        >
          {isFirstRun ? (
            <Stack.Screen 
              name="Setup" 
              component={SetupScreen} 
              options={{ headerShown: false }}
            />
          ) : !hasPermissions ? (
            <Stack.Screen 
              name="Permissions" 
              component={PermissionsScreen} 
              options={{ headerShown: false }}
            />
          ) : (
            <Stack.Screen 
              name="Main" 
              component={MainTabs} 
              options={{ headerShown: false }}
            />
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </PaperProvider>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: '#0f0f1a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ffffff',
    marginTop: 20,
  },
  loadingSubtitle: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 10,
  },
});
