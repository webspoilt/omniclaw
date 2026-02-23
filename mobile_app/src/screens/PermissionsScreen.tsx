/**
 * OmniClaw Mobile - Permissions Screen
 * Requests all necessary permissions for "Allow Everything" mode
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Linking,
} from 'react-native';
import { Button, ProgressBar } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { request, check, PERMISSIONS, RESULTS } from 'react-native-permissions';
import { useOmniClawStore } from '../store/omniclawStore';

interface PermissionItem {
  id: string;
  name: string;
  description: string;
  icon: string;
  permission: any;
  required: boolean;
  androidOnly?: boolean;
}

const PERMISSIONS_LIST: PermissionItem[] = [
  {
    id: 'accessibility',
    name: 'Accessibility Service',
    description: 'Control screen and automate UI interactions',
    icon: 'access-point',
    permission: null, // Special handling for accessibility
    required: true,
    androidOnly: true,
  },
  {
    id: 'background',
    name: 'Background Service',
    description: 'Run agent continuously in background',
    icon: 'sync',
    permission: null, // Special handling
    required: true,
  },
  {
    id: 'storage',
    name: 'Storage Access',
    description: 'Read and write files on device',
    icon: 'folder',
    permission: PERMISSIONS.ANDROID.READ_EXTERNAL_STORAGE,
    required: true,
    androidOnly: true,
  },
  {
    id: 'camera',
    name: 'Camera',
    description: 'Capture images and scan documents',
    icon: 'camera',
    permission: PERMISSIONS.ANDROID.CAMERA,
    required: false,
  },
  {
    id: 'microphone',
    name: 'Microphone',
    description: 'Voice commands and audio recording',
    icon: 'microphone',
    permission: PERMISSIONS.ANDROID.RECORD_AUDIO,
    required: false,
  },
  {
    id: 'location',
    name: 'Location',
    description: 'Location-based automation',
    icon: 'map-marker',
    permission: PERMISSIONS.ANDROID.ACCESS_FINE_LOCATION,
    required: false,
  },
  {
    id: 'notifications',
    name: 'Notifications',
    description: 'Receive agent alerts and updates',
    icon: 'bell',
    permission: null,
    required: false,
  },
];

export default function PermissionsScreen({ navigation }: any) {
  const { updatePermissions, setSetupComplete } = useOmniClawStore();
  const [permissionStatus, setPermissionStatus] = useState<Record<string, string>>({});
  const [grantedCount, setGrantedCount] = useState(0);
  
  useEffect(() => {
    checkPermissions();
  }, []);
  
  const checkPermissions = async () => {
    const status: Record<string, string> = {};
    let granted = 0;
    
    for (const perm of PERMISSIONS_LIST) {
      if (perm.permission) {
        const result = await check(perm.permission);
        status[perm.id] = result;
        if (result === RESULTS.GRANTED) {
          granted++;
        }
      } else {
        // Check special permissions
        status[perm.id] = 'unknown';
      }
    }
    
    setPermissionStatus(status);
    setGrantedCount(granted);
  };
  
  const requestPermission = async (perm: PermissionItem) => {
    if (perm.id === 'accessibility') {
      // Open accessibility settings
      Alert.alert(
        'Accessibility Service',
        'OmniClaw needs Accessibility permission to control your device. Please enable it in Settings.',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Open Settings',
            onPress: () => {
              Linking.openSettings();
            },
          },
        ]
      );
      return;
    }
    
    if (perm.id === 'background') {
      // Request battery optimization exemption
      Alert.alert(
        'Background Service',
        'Please disable battery optimization for OmniClaw to run in background.',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Open Settings',
            onPress: () => {
              Linking.openSettings();
            },
          },
        ]
      );
      return;
    }
    
    if (perm.permission) {
      const result = await request(perm.permission);
      setPermissionStatus((prev) => ({
        ...prev,
        [perm.id]: result,
      }));
      
      if (result === RESULTS.GRANTED) {
        setGrantedCount((prev) => prev + 1);
      }
      
      // Update store
      updatePermissions({ [perm.id]: result === RESULTS.GRANTED });
    }
  };
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case RESULTS.GRANTED:
        return { icon: 'check-circle', color: '#10b981' };
      case RESULTS.DENIED:
        return { icon: 'close-circle', color: '#ef4444' };
      case RESULTS.BLOCKED:
        return { icon: 'alert-circle', color: '#f59e0b' };
      default:
        return { icon: 'help-circle', color: '#6b7280' };
    }
  };
  
  const canProceed = () => {
    // Check if all required permissions are granted
    const requiredPerms = PERMISSIONS_LIST.filter((p) => p.required);
    return requiredPerms.every(
      (p) => permissionStatus[p.id] === RESULTS.GRANTED
    );
  };
  
  const proceed = () => {
    setSetupComplete(true);
    navigation.replace('Main');
  };
  
  const progress = grantedCount / PERMISSIONS_LIST.length;
  
  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Icon name="shield-check" size={48} color="#6366f1" />
        <Text style={styles.title}>Allow Everything</Text>
        <Text style={styles.subtitle}>
          Grant permissions to unlock OmniClaw's full potential
        </Text>
        
        <View style={styles.progressContainer}>
          <ProgressBar
            progress={progress}
            color="#6366f1"
            style={styles.progressBar}
          />
          <Text style={styles.progressText}>
            {grantedCount} of {PERMISSIONS_LIST.length} granted
          </Text>
        </View>
      </View>
      
      {/* Permissions List */}
      <ScrollView style={styles.permissionsList}>
        {PERMISSIONS_LIST.map((perm) => {
          const status = permissionStatus[perm.id] || 'unknown';
          const { icon, color } = getStatusIcon(status);
          
          return (
            <TouchableOpacity
              key={perm.id}
              style={styles.permissionItem}
              onPress={() => requestPermission(perm)}
            >
              <View style={styles.permissionIcon}>
                <Icon name={perm.icon} size={24} color="#6366f1" />
              </View>
              
              <View style={styles.permissionInfo}>
                <View style={styles.permissionHeader}>
                  <Text style={styles.permissionName}>{perm.name}</Text>
                  {perm.required && (
                    <View style={styles.requiredBadge}>
                      <Text style={styles.requiredText}>Required</Text>
                    </View>
                  )}
                </View>
                <Text style={styles.permissionDescription}>
                  {perm.description}
                </Text>
              </View>
              
              <Icon name={icon} size={24} color={color} />
            </TouchableOpacity>
          );
        })}
      </ScrollView>
      
      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Required permissions must be granted to continue
        </Text>
        <Button
          mode="contained"
          onPress={proceed}
          disabled={!canProceed()}
          style={styles.proceedButton}
          labelStyle={styles.proceedButtonLabel}
        >
          Continue
        </Button>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f1a',
  },
  header: {
    padding: 24,
    alignItems: 'center',
    backgroundColor: '#1a1a2e',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    marginTop: 16,
  },
  subtitle: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 8,
    marginHorizontal: 32,
  },
  progressContainer: {
    width: '100%',
    marginTop: 24,
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
    backgroundColor: '#2d2d44',
  },
  progressText: {
    fontSize: 12,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 8,
  },
  permissionsList: {
    flex: 1,
    padding: 16,
  },
  permissionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2d2d44',
  },
  permissionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(99, 102, 241, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  permissionInfo: {
    flex: 1,
    marginLeft: 16,
    marginRight: 12,
  },
  permissionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  permissionName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  requiredBadge: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: 8,
  },
  requiredText: {
    fontSize: 10,
    color: '#ef4444',
    fontWeight: 'bold',
  },
  permissionDescription: {
    fontSize: 13,
    color: '#6b7280',
  },
  footer: {
    padding: 24,
    backgroundColor: '#1a1a2e',
    borderTopWidth: 1,
    borderTopColor: '#2d2d44',
  },
  footerText: {
    fontSize: 12,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 16,
  },
  proceedButton: {
    backgroundColor: '#6366f1',
    paddingVertical: 8,
  },
  proceedButtonLabel: {
    fontSize: 16,
    fontWeight: 'bold',
  },
});
