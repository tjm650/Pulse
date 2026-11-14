import { createClient } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

// Non-public EXPO_* values are passed into the client through app.config.js.
const supabaseUrl = Constants.expoConfig?.extra?.EXPO_SUPABASE_URL;
const supabasePublishableKey =
  Constants.expoConfig?.extra?.EXPO_SUPABASE_PUBLISHABLE_KEY;

if (!supabaseUrl || !supabasePublishableKey) {
  const missing = [
    !supabaseUrl && 'EXPO_SUPABASE_URL',
    !supabasePublishableKey && 'EXPO_SUPABASE_PUBLISHABLE_KEY',
  ].filter(Boolean);

  throw new Error(
    `Missing Expo Supabase environment variables: ${missing.join(', ')}. Set them in the Expo environment or frontend/.env, then restart Expo.`
  );
}

export const supabase = createClient(supabaseUrl, supabasePublishableKey, {
  auth: {
    storage: AsyncStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
});
