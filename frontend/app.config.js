export default ({ config }) => ({
  ...config,
  extra: {
    ...config.extra,
    // Use the deployed HTTPS API unless an explicit environment override is provided.
    EXPO_API_URL: process.env.EXPO_API_URL || "https://pulse-w59d.onrender.com",
    EXPO_SUPABASE_URL: process.env.EXPO_SUPABASE_URL,
    EXPO_SUPABASE_PUBLISHABLE_KEY: process.env.EXPO_SUPABASE_PUBLISHABLE_KEY,
  },
});
