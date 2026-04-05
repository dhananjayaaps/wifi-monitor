import { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  ScrollView,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { devicesAPI } from '@/lib/api';

interface Device {
  id: number;
  mac_address: string;
  hostname: string;
  ip_address: string;
  is_active: boolean;
  manufacturer?: string;
  device_type?: string;
  last_seen: string;
  data_cap?: number | null;
}

interface Stats {
  bytes_uploaded: number;
  bytes_downloaded: number;
  timestamp: string;
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

const deviceTypeIcon: Record<string, string> = {
  smartphone: 'phone-portrait',
  laptop: 'laptop',
  tablet: 'tablet-portrait',
  smart_tv: 'tv',
  router: 'git-network',
  iot_device: 'cube',
};

function DeviceIcon({ type, active }: { type?: string; active?: boolean }) {
  const iconName = (type && deviceTypeIcon[type]) || 'hardware-chip';
  return (
    <Ionicons
      name={iconName as any}
      size={20}
      color={active ? '#2563eb' : '#94a3b8'}
    />
  );
}

const RANGES = [
  { label: '1h', hours: 1 },
  { label: '6h', hours: 6 },
  { label: '24h', hours: 24 },
  { label: '7d', hours: 168 },
  { label: '30d', hours: 720 },
];

export default function DevicesScreen() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [stats, setStats] = useState<Stats[]>([]);
  const [loading, setLoading] = useState(true);
  const [capInput, setCapInput] = useState('');
  const [isClearingStats, setIsClearingStats] = useState(false);
  const [isDeletingDevice, setIsDeletingDevice] = useState(false);
  const [rangeHours, setRangeHours] = useState(24);
  const [showDetail, setShowDetail] = useState(false);
  const isRefreshingDevices = useRef(false);
  const isRefreshingStats = useRef(false);

  const getBucketMinutes = (hours: number) => {
    if (hours <= 6) return 1;
    if (hours <= 24) return 5;
    if (hours <= 168) return 30;
    return 120;
  };

  const loadDevices = async () => {
    if (isRefreshingDevices.current) return;
    isRefreshingDevices.current = true;
    try {
      const response = await devicesAPI.list();
      const data = response.data.data || [];
      setDevices(data);
      if (data.length === 0) {
        setSelectedDevice(null);
        setCapInput('');
      } else if (!selectedDevice) {
        setSelectedDevice(data[0]);
        setCapInput(bytesToMBString(data[0].data_cap));
      } else {
        const updated = data.find((d: Device) => d.id === selectedDevice?.id);
        if (updated) {
          setSelectedDevice(updated);
          setCapInput(bytesToMBString(updated.data_cap));
        }
      }
    } catch (error) {
      console.error('Failed to load devices:', error);
    } finally {
      setLoading(false);
      isRefreshingDevices.current = false;
    }
  };

  const loadStats = async (deviceId: number, hours: number = rangeHours) => {
    if (isRefreshingStats.current) return;
    isRefreshingStats.current = true;
    try {
      const bucketMinutes = getBucketMinutes(hours);
      const response = await devicesAPI.getStats(deviceId, hours, bucketMinutes);
      setStats(response.data.data || []);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      isRefreshingStats.current = false;
    }
  };

  useEffect(() => {
    loadDevices();
    const id = setInterval(loadDevices, 30000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!selectedDevice) return;
    loadStats(selectedDevice.id, rangeHours);
    const refreshMs = rangeHours <= 6 ? 30000 : rangeHours <= 24 ? 60000 : 300000;
    const id = setInterval(() => loadStats(selectedDevice.id, rangeHours), refreshMs);
    return () => clearInterval(id);
  }, [selectedDevice?.id, rangeHours]);

  const handleDeviceSelect = (device: Device) => {
    setSelectedDevice(device);
    setCapInput(bytesToMBString(device.data_cap));
    setShowDetail(true);
  };

  const saveCap = async () => {
    if (!selectedDevice) return;
    const value = mbStringToBytes(capInput);
    if (value === undefined) {
      Alert.alert('Invalid input', 'Please enter a valid non-negative number of MB, or leave empty to clear.');
      return;
    }
    try {
      const resp = await devicesAPI.setCap(selectedDevice.id, value);
      const updated = resp.data.data as Device;
      setDevices((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      setSelectedDevice(updated);
      setCapInput(bytesToMBString(updated.data_cap));
    } catch {
      Alert.alert('Error', 'Failed to save data cap.');
    }
  };

  const clearStats = async () => {
    if (!selectedDevice || isClearingStats) return;
    Alert.alert(
      'Clear Usage Data',
      'Clear all usage data for this device? This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            setIsClearingStats(true);
            try {
              await devicesAPI.clearStats(selectedDevice.id);
              setStats([]);
            } catch {
              Alert.alert('Error', 'Failed to clear device usage data.');
            } finally {
              setIsClearingStats(false);
            }
          },
        },
      ]
    );
  };

  const deleteDevice = async () => {
    if (!selectedDevice || isDeletingDevice) return;
    Alert.alert(
      'Delete Device',
      'Delete this device and all of its data? This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            setIsDeletingDevice(true);
            try {
              await devicesAPI.delete(selectedDevice.id);
              const remaining = devices.filter((d) => d.id !== selectedDevice.id);
              setDevices(remaining);
              if (remaining.length > 0) {
                setSelectedDevice(remaining[0]);
                setCapInput(bytesToMBString(remaining[0].data_cap));
                loadStats(remaining[0].id);
              } else {
                setSelectedDevice(null);
                setCapInput('');
                setStats([]);
                setShowDetail(false);
              }
            } catch {
              Alert.alert('Error', 'Failed to delete device.');
            } finally {
              setIsDeletingDevice(false);
            }
          },
        },
      ]
    );
  };

  const totalBytes = stats.reduce((s, r) => s + (r.bytes_uploaded || 0) + (r.bytes_downloaded || 0), 0);
  const totalUpload = stats.reduce((s, r) => s + (r.bytes_uploaded || 0), 0);
  const totalDownload = stats.reduce((s, r) => s + (r.bytes_downloaded || 0), 0);
  const isOverCap = Boolean(selectedDevice?.data_cap && totalBytes >= selectedDevice.data_cap);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2563eb" />
      </View>
    );
  }

  if (showDetail && selectedDevice) {
    return (
      <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
        {/* Back button */}
        <TouchableOpacity style={styles.backBtn} onPress={() => setShowDetail(false)}>
          <Ionicons name="arrow-back" size={18} color="#2563eb" />
          <Text style={styles.backText}>All Devices</Text>
        </TouchableOpacity>

        {/* Device Header */}
        <View style={styles.card}>
          <View style={styles.deviceHeader}>
            <DeviceIcon type={selectedDevice.device_type} active={selectedDevice.is_active} />
            <Text style={styles.deviceTitle}>
              {selectedDevice.hostname || 'Device'}
            </Text>
            <View style={[styles.statusBadge, selectedDevice.is_active ? styles.statusActive : styles.statusInactive]}>
              <Text style={[styles.statusText, selectedDevice.is_active ? styles.statusTextActive : styles.statusTextInactive]}>
                {selectedDevice.is_active ? 'Active' : 'Offline'}
              </Text>
            </View>
          </View>

          {isOverCap && (
            <View style={styles.warningBox}>
              <Text style={styles.warningText}>
                Usage exceeded cap for this range. Total: {formatBytes(totalBytes)}
                {selectedDevice.data_cap ? ` (cap ${formatBytes(selectedDevice.data_cap)})` : ''}
              </Text>
            </View>
          )}

          <View style={styles.usageBox}>
            <Text style={styles.usageTitle}>Usage (selected range)</Text>
            <View style={styles.usageRow}>
              <Text style={styles.usageItem}>Total: {formatBytes(totalBytes)}</Text>
              <Text style={styles.usageItem}>↑ {formatBytes(totalUpload)}</Text>
              <Text style={styles.usageItem}>↓ {formatBytes(totalDownload)}</Text>
            </View>
          </View>

          <View style={styles.detailGrid}>
            <DetailItem label="IP Address" value={selectedDevice.ip_address} />
            <DetailItem label="MAC Address" value={selectedDevice.mac_address} mono />
            <DetailItem label="Type" value={selectedDevice.device_type || 'Unknown'} />
            <DetailItem label="Last Seen" value={new Date(selectedDevice.last_seen).toLocaleDateString()} />
          </View>

          {/* Data Cap */}
          <Text style={styles.fieldLabel}>Data Cap (MB)</Text>
          <View style={styles.capRow}>
            <TextInput
              style={[styles.input, { flex: 1 }]}
              value={capInput}
              onChangeText={setCapInput}
              keyboardType="decimal-pad"
              placeholder="e.g. 1024 for 1 GB"
              placeholderTextColor="#94a3b8"
            />
            <TouchableOpacity style={styles.saveBtn} onPress={saveCap}>
              <Text style={styles.saveBtnText}>Save</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.capHint}>
            Current: {selectedDevice.data_cap ? `${bytesToMBString(selectedDevice.data_cap)} MB` : 'No cap set'}
          </Text>

          <View style={styles.dangerRow}>
            <TouchableOpacity
              style={[styles.outlineBtn, styles.warnBtn]}
              onPress={clearStats}
              disabled={isClearingStats}
            >
              <Text style={styles.warnBtnText}>{isClearingStats ? 'Clearing...' : 'Clear Usage'}</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.outlineBtn, styles.dangerBtn]}
              onPress={deleteDevice}
              disabled={isDeletingDevice}
            >
              <Text style={styles.dangerBtnText}>{isDeletingDevice ? 'Deleting...' : 'Delete Device'}</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Usage Stats */}
        <View style={[styles.card, { marginTop: 12 }]}>
          <Text style={styles.cardTitle}>Usage Stats</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.rangeRow}>
              {RANGES.map(({ label, hours }) => (
                <TouchableOpacity
                  key={hours}
                  style={[styles.rangeBtn, rangeHours === hours && styles.rangeBtnActive]}
                  onPress={() => setRangeHours(hours)}
                >
                  <Text style={[styles.rangeBtnText, rangeHours === hours && styles.rangeBtnTextActive]}>
                    {label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>

          {stats.length > 0 ? (
            <>
              <View style={styles.statsHeader}>
                <Text style={[styles.statsCell, { flex: 2 }]}>Time</Text>
                <Text style={styles.statsCell}>Upload</Text>
                <Text style={styles.statsCell}>Download</Text>
              </View>
              {stats.slice(-30).map((stat, i) => (
                <View key={i} style={[styles.statsRow, i % 2 === 0 && styles.statsRowAlt]}>
                  <Text style={[styles.statsCell, { flex: 2, fontSize: 11 }]}>
                    {rangeHours > 24
                      ? new Date(stat.timestamp).toLocaleDateString()
                      : new Date(stat.timestamp).toLocaleTimeString()}
                  </Text>
                  <Text style={styles.statsCell}>{formatBytes(stat.bytes_uploaded)}</Text>
                  <Text style={styles.statsCell}>{formatBytes(stat.bytes_downloaded)}</Text>
                </View>
              ))}
            </>
          ) : (
            <Text style={styles.emptyText}>No usage data for this range</Text>
          )}
        </View>
      </ScrollView>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={devices}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
        refreshControl={
          <RefreshControl refreshing={false} onRefresh={loadDevices} />
        }
        ListEmptyComponent={
          <View style={styles.centered}>
            <Text style={styles.emptyText}>No devices found</Text>
          </View>
        }
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.deviceCard} onPress={() => handleDeviceSelect(item)} activeOpacity={0.7}>
            <View style={styles.deviceCardLeft}>
              <View style={styles.deviceIconWrap}>
                <DeviceIcon type={item.device_type} active={item.is_active} />
              </View>
              <View>
                <Text style={styles.deviceHostname}>{item.hostname || 'Unknown'}</Text>
                <Text style={styles.deviceIp}>{item.ip_address}</Text>
                <Text style={styles.deviceMac}>{item.mac_address}</Text>
              </View>
            </View>
            <View style={[styles.statusBadge, item.is_active ? styles.statusActive : styles.statusInactive]}>
              <Text style={[styles.statusText, item.is_active ? styles.statusTextActive : styles.statusTextInactive]}>
                {item.is_active ? 'Active' : 'Offline'}
              </Text>
            </View>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

function DetailItem({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <View style={styles.detailItem}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={[styles.detailValue, mono && { fontFamily: 'monospace', fontSize: 11 }]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f1f5f9' },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  backBtn: { flexDirection: 'row', alignItems: 'center', padding: 16, paddingBottom: 4 },
  backText: { color: '#2563eb', fontSize: 15, marginLeft: 6, fontWeight: '500' },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginTop: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  cardTitle: { fontSize: 17, fontWeight: '700', color: '#0f172a', marginBottom: 12 },
  deviceCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  deviceCardLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  deviceIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 8,
    backgroundColor: '#f1f5f9',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  deviceHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  deviceTitle: { fontSize: 18, fontWeight: '700', color: '#0f172a', flex: 1, marginLeft: 10 },
  deviceHostname: { fontSize: 14, fontWeight: '600', color: '#0f172a' },
  deviceIp: { fontSize: 12, color: '#64748b', marginTop: 2 },
  deviceMac: { fontSize: 11, color: '#94a3b8', fontFamily: 'monospace', marginTop: 1 },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20 },
  statusActive: { backgroundColor: '#dcfce7' },
  statusInactive: { backgroundColor: '#f1f5f9' },
  statusText: { fontSize: 12, fontWeight: '500' },
  statusTextActive: { color: '#15803d' },
  statusTextInactive: { color: '#64748b' },
  warningBox: {
    backgroundColor: '#fffbeb',
    borderWidth: 1,
    borderColor: '#fde68a',
    borderRadius: 8,
    padding: 10,
    marginBottom: 10,
  },
  warningText: { color: '#92400e', fontSize: 13 },
  usageBox: {
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    padding: 10,
    marginBottom: 12,
  },
  usageTitle: { fontSize: 12, color: '#64748b', marginBottom: 4 },
  usageRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  usageItem: { fontSize: 13, fontWeight: '500', color: '#0f172a' },
  detailGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginBottom: 12 },
  detailItem: { width: '48%', paddingVertical: 6 },
  detailLabel: { fontSize: 11, color: '#64748b' },
  detailValue: { fontSize: 13, fontWeight: '500', color: '#0f172a', marginTop: 2 },
  fieldLabel: { fontSize: 13, fontWeight: '500', color: '#334155', marginBottom: 6, marginTop: 4 },
  capRow: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  input: {
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
    color: '#0f172a',
    backgroundColor: '#f8fafc',
  },
  saveBtn: {
    backgroundColor: '#2563eb',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  saveBtnText: { color: '#fff', fontWeight: '600', fontSize: 14 },
  capHint: { fontSize: 11, color: '#94a3b8', marginTop: 4 },
  dangerRow: { flexDirection: 'row', gap: 10, marginTop: 16 },
  outlineBtn: { flex: 1, paddingVertical: 10, borderWidth: 1.5, borderRadius: 8, alignItems: 'center' },
  warnBtn: { borderColor: '#f59e0b' },
  warnBtnText: { color: '#b45309', fontWeight: '500', fontSize: 13 },
  dangerBtn: { borderColor: '#ef4444' },
  dangerBtnText: { color: '#dc2626', fontWeight: '500', fontSize: 13 },
  rangeRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  rangeBtn: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#cbd5e1',
    backgroundColor: '#fff',
  },
  rangeBtnActive: { backgroundColor: '#2563eb', borderColor: '#2563eb' },
  rangeBtnText: { fontSize: 13, color: '#475569' },
  rangeBtnTextActive: { color: '#fff', fontWeight: '600' },
  statsHeader: {
    flexDirection: 'row',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    marginBottom: 2,
  },
  statsRow: { flexDirection: 'row', paddingVertical: 5 },
  statsRowAlt: { backgroundColor: '#f8fafc' },
  statsCell: { flex: 1, fontSize: 12, color: '#334155', textAlign: 'right', paddingRight: 4 },
  emptyText: { fontSize: 14, color: '#94a3b8', textAlign: 'center', paddingVertical: 20 },
});
