import axios from "axios";
import secure from "./secure";
import { supabase } from "@/services/supabase";

export const ADDRESS = process.env.EXPO_PUBLIC_API_HOST || "localhost:8000";
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || `http://${ADDRESS}`;

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
          await supabase.auth.setSession({ access_token: newTokens.access, refresh_token: newTokens.refresh });

          originalRequest.headers.Authorization = `Bearer ${newTokens.access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        console.error("Token refresh failed:", refreshError);
        // Clear invalid tokens
        await supabase.auth.signOut({ scope: "local" });
        await secure.remove("tokens");
      }
    }

    return Promise.reject(error);
  }
);

export default api;