'use client';

import { useState, useEffect } from 'react';
import { Navbar } from '@/components/Navbar';
import { alertsAPI } from '@/lib/api';
import { AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface Alert {
  id: number;
  title: string;
  description?: string;
  threshold: number;
  status: string;
  created_at: string;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAlerts = async () => {
      try {
        const response = await alertsAPI.list();
        setAlerts(response.data.data || []);
      } catch (error) {
        console.error('Failed to load alerts:', error);
      } finally {
        setLoading(false);
      }
    };

    loadAlerts();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <AlertTriangle className="text-red-600" size={20} />;
      case 'resolved':
        return <CheckCircle className="text-green-600" size={20} />;
      default:
        return <Clock className="text-blue-600" size={20} />;
    }
  };

  const getStatusBadge = (status: string) => {
    const badgeClass =
      status === 'active'
        ? 'bg-red-100 text-red-800'
        : status === 'resolved'
          ? 'bg-green-100 text-green-800'
          : 'bg-blue-100 text-blue-800';

    return <span className={`px-3 py-1 rounded-full text-sm font-medium ${badgeClass}`}>{status}</span>;
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-slate-900 mb-8">Alerts</h1>

        {loading ? (
          <p className="text-slate-600">Loading...</p>
        ) : (
          <div className="space-y-4">
            {alerts.length > 0 ? (
              alerts.map((alert) => (
                <div key={alert.id} className="bg-white rounded-lg shadow p-6 border-l-4 border-slate-300">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="mt-1">{getStatusIcon(alert.status)}</div>
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-slate-900">{alert.title}</h3>
                        {alert.description && (
                          <p className="text-slate-600 mt-1">{alert.description}</p>
                        )}
                        <div className="flex items-center gap-4 mt-3 text-sm text-slate-600">
                          <span>Threshold: {alert.threshold} MB/s</span>
                          <span>{new Date(alert.created_at).toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                    <div>{getStatusBadge(alert.status)}</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <p className="text-slate-600 text-lg">No alerts yet</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
