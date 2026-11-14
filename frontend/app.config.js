export default ({ config }) => ({
  ...config,
  extra: {
    ...config.extra,
    EXPO_API_URL:
      process.env.EXPO_PUBLIC_API_URL || process.env.EXPO_API_URL,
    EXPO_SUPABASE_URL:
      process.env.EXPO_PUBLIC_SUPABASE_URL || process.env.EXPO_SUPABASE_URL,
    EXPO_SUPABASE_PUBLISHABLE_KEY:
      process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
      process.env.EXPO_SUPABASE_PUBLISHABLE_KEY,
  },
});
