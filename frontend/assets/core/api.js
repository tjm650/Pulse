import axios from "axios";
import Constants from "expo-constants";
import secure from "./secure";
import { supabase } from "@/services/supabase";

const DEFAULT_API_URL = "https://pulse-w59d.onrender.com";
const configuredApiUrl =
  Constants.expoConfig?.extra?.EXPO_API_URL || process.env.EXPO_API_URL;

export const API_BASE_URL = (configuredApiUrl || DEFAULT_API_URL).replace(/\/+$/, "");

// Temporary network diagnostics: logs the destination only, never credentials or request bodies.
console.info("[Pulse API] Resolved base URL:", API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    console.info("[Pulse API] Request:", config.method?.toUpperCase(), `${config.baseURL || API_BASE_URL}${config.url || ""}`);
    try {
      const tokens = await secure.get("tokens");
      if (tokens?.access) {
        config.headers.Authorization = `Bearer ${tokens.access}`;
      }
    } catch (error) {
      console.error("Error getting tokens:", error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    console.error("[Pulse API] Request failed:", {
      message: error.message,
      code: error.code,
      url: error.config ? `${error.config.baseURL || API_BASE_URL}${error.config.url || ""}` : "unknown",
      hasHttpResponse: Boolean(error.response),
      responseStatus: error.response?.status,
    });
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const tokens = await secure.get("tokens");
        if (tokens?.refresh) {
          const response = await axios.post(`${API_BASE_URL}/api/token/refresh/`, {
            refresh: tokens.refresh,
          });

          const newTokens = {
            access: response.data.access,
            refresh: response.data.refresh || tokens.refresh,
          };

          await secure.set("tokens", newTokens);
          if (supabase) {
            await supabase.auth.setSession({ access_token: newTokens.access, refresh_token: newTokens.refresh });
          }

          originalRequest.headers.Authorization = `Bearer ${newTokens.access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        console.error("Token refresh failed:", refreshError);
        // Clear invalid tokens
        if (supabase) {
          await supabase.auth.signOut({ scope: "local" });
        }
        await secure.remove("tokens");
      }
    }

    return Promise.reject(error);
  }
);

export default api;
