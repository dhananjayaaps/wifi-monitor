'use client';

import { useState, useEffect } from 'react';
import { alertsAPI } from '@/lib/api';
import { AlertTriangle } from 'lucide-react';

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

export default function AlertsPage() {
  const [history, setHistory] = useState<AlertHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const refreshMs = 30000;

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const histResp = await alertsAPI.history(24);
        setHistory(histResp.data.data || []);
      } catch (error) {
        console.error('Failed to load alert history:', error);
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
    const intervalId = window.setInterval(loadHistory, refreshMs);
    return () => window.clearInterval(intervalId);
  }, []);

  const deviceName = (item: AlertHistoryItem) => {
    if (item.device_hostname) return item.device_hostname;
    if (item.device_mac) return item.device_mac;
    if (item.device_id) return `Device ${item.device_id}`;
    return 'Unknown device';
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
                    <h3 className="text-lg font-semibold text-slate-900">
                      {item.alert_type === 'data_cap' ? 'Data cap exceeded' : 'Data usage alert'}
                    </h3>
                    <p className="text-slate-600 mt-1">
                      Device: {deviceName(item)}
                    </p>
                    {item.threshold_value != null && (
                      <p className="text-xs text-slate-500 mt-1">
                        Threshold: {formatBytes(item.threshold_value)}
                      </p>
                    )}
                    <div className="flex items-center gap-4 mt-3 text-sm text-slate-600">
                      <span>
                        Value at trigger: {formatBytes(item.value_at_trigger)}
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
