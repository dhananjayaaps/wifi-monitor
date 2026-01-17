'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Wifi, AlertTriangle, Server } from 'lucide-react';

export function DashboardNav() {
  const pathname = usePathname();

  const navItems = [
    { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
    { href: '/dashboard/devices', label: 'Devices', icon: Wifi },
    { href: '/dashboard/alerts', label: 'Alerts', icon: AlertTriangle },
    { href: '/dashboard/agents', label: 'Agents', icon: Server },
  ];

  return (
    <aside className="bg-white border-r border-slate-200 w-64 min-h-screen">
      <nav className="p-4 space-y-2">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                isActive
                  ? 'bg-blue-100 text-blue-600 font-medium'
                  : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              <Icon size={20} />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
