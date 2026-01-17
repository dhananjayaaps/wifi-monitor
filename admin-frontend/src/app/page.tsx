'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function Home() {
  const router = useRouter();

  // Redirect to dashboard on mount
  router.push('/dashboard');

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">WiFi Monitor</h1>
        <p className="text-slate-600 mb-6">Redirecting to dashboard...</p>
        <Link href="/dashboard" className="text-blue-600 hover:underline">
          Click here if not redirected
        </Link>
      </div>
    </div>
  );
}
