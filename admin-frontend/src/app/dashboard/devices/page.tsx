'use client';

import { useState, useEffect } from 'react';
import { Navbar } from '@/components/Navbar';
import { devicesAPI } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface Device {
  id: number;
  mac_address: string;
  hostname: string;
  ip_address: string;
  is_active: boolean;
  manufacturer?: string;
  device_type?: string;
  last_seen: string;
}

interface Stats {
  bytes_uploaded: number;
  bytes_downloaded: number;
  timestamp: string;
}

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [stats, setStats] = useState<Stats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDevices = async () => {
      try {
        const response = await devicesAPI.list();
        setDevices(response.data.data || []);
        if (response.data.data && response.data.data.length > 0) {
          setSelectedDevice(response.data.data[0]);
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
    loadStats(device.id);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-slate-900 mb-8">Devices</h1>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Devices List */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-slate-900 mb-4">All Devices</h2>
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
                    <p className="font-medium text-slate-900">{device.hostname || 'Unknown'}</p>
                    <p className="text-xs text-slate-600">{device.ip_address}</p>
                    <span
                      className={`text-xs font-medium ${
                        device.is_active ? 'text-green-600' : 'text-slate-400'
                      }`}
                    >
                      {device.is_active ? '● Active' : '● Offline'}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Device Details */}
          <div className="lg:col-span-3">
            {selectedDevice ? (
              <>
                <div className="bg-white rounded-lg shadow p-6 mb-6">
                  <h2 className="text-2xl font-bold text-slate-900 mb-4">
                    {selectedDevice.hostname || 'Device'}
                  </h2>

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <DetailItem label="IP Address" value={selectedDevice.ip_address} />
                    <DetailItem label="MAC Address" value={selectedDevice.mac_address} />
                    <DetailItem label="Type" value={selectedDevice.device_type || 'Unknown'} />
                    <DetailItem label="Manufacturer" value={selectedDevice.manufacturer || 'Unknown'} />
                    <DetailItem
                      label="Status"
                      value={selectedDevice.is_active ? 'Active' : 'Inactive'}
                    />
                    <DetailItem label="Last Seen" value={new Date(selectedDevice.last_seen).toLocaleDateString()} />
                  </div>
                </div>

                {/* Usage Stats Chart */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-xl font-bold text-slate-900 mb-4">Usage Stats</h3>
                  {stats.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={stats.slice(-10)}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="timestamp"
                          tick={{ fontSize: 12 }}
                          tickFormatter={(time) => new Date(time).toLocaleTimeString()}
                        />
                        <YAxis />
                        <Tooltip
                          formatter={(value: any) => `${(value / 1024 / 1024).toFixed(2)} MB`}
                        />
                        <Legend />
                        <Bar dataKey="bytes_uploaded" fill="#3b82f6" name="Upload (bytes)" />
                        <Bar dataKey="bytes_downloaded" fill="#10b981" name="Download (bytes)" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-slate-600">No usage data available</p>
                  )}
                </div>
              </>
            ) : (
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-slate-600">Select a device to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-slate-600">{label}</p>
      <p className="font-medium text-slate-900">{value}</p>
    </div>
  );
}
