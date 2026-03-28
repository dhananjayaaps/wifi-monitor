'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { devicesAPI } from '@/lib/api';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

import {
  Smartphone,
  Laptop,
  Tablet,
  Tv,
  Router,
  Cpu,
} from 'lucide-react';

/* ---------------- Types ---------------- */

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

const mbStringToBytes = (value: string) => {
  const trimmed = value.trim();
  if (!trimmed.length) return null;
  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed) || parsed < 0) return undefined;
  return Math.round(parsed * 1024 * 1024);
};

/* ---------------- Device Icon Mapping ---------------- */

const deviceTypeIconMap: Record<
  string,
  React.ComponentType<{ className?: string }>
> = {
  smartphone: Smartphone,
  laptop: Laptop,
  tablet: Tablet,
  smart_tv: Tv,
  router: Router,
  iot_device: Cpu,
};

function DeviceIcon({
  type,
  active,
}: {
  type?: string;
  active?: boolean;
}) {
  if (!type) return null;

  const Icon = deviceTypeIconMap[type];
  if (!Icon) return null;

  return (
    <Icon
      className={`w-6 h-6 ${
        active ? 'text-green-600' : 'text-slate-500'
      }`}
    />
  );
}

/* ---------------- Main Component ---------------- */

export default function DevicesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [stats, setStats] = useState<Stats[]>([]);
  const [loading, setLoading] = useState(true);
  const [capInput, setCapInput] = useState<string>("");
  const [isClearingStats, setIsClearingStats] = useState(false);
  const [isDeletingDevice, setIsDeletingDevice] = useState(false);
  const [rangeHours, setRangeHours] = useState(24);
  const isRefreshingDevices = useRef(false);
  const isRefreshingStats = useRef(false);

  const devicesRefreshMs = 30000;

  const getBucketMinutes = (hours: number) => {
    if (hours <= 6) return 1;
    if (hours <= 24) return 5;
    if (hours <= 168) return 30;
    return 120;
  };

  const getStatsRefreshMs = (hours: number) => {
    if (hours <= 6) return 30000;
    if (hours <= 24) return 60000;
    if (hours <= 168) return 300000;
    return 600000;
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
        setCapInput("");
        setStats([]);
        return;
      }

      const urlDeviceId = Number(searchParams.get('deviceId'));
      const desiredId = Number.isFinite(urlDeviceId) && urlDeviceId > 0
        ? urlDeviceId
        : selectedDevice?.id;

      if (desiredId) {
        const updated = data.find((d: Device) => d.id === desiredId);
        if (updated) {
          setSelectedDevice(updated);
          setCapInput(bytesToMBString(updated.data_cap));
          return;
        }
      }

      setSelectedDevice(data[0]);
      setCapInput(bytesToMBString(data[0].data_cap));
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
    const intervalId = window.setInterval(loadDevices, devicesRefreshMs);
    return () => window.clearInterval(intervalId);
  }, [searchParams]);

  useEffect(() => {
    if (!selectedDevice) return;
    loadStats(selectedDevice.id, rangeHours);
    const refreshMs = getStatsRefreshMs(rangeHours);
    const intervalId = window.setInterval(() => {
      loadStats(selectedDevice.id, rangeHours);
    }, refreshMs);
    return () => window.clearInterval(intervalId);
  }, [selectedDevice?.id, rangeHours]);

  const handleDeviceSelect = (device: Device) => {
    setSelectedDevice(device);
    setCapInput(bytesToMBString(device.data_cap));
    const nextParams = new URLSearchParams(searchParams.toString());
    nextParams.set('deviceId', String(device.id));
    router.replace(`?${nextParams.toString()}`);
  };

  const handleRangeChange = (hours: number) => {
    setRangeHours(hours);
  };

  const latestUsage = stats.length > 0 ? stats[stats.length - 1] : null;
  const latestTotalBytes = latestUsage
    ? (latestUsage.bytes_uploaded || 0) + (latestUsage.bytes_downloaded || 0)
    : 0;
  const isOverCap = Boolean(
    selectedDevice?.data_cap && latestTotalBytes >= selectedDevice.data_cap
  );
  const totalRangeBytes = stats.reduce(
    (sum, stat) => sum + (stat.bytes_uploaded || 0) + (stat.bytes_downloaded || 0),
    0
  );
  const totalRangeUpload = stats.reduce(
    (sum, stat) => sum + (stat.bytes_uploaded || 0),
    0
  );
  const totalRangeDownload = stats.reduce(
    (sum, stat) => sum + (stat.bytes_downloaded || 0),
    0
  );

  const saveCap = async () => {
    if (!selectedDevice) return;
    const value = mbStringToBytes(capInput);
    if (value === undefined) {
      alert('Please enter a valid non-negative number of MB, or leave empty to clear.');
      return;
    }
    try {
      const resp = await devicesAPI.setCap(selectedDevice.id, value);
      const updated = resp.data.data as Device;
      // Update local state for devices and selected device
      setDevices((prev) => prev.map((d) => d.id === updated.id ? updated : d));
      setSelectedDevice(updated);
      setCapInput(bytesToMBString(updated.data_cap));
    } catch (e) {
      console.error('Failed to save cap', e);
      alert('Failed to save data cap.');
    }
  };

  const clearStats = async () => {
    if (!selectedDevice || isClearingStats) return;
    const confirmClear = window.confirm(
      'Clear all usage data for this device? This cannot be undone.'
    );
    if (!confirmClear) return;

    setIsClearingStats(true);
    try {
      await devicesAPI.clearStats(selectedDevice.id);
      setStats([]);
    } catch (e) {
      console.error('Failed to clear stats', e);
      alert('Failed to clear device usage data.');
    } finally {
      setIsClearingStats(false);
    }
  };

  const deleteDevice = async () => {
    if (!selectedDevice || isDeletingDevice) return;
    const confirmDelete = window.confirm(
      'Delete this device and all of its data? This cannot be undone.'
    );
    if (!confirmDelete) return;

    setIsDeletingDevice(true);
    try {
      await devicesAPI.delete(selectedDevice.id);
      setDevices((prev) => prev.filter((d) => d.id !== selectedDevice.id));

      const remaining = devices.filter((d) => d.id !== selectedDevice.id);
      if (remaining.length > 0) {
        setSelectedDevice(remaining[0]);
        setCapInput(remaining[0].data_cap ? String(remaining[0].data_cap) : "");
        loadStats(remaining[0].id);
      } else {
        setSelectedDevice(null);
        setCapInput("");
        setStats([]);
      }
    } catch (e) {
      console.error('Failed to delete device', e);
      alert('Failed to delete device.');
    } finally {
      setIsDeletingDevice(false);
    }
  };

  return (
    <div className="px-8 py-8">
      <h1 className="text-4xl font-bold text-slate-900 mb-8">Devices</h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* -------- Devices List -------- */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-slate-900 mb-4">
            All Devices
          </h2>

          {loading ? (
            <p className="text-slate-600">Loading...</p>
          ) : (
            <div className="space-y-2">
              {devices.map((device) => (
                <button
                  key={device.id}
                  onClick={() => handleDeviceSelect(device)}
                  className={`w-full text-left p-3 rounded-lg transition ${
                    selectedDevice?.id === device.id
                      ? 'bg-blue-100 border-l-4 border-blue-600'
                      : 'bg-slate-50 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <DeviceIcon
                      type={device.device_type}
                      active={device.is_active}
                    />

                    <div>
                      <p className="font-medium text-slate-900">
                        {device.hostname || 'Unknown'}
                      </p>
                      <p className="text-xs text-slate-600">
                        {device.ip_address}
                      </p>
                    </div>
                  </div>

                  <p
                    className={`mt-1 text-xs font-medium ${
                      device.is_active
                        ? 'text-green-600'
                        : 'text-slate-400'
                    }`}
                  >
                    ● {device.is_active ? 'Active' : 'Offline'}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* -------- Device Details -------- */}
        <div className="lg:col-span-3">
          {selectedDevice ? (
            <>
              <div className="bg-white rounded-lg shadow p-6 mb-6">
                <div className="flex items-center gap-3 mb-4">
                  <DeviceIcon
                    type={selectedDevice.device_type}
                    active={selectedDevice.is_active}
                  />
                  <h2 className="text-2xl font-bold text-slate-900">
                    {selectedDevice.hostname || 'Device'}
                  </h2>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {isOverCap && (
                    <div className="col-span-2 md:col-span-3 rounded border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900">
                      Usage exceeded the device cap. Latest interval: {formatBytes(latestTotalBytes)}
                      {selectedDevice?.data_cap ? ` (cap ${formatBytes(selectedDevice.data_cap)})` : ''}.
                    </div>
                  )}
                  <div className="col-span-2 md:col-span-3 rounded border border-slate-200 bg-slate-50 px-4 py-3">
                    <p className="text-sm text-slate-600">Total Usage (selected range)</p>
                    <div className="mt-1 flex flex-wrap gap-4">
                      <span className="text-sm font-medium text-slate-900">
                        Total: {formatBytes(totalRangeBytes)}
                      </span>
                      <span className="text-sm text-slate-700">
                        Upload: {formatBytes(totalRangeUpload)}
                      </span>
                      <span className="text-sm text-slate-700">
                        Download: {formatBytes(totalRangeDownload)}
                      </span>
                    </div>
                  </div>
                  <DetailItem
                    label="IP Address"
                    value={selectedDevice.ip_address}
                  />
                  <DetailItem
                    label="MAC Address"
                    value={selectedDevice.mac_address}
                  />
                  <DetailItem
                    label="Type"
                    value={selectedDevice.device_type || 'Unknown'}
                  />
                  <DetailItem
                    label="Status"
                    value={
                      selectedDevice.is_active
                        ? 'Active'
                        : 'Inactive'
                    }
                  />
                  <DetailItem
                    label="Last Seen"
                    value={new Date(
                      selectedDevice.last_seen
                    ).toLocaleDateString()}
                  />
                  <div className="col-span-2">
                    <p className="text-sm text-slate-600">Data Cap (MB)</p>
                    <div className="flex items-center gap-2 mt-1">
                      <input
                        type="text"
                        value={capInput}
                        onChange={(e) => setCapInput(e.target.value)}
                        className="border rounded px-3 py-2 w-full max-w-md"
                        placeholder="e.g. 1024 for 1 GB, empty to clear"
                      />
                      <button
                        onClick={saveCap}
                        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                      >
                        Save Cap
                      </button>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      Current: {selectedDevice.data_cap ? `${bytesToMBString(selectedDevice.data_cap)} MB` : 'No cap set'}
                    </p>
                    <div className="flex flex-wrap gap-3 mt-4">
                      <button
                        onClick={clearStats}
                        disabled={isClearingStats}
                        className="border border-amber-500 text-amber-700 px-4 py-2 rounded hover:bg-amber-50 disabled:opacity-60"
                      >
                        {isClearingStats ? 'Clearing...' : 'Clear Usage Data'}
                      </button>
                      <button
                        onClick={deleteDevice}
                        disabled={isDeletingDevice}
                        className="border border-red-500 text-red-700 px-4 py-2 rounded hover:bg-red-50 disabled:opacity-60"
                      >
                        {isDeletingDevice ? 'Deleting...' : 'Delete Device'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* -------- Usage Chart -------- */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-xl font-bold text-slate-900 mb-4">
                  Usage Stats
                </h3>

                <div className="flex flex-wrap gap-2 mb-4">
                  {[1, 6, 24, 168, 720].map((hours) => (
                    <button
                      key={hours}
                      onClick={() => handleRangeChange(hours)}
                      className={`px-3 py-1 rounded text-sm border transition ${
                        rangeHours === hours
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      {hours >= 24 ? `${hours / 24}d` : `${hours}h`}
                    </button>
                  ))}
                </div>

                {stats.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={stats}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="timestamp"
                        tick={{ fontSize: 12 }}
                        tickFormatter={(time) => {
                          const date = new Date(time);
                          return rangeHours > 24
                            ? date.toLocaleDateString()
                            : date.toLocaleTimeString();
                        }}
                      />
                      <YAxis
                        width={84}
                        tickMargin={8}
                        tickFormatter={(value) => formatBytes(value)}
                      />
                      <Tooltip
                        formatter={(value: any) => formatBytes(Number(value))}
                      />
                      <Legend wrapperStyle={{ paddingLeft: 8 }} />
                      <Line
                        type="monotone"
                        dataKey="bytes_uploaded"
                        name="Upload"
                        stroke="#3b82f6"
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="bytes_downloaded"
                        name="Download"
                        stroke="#10b981"
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-slate-600">
                    No usage data available
                  </p>
                )}
              </div>
            </>
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-slate-600">
                Select a device to view details
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ---------------- Helpers ---------------- */

function DetailItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <p className="text-sm text-slate-600">{label}</p>
      <p className="font-medium text-slate-900">{value}</p>
    </div>
  );
}
