import { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { devicesAPI, alertsAPI, agentsAPI } from '@/lib/api';

interface Device {
  id: number;
  mac_address: string;
  hostname: string;
  ip_address: string;
  is_active: boolean;
  device_type?: string;
}

interface AlertHistoryItem {
  id: number;
  alert_id: number;
  device_id: number | null;
  value_at_trigger: number;
  triggered_at: string;
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

function StatCard({
  icon,
  iconBg,
  label,
  value,
}: {
  icon: React.ReactNode;
  iconBg: string;
  label: string;
  value: number;
}) {
  return (
    <View style={styles.statCard}>
      <View style={[styles.statIconWrap, { backgroundColor: iconBg }]}>{icon}</View>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

export default function DashboardScreen() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [alerts, setAlerts] = useState<AlertHistoryItem[]>([]);
  const [agentCount, setAgentCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const [devicesRes, alertsRes, agentsRes] = await Promise.all([
        devicesAPI.list(),
        alertsAPI.history({ hours: 24 }),
        agentsAPI.list(),
      ]);
      setDevices(devicesRes.data.data || []);
      setAlerts(alertsRes.data.data || []);
      setAgentCount(agentsRes.data.data?.length || 0);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const activeDevices = devices.filter((d) => d.is_active).length;

  const deviceName = (device_id: number | null) => {
    if (!device_id) return 'Unknown device';
    const device = devices.find((d) => d.id === device_id);
    return device?.hostname || device?.mac_address || `Device ${device_id}`;
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2563eb" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* Stat Cards */}
      <View style={styles.statsGrid}>
        <StatCard
          icon={<Ionicons name="wifi" size={22} color="#2563eb" />}
          iconBg="#dbeafe"
          label="Connected"
          value={activeDevices}
        />
        <StatCard
          icon={<Ionicons name="phone-portrait" size={22} color="#16a34a" />}
          iconBg="#dcfce7"
          label="Total Devices"
          value={devices.length}
        />
        <StatCard
          icon={<Ionicons name="flash" size={22} color="#9333ea" />}
          iconBg="#f3e8ff"
          label="Agents"
          value={agentCount}
        />
        <StatCard
          icon={<Ionicons name="warning" size={22} color="#ea580c" />}
          iconBg="#ffedd5"
          label="Alerts (24h)"
          value={alerts.length}
        />
      </View>

      {/* Devices Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Devices</Text>
        {devices.length > 0 ? (
          devices.slice(0, 8).map((device) => (
            <View key={device.id} style={styles.deviceRow}>
              <View style={styles.deviceInfo}>
                <Text style={styles.deviceHostname}>
                  {device.hostname || 'Unknown'}
                </Text>
                <Text style={styles.deviceIp}>{device.ip_address}</Text>
                <Text style={styles.deviceMac}>{device.mac_address}</Text>
              </View>
              <View
                style={[
                  styles.statusBadge,
                  device.is_active ? styles.statusActive : styles.statusInactive,
                ]}
              >
                <Text
                  style={[
                    styles.statusText,
                    device.is_active ? styles.statusTextActive : styles.statusTextInactive,
                  ]}
                >
                  {device.is_active ? 'Active' : 'Offline'}
                </Text>
              </View>
            </View>
          ))
        ) : (
          <Text style={styles.emptyText}>No devices found</Text>
        )}
      </View>

      {/* Alerts Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Alerts</Text>
        {alerts.length > 0 ? (
          alerts.slice(0, 5).map((alert) => (
            <View key={alert.id} style={styles.alertRow}>
              <Ionicons name="warning" size={16} color="#dc2626" style={{ marginTop: 2 }} />
              <View style={{ flex: 1, marginLeft: 10 }}>
                <Text style={styles.alertTitle}>Data usage alert</Text>
                <Text style={styles.alertDevice}>Device: {deviceName(alert.device_id)}</Text>
                <Text style={styles.alertMeta}>
                  {formatBytes(alert.value_at_trigger)} · {new Date(alert.triggered_at).toLocaleString()}
                </Text>
              </View>
            </View>
          ))
        ) : (
          <Text style={styles.emptyText}>No alerts in the last 24 hours</Text>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f1f5f9' },
  content: { padding: 16, paddingBottom: 32 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  statCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    flex: 1,
    minWidth: '45%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  statIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  statValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#0f172a',
  },
  statLabel: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
    textAlign: 'center',
  },
  section: {
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
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0f172a',
    marginBottom: 12,
  },
  deviceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  deviceInfo: { flex: 1 },
  deviceHostname: { fontSize: 14, fontWeight: '600', color: '#0f172a' },
  deviceIp: { fontSize: 12, color: '#64748b', marginTop: 2 },
  deviceMac: { fontSize: 11, color: '#94a3b8', fontFamily: 'monospace', marginTop: 1 },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
    marginLeft: 8,
  },
  statusActive: { backgroundColor: '#dcfce7' },
  statusInactive: { backgroundColor: '#f1f5f9' },
  statusText: { fontSize: 12, fontWeight: '500' },
  statusTextActive: { color: '#15803d' },
  statusTextInactive: { color: '#64748b' },
  alertRow: {
    flexDirection: 'row',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  alertTitle: { fontSize: 14, fontWeight: '600', color: '#0f172a' },
  alertDevice: { fontSize: 12, color: '#64748b', marginTop: 2 },
  alertMeta: { fontSize: 11, color: '#94a3b8', marginTop: 4 },
  emptyText: { fontSize: 14, color: '#94a3b8', textAlign: 'center', paddingVertical: 16 },
});
