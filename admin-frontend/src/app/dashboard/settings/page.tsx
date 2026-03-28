'use client';

import { useEffect, useState } from 'react';
import { settingsAPI } from '@/lib/api';

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

export default function SettingsPage() {
  const [defaultCap, setDefaultCap] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await settingsAPI.get();
        const value = response.data.data?.default_device_cap;
        setDefaultCap(bytesToMBString(value));
      } catch (error) {
        console.error('Failed to load settings:', error);
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, []);

  const saveSettings = async () => {
    if (saving) return;

    const value = mbStringToBytes(defaultCap);
    if (value === undefined) {
      alert('Please enter a valid non-negative number of MB, or leave empty to clear.');
      return;
    }

    setSaving(true);
    try {
      const response = await settingsAPI.update(value);
      const updated = response.data.data?.default_device_cap;
      setDefaultCap(bytesToMBString(updated));
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="px-8 py-8">
      <h1 className="text-4xl font-bold text-slate-900 mb-8">Settings</h1>

      <div className="bg-white rounded-lg shadow p-6 max-w-2xl">
        <h2 className="text-xl font-bold text-slate-900 mb-4">Default Device Cap</h2>

        {loading ? (
          <p className="text-slate-600">Loading...</p>
        ) : (
          <>
            <p className="text-sm text-slate-600">
              New devices will automatically receive this data cap.
            </p>
            <div className="flex items-center gap-3 mt-3">
              <input
                type="text"
                value={defaultCap}
                onChange={(e) => setDefaultCap(e.target.value)}
                className="border rounded px-3 py-2 w-full max-w-md"
                placeholder="e.g. 1024 for 1 GB, empty to clear"
              />
              <button
                onClick={saveSettings}
                disabled={saving}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-60"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Current: {defaultCap ? `${defaultCap} MB` : 'No default cap set'}
            </p>
            <p className="text-xs text-amber-700 mt-3">
              Note: this value is stored in the running backend config and resets on server restart.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
