import { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { agentsAPI } from '@/lib/api';

interface Agent {
  id: number;
  name: string;
  is_active: boolean;
  last_sync?: string;
  created_at: string;
}

export default function AgentsScreen() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [agentName, setAgentName] = useState('');
  const [registering, setRegistering] = useState(false);
  const [formError, setFormError] = useState('');

  const loadAgents = async () => {
    try {
      const response = await agentsAPI.list();
      setAgents(response.data.data || []);
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadAgents();
  };

  const handleRegister = async () => {
    setFormError('');
    if (!agentName.trim()) {
      setFormError('Please enter a name for the agent.');
      return;
    }
    setRegistering(true);
    try {
      await agentsAPI.register(agentName.trim());
      setAgentName('');
      setShowForm(false);
      loadAgents();
    } catch (error: any) {
      setFormError(error.response?.data?.message || 'Failed to register agent.');
    } finally {
      setRegistering(false);
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
    <View style={styles.container}>
      <FlatList
        data={agents}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListHeaderComponent={
          <>
            {/* Register button / form */}
            {showForm ? (
              <View style={styles.formCard}>
                <Text style={styles.formTitle}>Register New Agent</Text>
                {formError !== '' && (
                  <View style={styles.errorBox}>
                    <Text style={styles.errorText}>{formError}</Text>
                  </View>
                )}
                <Text style={styles.fieldLabel}>Agent Name</Text>
                <TextInput
                  style={styles.input}
                  value={agentName}
                  onChangeText={setAgentName}
                  placeholder="e.g. Living Room WiFi"
                  placeholderTextColor="#94a3b8"
                  autoFocus
                />
                <View style={styles.formBtns}>
                  <TouchableOpacity
                    style={[styles.primaryBtn, registering && styles.primaryBtnDisabled]}
                    onPress={handleRegister}
                    disabled={registering}
                  >
                    {registering ? (
                      <ActivityIndicator color="#fff" size="small" />
                    ) : (
                      <Text style={styles.primaryBtnText}>Register</Text>
                    )}
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.cancelBtn}
                    onPress={() => { setShowForm(false); setFormError(''); setAgentName(''); }}
                  >
                    <Text style={styles.cancelBtnText}>Cancel</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ) : (
              <TouchableOpacity style={styles.addBtn} onPress={() => setShowForm(true)} activeOpacity={0.8}>
                <Ionicons name="add" size={20} color="#fff" />
                <Text style={styles.addBtnText}>Register Agent</Text>
              </TouchableOpacity>
            )}
          </>
        }
        ListEmptyComponent={
          <View style={styles.emptyWrap}>
            <Ionicons name="server-outline" size={48} color="#cbd5e1" />
            <Text style={styles.emptyText}>No agents registered yet</Text>
          </View>
        }
        renderItem={({ item }) => (
          <View style={styles.agentCard}>
            <View style={styles.agentIconWrap}>
              <Ionicons name="server" size={24} color="#2563eb" />
            </View>
            <View style={styles.agentInfo}>
              <Text style={styles.agentName}>{item.name}</Text>
              <Text style={[styles.agentStatus, item.is_active ? styles.statusActive : styles.statusInactive]}>
                ● {item.is_active ? 'Active' : 'Inactive'}
              </Text>
              <Text style={styles.agentMeta}>
                Registered: {new Date(item.created_at).toLocaleDateString()}
              </Text>
              {item.last_sync && (
                <Text style={styles.agentMeta}>
                  Last Sync: {new Date(item.last_sync).toLocaleString()}
                </Text>
              )}
            </View>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f1f5f9' },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  addBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2563eb',
    borderRadius: 10,
    paddingVertical: 12,
    marginBottom: 16,
    gap: 8,
  },
  addBtnText: { color: '#fff', fontSize: 15, fontWeight: '600' },
  formCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  formTitle: { fontSize: 16, fontWeight: '700', color: '#0f172a', marginBottom: 12 },
  errorBox: {
    backgroundColor: '#fef2f2',
    borderWidth: 1,
    borderColor: '#fecaca',
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
  },
  errorText: { color: '#b91c1c', fontSize: 13 },
  fieldLabel: { fontSize: 13, fontWeight: '500', color: '#334155', marginBottom: 6 },
  input: {
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
    color: '#0f172a',
    backgroundColor: '#f8fafc',
    marginBottom: 12,
  },
  formBtns: { flexDirection: 'row', gap: 10 },
  primaryBtn: {
    flex: 1,
    backgroundColor: '#2563eb',
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
  },
  primaryBtnDisabled: { backgroundColor: '#93c5fd' },
  primaryBtnText: { color: '#fff', fontWeight: '600', fontSize: 14 },
  cancelBtn: {
    flex: 1,
    backgroundColor: '#e2e8f0',
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
  },
  cancelBtnText: { color: '#0f172a', fontWeight: '500', fontSize: 14 },
  agentCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'flex-start',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  agentIconWrap: {
    width: 48,
    height: 48,
    borderRadius: 10,
    backgroundColor: '#eff6ff',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  agentInfo: { flex: 1 },
  agentName: { fontSize: 15, fontWeight: '600', color: '#0f172a' },
  agentStatus: { fontSize: 13, fontWeight: '500', marginTop: 3 },
  statusActive: { color: '#16a34a' },
  statusInactive: { color: '#94a3b8' },
  agentMeta: { fontSize: 12, color: '#64748b', marginTop: 3 },
  emptyWrap: { paddingVertical: 60, alignItems: 'center', gap: 12 },
  emptyText: { fontSize: 14, color: '#94a3b8' },
});
