'use client';

import { ReactNode, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { authAPI } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const setUser = useAuthStore((state) => state.setUser);

  useEffect(() => {
    const checkAuth = async () => {
      const token = Cookies.get('access_token');

      if (!token) {
        if (pathname !== '/login' && pathname !== '/register') {
          router.push('/login');
        }
        return;
      }

      try {
        const response = await authAPI.me();
        setUser(response.data.data);
        if (pathname === '/login' || pathname === '/register') {
          router.push('/dashboard');
        }
      } catch (error) {
        Cookies.remove('access_token');
        router.push('/login');
      }
    };

    checkAuth();
  }, [pathname, router, setUser]);

  return <>{children}</>;
}
