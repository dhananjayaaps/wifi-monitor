import { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { settingsAPI } from '@/lib/api';

const bytesToMBString = (bytes?: number | null) => {
  if (!bytes || !Number.isFinite(bytes)) return '';
  return (bytes / (1024 * 1024)).toFixed(2);
};

const mbStringToBytes = (value: string): number | null | undefined => {
  const trimmed = value.trim();
  if (!trimmed.length) return null;
  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed) || parsed < 0) return undefined;
  return Math.round(parsed * 1024 * 1024);
};

export default function SettingsScreen() {
  const [defaultCap, setDefaultCap] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await settingsAPI.get();
        const value = response.data.data?.default_device_cap;
        setDefaultCap(bytesToMBString(value));
      } catch (error) {
        console.error('Failed to load settings:', error);
      } finally {
        setLoading(false);
      }
    };
    loadSettings();
  }, []);

  const saveSettings = async () => {
    if (saving) return;
    const value = mbStringToBytes(defaultCap);
    if (value === undefined) {
      Alert.alert('Invalid input', 'Please enter a valid non-negative number of MB, or leave empty to clear.');
      return;
    }
    setSaving(true);
    try {
      const response = await settingsAPI.update(value);
      const updated = response.data.data?.default_device_cap;
      setDefaultCap(bytesToMBString(updated));
      Alert.alert('Saved', 'Settings saved successfully.');
    } catch (error) {
      console.error('Failed to save settings:', error);
      Alert.alert('Error', 'Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2563eb" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Ionicons name="options-outline" size={20} color="#2563eb" />
          <Text style={styles.cardTitle}>Default Device Cap</Text>
        </View>

        <Text style={styles.description}>
          New devices will automatically receive this data cap (in MB). Leave empty to set no default cap.
        </Text>

        <Text style={styles.fieldLabel}>Data Cap (MB)</Text>
        <TextInput
          style={styles.input}
          value={defaultCap}
          onChangeText={setDefaultCap}
          keyboardType="decimal-pad"
          placeholder="e.g. 1024 for 1 GB, empty to clear"
          placeholderTextColor="#94a3b8"
        />
        <Text style={styles.currentValue}>
          Current: {defaultCap ? `${defaultCap} MB` : 'No default cap set'}
        </Text>

        <TouchableOpacity
          style={[styles.saveBtn, saving && styles.saveBtnDisabled]}
          onPress={saveSettings}
          disabled={saving}
          activeOpacity={0.8}
        >
          {saving ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.saveBtnText}>Save Settings</Text>
          )}
        </TouchableOpacity>

        <View style={styles.noteBox}>
          <Ionicons name="information-circle-outline" size={16} color="#b45309" />
          <Text style={styles.noteText}>
            This value is stored in the running backend config and resets on server restart.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f1f5f9' },
  content: { padding: 16, paddingBottom: 40 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 18,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  cardTitle: { fontSize: 17, fontWeight: '700', color: '#0f172a' },
  description: { fontSize: 13, color: '#64748b', marginBottom: 16, lineHeight: 18 },
  fieldLabel: { fontSize: 13, fontWeight: '500', color: '#334155', marginBottom: 6 },
  input: {
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 12,
    fontSize: 15,
    color: '#0f172a',
    backgroundColor: '#f8fafc',
    marginBottom: 6,
  },
  currentValue: { fontSize: 12, color: '#94a3b8', marginBottom: 16 },
  saveBtn: {
    backgroundColor: '#2563eb',
    borderRadius: 8,
    paddingVertical: 13,
    alignItems: 'center',
    marginBottom: 16,
  },
  saveBtnDisabled: { backgroundColor: '#93c5fd' },
  saveBtnText: { color: '#fff', fontWeight: '600', fontSize: 15 },
  noteBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#fffbeb',
    borderRadius: 8,
    padding: 10,
    gap: 8,
  },
  noteText: { fontSize: 12, color: '#b45309', flex: 1, lineHeight: 17 },
});
