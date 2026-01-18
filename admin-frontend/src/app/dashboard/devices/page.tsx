'use client';

import { useState, useEffect } from 'react';
import { devicesAPI } from '@/lib/api';
import {
  BarChart,
  Bar,
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
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [stats, setStats] = useState<Stats[]>([]);
  const [loading, setLoading] = useState(true);
  const [capInput, setCapInput] = useState<string>("");

  useEffect(() => {
    const loadDevices = async () => {
      try {
        const response = await devicesAPI.list();
        const data = response.data.data || [];
        setDevices(data);
        if (data.length > 0) {
          setSelectedDevice(data[0]);
          setCapInput(data[0].data_cap ? String(data[0].data_cap) : "");
          loadStats(data[0].id);
        }
      } catch (error) {
        console.error('Failed to load devices:', error);
      } finally {
        setLoading(false);
      }
    };

    loadDevices();
  }, []);

  const loadStats = async (deviceId: number) => {
    try {
      const response = await devicesAPI.getStats(deviceId);
      setStats(response.data.data || []);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleDeviceSelect = (device: Device) => {
    setSelectedDevice(device);
    setCapInput(device.data_cap ? String(device.data_cap) : "");
    loadStats(device.id);
  };

  const saveCap = async () => {
    if (!selectedDevice) return;
    let value: number | null = null;
    const trimmed = capInput.trim();
    if (trimmed.length > 0) {
      const parsed = Number(trimmed);
      if (!Number.isFinite(parsed) || parsed < 0) {
        alert('Please enter a valid non-negative number of bytes, or leave empty to clear.');
        return;
      }
      value = parsed;
    }
    try {
      const resp = await devicesAPI.setCap(selectedDevice.id, value);
      const updated = resp.data.data as Device;
      // Update local state for devices and selected device
      setDevices((prev) => prev.map((d) => d.id === updated.id ? updated : d));
      setSelectedDevice(updated);
      setCapInput(updated.data_cap ? String(updated.data_cap) : "");
    } catch (e) {
      console.error('Failed to save cap', e);
      alert('Failed to save data cap.');
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
                    <p className="text-sm text-slate-600">Data Cap (bytes)</p>
                    <div className="flex items-center gap-2 mt-1">
                      <input
                        type="text"
                        value={capInput}
                        onChange={(e) => setCapInput(e.target.value)}
                        className="border rounded px-3 py-2 w-full max-w-md"
                        placeholder="e.g. 1073741824 for 1 GB, empty to clear"
                      />
                      <button
                        onClick={saveCap}
                        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                      >
                        Save Cap
                      </button>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      Current: {selectedDevice.data_cap ? `${selectedDevice.data_cap} bytes` : 'No cap set'}
                    </p>
                  </div>
                </div>
              </div>

              {/* -------- Usage Chart -------- */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-xl font-bold text-slate-900 mb-4">
                  Usage Stats
                </h3>

                {stats.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={stats.slice(-10)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="timestamp"
                        tick={{ fontSize: 12 }}
                        tickFormatter={(time) =>
                          new Date(time).toLocaleTimeString()
                        }
                      />
                      <YAxis />
                      <Tooltip
                        formatter={(value: any) =>
                          `${(value / 1024 / 1024).toFixed(2)} MB`
                        }
                      />
                      <Legend />
                      <Bar
                        dataKey="bytes_uploaded"
                        name="Upload"
                        fill="#3b82f6"
                      />
                      <Bar
                        dataKey="bytes_downloaded"
                        name="Download"
                        fill="#10b981"
                      />
                    </BarChart>
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
