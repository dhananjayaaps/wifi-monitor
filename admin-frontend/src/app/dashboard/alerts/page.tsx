'use client';

import { useState, useEffect } from 'react';
import { alertsAPI, devicesAPI } from '@/lib/api';
import { AlertTriangle } from 'lucide-react';

interface AlertHistoryItem {
  id: number;
  alert_id: number;
  device_id: number | null;
  value_at_trigger: number;
  triggered_at: string;
  resolved_at?: string | null;
}

interface DeviceSummary {
  id: number;
  hostname?: string;
  mac_address: string;
}

export default function AlertsPage() {
  const [history, setHistory] = useState<AlertHistoryItem[]>([]);
  const [devices, setDevices] = useState<DeviceSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const [histResp, devResp] = await Promise.all([
          alertsAPI.history(24),
          devicesAPI.list(),
        ]);
        setHistory(histResp.data.data || []);
        setDevices(devResp.data.data || []);
      } catch (error) {
        console.error('Failed to load alert history:', error);
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
  }, []);

  const deviceName = (device_id: number | null) => {
    if (!device_id) return 'Unknown device';
    const device = devices.find((d) => d.id === device_id);
    if (!device) return `Device ${device_id}`;
    return device.hostname || device.mac_address;
  };

  return (
    <div className="px-8 py-8">
      <h1 className="text-4xl font-bold text-slate-900 mb-8">Alerts</h1>

        {loading ? (
          <p className="text-slate-600">Loading...</p>
        ) : (
          <div className="space-y-4">
            {history.length > 0 ? (
              history.map((item) => (
                <div key={item.id} className="bg-white rounded-lg shadow p-6 border-l-4 border-red-400">
                  <div className="flex items-start gap-4">
                    <AlertTriangle className="text-red-600 mt-1" size={20} />
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-slate-900">Data usage alert</h3>
                      <p className="text-slate-600 mt-1">
                        Device: {deviceName(item.device_id)}
                      </p>
                      <div className="flex items-center gap-4 mt-3 text-sm text-slate-600">
                        <span>
                          Value at trigger: {(item.value_at_trigger / 1024 / 1024).toFixed(2)} MB
                        </span>
                        <span>{new Date(item.triggered_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <p className="text-slate-600 text-lg">No alerts in the last 24 hours</p>
              </div>
            )}
          </div>
        )}
    </div>
  );
}
