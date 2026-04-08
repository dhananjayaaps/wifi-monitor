import { Slot, useRouter, useSegments, useRootNavigationState } from 'expo-router';
import { useEffect } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider, useAuth } from '@/context/AuthContext';

function AuthGuard() {
  const { token, isLoading } = useAuth();
  const segments = useSegments();
  const router = useRouter();
  // Expo Router v5: wait for navigation state to be ready before redirecting
  const navigationState = useRootNavigationState();

  useEffect(() => {
    if (!navigationState?.key || isLoading) return;
    const inAuthGroup = segments[0] === '(auth)';
    if (!token && !inAuthGroup) {
      router.replace('/(auth)/login');
    } else if (token && inAuthGroup) {
      router.replace('/(tabs)');
    }
  }, [token, isLoading, segments, navigationState?.key]);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0f172a' }}>
        <ActivityIndicator color="#2563eb" size="large" />
      </View>
    );
  }

  return <Slot />;
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <AuthGuard />
      </AuthProvider>
    </SafeAreaProvider>
  );
}
