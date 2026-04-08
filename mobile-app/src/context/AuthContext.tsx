import React, { createContext, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { setUnauthorizedHandler } from '@/lib/api';

interface AuthContextType {
  token: string | null;
  isLoading: boolean;
  signIn: (token: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  token: null,
  isLoading: true,
  signIn: async () => {},
  signOut: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    AsyncStorage.getItem('access_token').then((value) => {
      setToken(value);
      setIsLoading(false);
    });
  }, []);

  const signIn = async (newToken: string) => {
    await AsyncStorage.setItem('access_token', newToken);
    setToken(newToken);
  };

  const signOut = async () => {
    await AsyncStorage.removeItem('access_token');
    setToken(null);
  };

  // Register handler so api.ts 401 interceptor can trigger sign-out
  useEffect(() => {
    setUnauthorizedHandler(signOut);
    return () => setUnauthorizedHandler(() => {});
  }, []);

  return (
    <AuthContext.Provider value={{ token, isLoading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
