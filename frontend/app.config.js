export default ({ config }) => ({
  ...config,
  extra: {
    ...config.extra,
    EXPO_API_URL:
      process.env.EXPO_PUBLIC_API_URL || process.env.EXPO_API_URL,
  },
});
