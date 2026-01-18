'use client';

import { useState, useEffect } from 'react';
import { devicesAPI, alertsAPI, agentsAPI } from '@/lib/api';
import { Wifi, AlertTriangle, Zap, Activity, Smartphone, Laptop, Tablet, Tv, Router, Cpu } from 'lucide-react';

interface Device {
  id: number;
  mac_address: string;
  hostname: string;
  ip_address: string;
  is_active: boolean;
  manufacturer?: string;
  device_type?: string;
}

interface Alert {
  id: number;
  title: string;
  threshold: number;
  status: string;
}

const deviceTypeIconMap: Record<string, React.ComponentType<{ className?: string; size?: number }>> = {
  smartphone: Smartphone,
  laptop: Laptop,
  tablet: Tablet,
  smart_tv: Tv,
  router: Router,
  iot_device: Cpu,
};

function DeviceIcon({ type, active }: { type?: string; active?: boolean }) {
  if (!type) return <Cpu className={`${active ? 'text-slate-600' : 'text-slate-400'}`} size={20} />;
  
  const Icon = deviceTypeIconMap[type];
  if (!Icon) return <Cpu className={`${active ? 'text-slate-600' : 'text-slate-400'}`} size={20} />;
  
  return <Icon className={`${active ? 'text-blue-600' : 'text-slate-400'}`} size={20} />;
}

export default function DashboardPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [agentCount, setAgentCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [devicesRes, alertsRes, agentsRes] = await Promise.all([
          devicesAPI.list(),
          alertsAPI.list(),
          agentsAPI.list(),
        ]);

        setDevices(devicesRes.data.data || []);
        setAlerts(alertsRes.data.data || []);
        setAgentCount(agentsRes.data.data?.length || 0);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const activeDevices = devices.filter((d) => d.is_active).length;

  return (
    <div className="px-8 py-8">
      <h1 className="text-4xl font-bold text-slate-900 mb-8">Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={<Wifi className="text-blue-600" size={24} />}
          label="Connected Devices"
          value={activeDevices}
        />
        <StatCard
          icon={<Activity className="text-green-600" size={24} />}
          label="Total Devices"
          value={devices.length}
        />
        <StatCard
          icon={<Zap className="text-purple-600" size={24} />}
          label="Agents"
          value={agentCount}
        />
        <StatCard
          icon={<AlertTriangle className="text-orange-600" size={24} />}
          label="Active Alerts"
          value={alerts.filter((a) => a.status === 'active').length}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Devices List */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold text-slate-900 mb-4">Devices</h2>
            {loading ? (
              <p className="text-slate-600">Loading...</p>
            ) : devices.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                        Device
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                        Hostname
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                        IP Address
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                        MAC Address
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {devices.map((device) => (
                      <tr key={device.id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-3 px-4">
                          <DeviceIcon type={device.device_type} active={device.is_active} />
                        </td>
                        <td className="py-3 px-4 text-slate-900">{device.hostname || 'N/A'}</td>
                        <td className="py-3 px-4 text-slate-600">{device.ip_address}</td>
                        <td className="py-3 px-4 text-slate-600 font-mono text-sm">
                          {device.mac_address}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-3 py-1 rounded-full text-sm font-medium ${
                              device.is_active
                                ? 'bg-green-100 text-green-800'
                                : 'bg-slate-100 text-slate-800'
                            }`}
                          >
                            {device.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-slate-600">No devices found</p>
            )}
          </div>
        </div>

        {/* Alerts */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Alerts</h2>
          {alerts.length > 0 ? (
            <div className="space-y-3">
              {alerts.slice(0, 5).map((alert) => (
                <div key={alert.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <h3 className="font-semibold text-slate-900 text-sm">{alert.title}</h3>
                  <p className="text-xs text-slate-600 mt-1">
                    Threshold: {alert.threshold} MB/s
                  </p>
                  <span className="text-xs font-medium text-orange-600 mt-2 block">
                    {alert.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-600">No alerts</p>
          )}
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
}

function StatCard({ icon, label, value }: StatCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-slate-600 text-sm font-medium">{label}</p>
          <p className="text-3xl font-bold text-slate-900 mt-2">{value}</p>
        </div>
        <div className="p-3 bg-slate-100 rounded-lg">{icon}</div>
      </div>
    </div>
  );
}
