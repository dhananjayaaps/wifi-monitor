'use client';

import { Navbar } from '@/components/Navbar';
import { DashboardNav } from '@/components/DashboardNav';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div>
      <Navbar />
      <div className="flex">
        <DashboardNav />
        <div className="flex-1 bg-slate-50">{children}</div>
      </div>
    </div>
  );
}
