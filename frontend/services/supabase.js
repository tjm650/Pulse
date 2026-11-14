import { createClient } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

// Non-public EXPO_* values are passed into the client through app.config.js.
const supabaseUrl = Constants.expoConfig?.extra?.EXPO_SUPABASE_URL;
const supabasePublishableKey =
  Constants.expoConfig?.extra?.EXPO_SUPABASE_PUBLISHABLE_KEY;

// Supabase is optional in credential-free local development environments.
// Features that require Supabase check for configuration when they are invoked.
export const isSupabaseConfigured = Boolean(supabaseUrl && supabasePublishableKey);

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabasePublishableKey, {
      auth: {
        storage: AsyncStorage,
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: false,
      },
    })
  : null;
