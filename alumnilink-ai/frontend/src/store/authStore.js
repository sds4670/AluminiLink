import { create } from "zustand";
import { persist } from "zustand/middleware";
import api from "../api/axios";

const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      role: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const res = await api.post("/api/v1/auth/login", { email, password });
        const { access_token, refresh_token, user } = res.data;
        localStorage.setItem("access_token", access_token);
        localStorage.setItem("refresh_token", refresh_token);
        set({
          token: access_token,
          role: user.role,
          isAuthenticated: true,
          user,
        });
        return user;
      },

      register: async (email, password, role, identifier, fullName) => {
        const payload = { email, password, role, full_name: fullName };
        if (role === "student") payload.roll_number = identifier;
        if (role === "alumni") payload.register_number = identifier;
        const res = await api.post("/api/v1/auth/register", payload);
        return res.data;
      },

      fetchMe: async () => {
        try {
          const res = await api.get("/api/v1/auth/me");
          set({ user: res.data, role: res.data.role, isAuthenticated: true });
          return res.data;
        } catch {
          get().logout();
        }
      },

      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, token: null, role: null, isAuthenticated: false });
      },
    }),
    {
      name: "alumnilink-auth",
      partialize: (state) => ({
        token: state.token,
        role: state.role,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export default useAuthStore;
