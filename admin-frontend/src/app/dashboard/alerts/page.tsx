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
  const [loadingMore, setLoadingMore] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [hours, setHours] = useState<number | undefined>(24);
  const pageSize = 25;
  const refreshMs = 30000;

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const histResp = await alertsAPI.history({ hours, limit: pageSize, offset: 0 });
        const items = histResp.data.data || [];
        setHistory(items);
        setHasMore(items.length === pageSize);
      } catch (error) {
        console.error('Failed to load alert history:', error);
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
    const intervalId = window.setInterval(loadHistory, refreshMs);
    return () => window.clearInterval(intervalId);
  }, [hours]);

  const clearHistory = async () => {
    if (clearing) return;
    const confirmed = window.confirm('Clear all alert history? This cannot be undone.');
    if (!confirmed) return;
    setClearing(true);
    try {
      await alertsAPI.clearHistory();
      setHistory([]);
      setHasMore(false);
    } catch (error) {
      console.error('Failed to clear alert history:', error);
    } finally {
      setClearing(false);
    }
  };

  const loadMore = async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const histResp = await alertsAPI.history({
        hours,
        limit: pageSize,
        offset: history.length,
      });
      const items = histResp.data.data || [];
      setHistory((prev) => [...prev, ...items]);
      setHasMore(items.length === pageSize);
    } catch (error) {
      console.error('Failed to load older alerts:', error);
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
    if (type === 'ddos_detected') return 'DDoS detected';
    if (type === 'dos_detected') return 'DoS detected';
    if (type === 'data_cap') return 'Data cap exceeded';
    return 'Data usage alert';
  };

  const showThreshold = (item: AlertHistoryItem) => {
    const type = (item.alert_type || '').toLowerCase();
    return type !== 'ddos_detected' && type !== 'dos_detected';
  };

  const valueLabel = (item: AlertHistoryItem) => {
    const type = (item.alert_type || '').toLowerCase();
    if (type === 'ddos_detected' || type === 'dos_detected') {
      return 'Traffic at trigger';
    }
    return 'Value at trigger';
  };

  return (
    <div className="px-8 py-8">
      <h1 className="text-4xl font-bold text-slate-900 mb-8">Alerts</h1>

      {loading ? (
        <p className="text-slate-600">Loading...</p>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3 justify-between">
            <div className="flex items-center gap-3">
            <label className="text-sm text-slate-600" htmlFor="history-hours">
              Time range
            </label>
            <select
              id="history-hours"
              className="rounded-md border border-slate-300 px-3 py-1 text-sm"
              value={hours ?? 'all'}
              onChange={(event) => {
                const value = event.target.value;
                setLoading(true);
                setHistory([]);
                setHasMore(true);
                if (value === 'all') {
                  setHours(undefined);
                } else {
                  setHours(Number(value));
                }
              }}
            >
              <option value="24">Last 24 hours</option>
              <option value="72">Last 3 days</option>
              <option value="168">Last 7 days</option>
              <option value="720">Last 30 days</option>
              <option value="all">All time</option>
            </select>
            </div>
            <button
              type="button"
              className="rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              onClick={clearHistory}
              disabled={clearing}
            >
              {clearing ? 'Clearing...' : 'Clear alerts'}
            </button>
          </div>
          {history.length > 0 ? (
            history.map((item) => (
              <div key={item.id} className="bg-white rounded-lg shadow p-6 border-l-4 border-red-400">
                <div className="flex items-start gap-4">
                  <AlertTriangle className="text-red-600 mt-1" size={20} />
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-slate-900">
                      {alertTitle(item)}
                    </h3>
                    <p className="text-slate-600 mt-1">
                      Device: {deviceName(item)}
                    </p>
                    {showThreshold(item) && item.threshold_value != null && (
                      <p className="text-xs text-slate-500 mt-1">
                        Threshold: {formatBytes(item.threshold_value)}
                      </p>
                    )}
                    <div className="flex flex-wrap items-center gap-4 mt-3 text-sm text-slate-600">
                      <span>
                        {valueLabel(item)}: {formatBytes(item.value_at_trigger)}
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
          {history.length > 0 && (
            <div className="flex justify-center pt-4">
              <button
                type="button"
                className="rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={loadMore}
                disabled={!hasMore || loadingMore}
              >
                {loadingMore ? 'Loading...' : hasMore ? 'Load older alerts' : 'No more alerts'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
