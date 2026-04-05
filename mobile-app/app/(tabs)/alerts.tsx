import { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { alertsAPI } from '@/lib/api';

interface AlertHistoryItem {
  id: number;
  alert_id: number;
  device_id: number | null;
  value_at_trigger: number;
  triggered_at: string;
  resolved_at?: string | null;
  alert_type?: string;
  threshold_value?: number;
  device_mac?: string | null;
  device_hostname?: string | null;
}

const formatBytes = (bytes: number) => {
  if (!Number.isFinite(bytes)) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let value = Math.max(0, bytes);
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(value < 10 && unitIndex > 0 ? 2 : 1)} ${units[unitIndex]}`;
};

const RANGES = [
  { label: '24h', value: 24 },
  { label: '3d', value: 72 },
  { label: '7d', value: 168 },
  { label: '30d', value: 720 },
  { label: 'All', value: undefined },
];

const pageSize = 25;
const refreshMs = 30000;

export default function AlertsScreen() {
  const [history, setHistory] = useState<AlertHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [hours, setHours] = useState<number | undefined>(24);

  const loadHistory = async () => {
    try {
      const resp = await alertsAPI.history({ hours, limit: pageSize, offset: 0 });
      const items = resp.data.data || [];
      setHistory(items);
      setHasMore(items.length === pageSize);
    } catch (error) {
      console.error('Failed to load alert history:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    setHistory([]);
    setHasMore(true);
    loadHistory();
    const id = setInterval(loadHistory, refreshMs);
    return () => clearInterval(id);
  }, [hours]);

  const clearHistory = () => {
    Alert.alert(
      'Clear Alert History',
      'Clear all alert history? This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            if (clearing) return;
            setClearing(true);
            try {
              await alertsAPI.clearHistory();
              setHistory([]);
              setHasMore(false);
            } catch (error) {
              console.error('Failed to clear alerts:', error);
            } finally {
              setClearing(false);
            }
          },
        },
      ]
    );
  };

  const loadMore = async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const resp = await alertsAPI.history({
        hours,
        limit: pageSize,
        offset: history.length,
      });
      const items = resp.data.data || [];
      setHistory((prev) => [...prev, ...items]);
      setHasMore(items.length === pageSize);
    } catch (error) {
      console.error('Failed to load more alerts:', error);
    } finally {
      setLoadingMore(false);
    }
  };

  const deviceName = (item: AlertHistoryItem) => {
    if (item.device_hostname) return item.device_hostname;
    if (item.device_mac) return item.device_mac;
    if (item.device_id) return `Device ${item.device_id}`;
    return 'Unknown device';
  };

  const alertTitle = (item: AlertHistoryItem) => {
    const type = (item.alert_type || '').toLowerCase();
    if (type === 'ddos_detected') return 'DDoS Detected';
    if (type === 'dos_detected') return 'DoS Detected';
    if (type === 'data_cap') return 'Data Cap Exceeded';
    return 'Data Usage Alert';
  };

  const showThreshold = (item: AlertHistoryItem) => {
    const type = (item.alert_type || '').toLowerCase();
    return type !== 'ddos_detected' && type !== 'dos_detected';
  };

  const alertBorderColor = (item: AlertHistoryItem) => {
    const type = (item.alert_type || '').toLowerCase();
    if (type === 'ddos_detected' || type === 'dos_detected') return '#dc2626';
    return '#f97316';
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
      {/* Range filter + clear */}
      <View style={styles.toolbar}>
        <FlatList
          horizontal
          data={RANGES}
          keyExtractor={(item) => String(item.value ?? 'all')}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ gap: 8, paddingVertical: 4 }}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[styles.rangeBtn, hours === item.value && styles.rangeBtnActive]}
              onPress={() => setHours(item.value)}
            >
              <Text style={[styles.rangeBtnText, hours === item.value && styles.rangeBtnTextActive]}>
                {item.label}
              </Text>
            </TouchableOpacity>
          )}
        />
        <TouchableOpacity style={styles.clearBtn} onPress={clearHistory} disabled={clearing}>
          <Text style={styles.clearBtnText}>{clearing ? 'Clearing...' : 'Clear'}</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={history}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
        ListEmptyComponent={
          <View style={styles.emptyWrap}>
            <Text style={styles.emptyText}>No alerts for this period</Text>
          </View>
        }
        onEndReached={hasMore ? loadMore : undefined}
        onEndReachedThreshold={0.3}
        ListFooterComponent={
          loadingMore ? <ActivityIndicator size="small" color="#2563eb" style={{ marginTop: 12 }} /> : null
        }
        renderItem={({ item }) => (
          <View style={[styles.alertCard, { borderLeftColor: alertBorderColor(item) }]}>
            <View style={styles.alertHeader}>
              <Ionicons name="warning" size={18} color={alertBorderColor(item)} />
              <Text style={styles.alertTitle}>{alertTitle(item)}</Text>
            </View>
            <Text style={styles.alertDevice}>Device: {deviceName(item)}</Text>
            {showThreshold(item) && item.threshold_value != null && (
              <Text style={styles.alertMeta}>Threshold: {formatBytes(item.threshold_value)}</Text>
            )}
            <View style={styles.alertFooter}>
              <Text style={styles.alertMeta}>
                {item.alert_type === 'ddos_detected' || item.alert_type === 'dos_detected'
                  ? 'Traffic at trigger: '
                  : 'Value at trigger: '}
                {formatBytes(item.value_at_trigger)}
              </Text>
              <Text style={styles.alertMeta}>
                {new Date(item.triggered_at).toLocaleString()}
              </Text>
            </View>
            {item.resolved_at && (
              <Text style={styles.resolvedText}>
                Resolved: {new Date(item.resolved_at).toLocaleString()}
              </Text>
            )}
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f1f5f9' },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  toolbar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    gap: 8,
  },
  rangeBtn: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#cbd5e1',
    backgroundColor: '#fff',
  },
  rangeBtnActive: { backgroundColor: '#2563eb', borderColor: '#2563eb' },
  rangeBtnText: { fontSize: 13, color: '#475569' },
  rangeBtnTextActive: { color: '#fff', fontWeight: '600' },
  clearBtn: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#cbd5e1',
    backgroundColor: '#fff',
    marginLeft: 'auto',
  },
  clearBtnText: { fontSize: 13, color: '#dc2626' },
  alertCard: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  alertHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 },
  alertTitle: { fontSize: 15, fontWeight: '600', color: '#0f172a' },
  alertDevice: { fontSize: 13, color: '#475569', marginBottom: 4 },
  alertFooter: { flexDirection: 'row', justifyContent: 'space-between', flexWrap: 'wrap', marginTop: 4 },
  alertMeta: { fontSize: 12, color: '#64748b' },
  resolvedText: { fontSize: 12, color: '#16a34a', marginTop: 4 },
  emptyWrap: { paddingVertical: 60, alignItems: 'center' },
  emptyText: { fontSize: 14, color: '#94a3b8' },
});
